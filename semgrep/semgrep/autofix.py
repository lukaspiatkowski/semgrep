import re
from pathlib import Path
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple

from semgrep.error import SemgrepError
from semgrep.rule_match import RuleMatch
from semgrep.rule_match_map import RuleMatchMap
from semgrep.verbose_logging import getLogger

logger = getLogger(__name__)

SPLIT_CHAR = "\n"


class Fix:
    def __init__(self, fixed_contents: str, fixed_lines: List[str]):
        self.fixed_contents = fixed_contents
        self.fixed_lines = fixed_lines


class FileOffsets:
    """
    This object is used to track state when applying multiple fixes to the same
    or subsequent lines in a single file.

    The assumption and current state here is that fixes are applied top-to-
    bottom and in a single pass; semgrep will not come back and re-parse or
    re-fix a file or line. This approach may need to be revisited or extended
    to support more complex overlapping autofix cases in future.
    """

    def __init__(self, line_offset: int, col_offset: int, active_line: int):
        self.line_offset = line_offset
        self.col_offset = col_offset
        self.active_line = active_line


def _get_lines(path: Path) -> List[str]:
    contents = path.read_text()
    lines = contents.split(SPLIT_CHAR)
    return lines


def _get_match_context(
    rule_match: RuleMatch, offsets: FileOffsets
) -> Tuple[int, int, int, int]:
    start_obj = rule_match.start
    start_line = start_obj.line - 1  # start_line is 1 indexed
    start_col = start_obj.col - 1  # start_col is 1 indexed
    end_obj = rule_match.end
    end_line = end_obj.line - 1  # end_line is 1 indexed
    end_col = end_obj.col - 1  # end_line is 1 indexed

    # adjust based on offsets
    start_line = start_line + offsets.line_offset
    end_line = end_line + offsets.line_offset
    start_col = start_col + offsets.col_offset
    end_col = end_col + offsets.col_offset

    return start_line, start_col, end_line, end_col


def _basic_fix(
    rule_match: RuleMatch, file_offsets: FileOffsets, fix: str
) -> Tuple[Fix, FileOffsets]:
    p = rule_match.path
    lines = _get_lines(p)

    # get the start and end points
    start_line, start_col, end_line, end_col = _get_match_context(
        rule_match, file_offsets
    )

    # break into before, to modify, after
    before_lines = lines[:start_line]
    before_on_start_line = lines[start_line][:start_col]
    after_on_end_line = lines[end_line][end_col:]  # next char after end of match
    modified_lines = (before_on_start_line + fix + after_on_end_line).splitlines()
    after_lines = lines[end_line + 1 :]  # next line after end of match
    contents_after_fix = before_lines + modified_lines + after_lines

    # update offsets
    file_offsets.line_offset = len(contents_after_fix) - len(lines)
    if start_line == end_line:
        file_offsets.col_offset = len(fix) - (end_col - start_col)

    return Fix(SPLIT_CHAR.join(contents_after_fix), modified_lines), file_offsets


def _regex_replace(
    rule_match: RuleMatch,
    file_offsets: FileOffsets,
    from_str: str,
    to_str: str,
    count: int = 1,
) -> Tuple[Fix, FileOffsets]:
    """
    Use a regular expression to autofix.
    Replaces from_str to to_str, starting from the left,
    exactly `count` times.
    """
    path = rule_match.path
    lines = _get_lines(path)

    start_line, _, end_line, _ = _get_match_context(rule_match, file_offsets)

    before_lines = lines[:start_line]
    after_lines = lines[end_line + 1 :]

    match_context = lines[start_line : end_line + 1]

    fix = re.sub(from_str, to_str, "\n".join(match_context), count)
    modified_context = fix.splitlines()
    modified_contents = before_lines + modified_context + after_lines

    # update offsets
    file_offsets.line_offset = len(modified_context) - len(match_context)

    return Fix(SPLIT_CHAR.join(modified_contents), modified_context), file_offsets


def _write_contents(path: Path, contents: str) -> None:
    path.write_text(contents)


def apply_fixes(rule_matches_by_rule: RuleMatchMap, dryrun: bool = False) -> None:
    """
    Modify files in place for all files with findings from rules with an
    autofix configuration
    """
    modified_files: Set[Path] = set()
    modified_files_offsets: Dict[Path, FileOffsets] = {}
    for _, rule_matches in rule_matches_by_rule.items():
        for rule_match in rule_matches:
            fix = rule_match.fix
            fix_regex = rule_match.fix_regex
            filepath = rule_match.path
            # initialize or retrieve/update offsets for the file
            file_offsets = modified_files_offsets.get(
                filepath, FileOffsets(0, 0, rule_match.start.line)
            )
            if file_offsets.active_line != rule_match.start.line:
                file_offsets.active_line = rule_match.start.line
                file_offsets.col_offset = 0
            if fix:
                try:
                    fixobj, new_file_offset = _basic_fix(rule_match, file_offsets, fix)
                except Exception as e:
                    raise SemgrepError(f"unable to modify file {filepath}: {e}")
            elif fix_regex:
                regex = fix_regex.get("regex")
                replacement = fix_regex.get("replacement")
                count = fix_regex.get("count", 0)
                if not regex or not replacement:
                    raise SemgrepError(
                        "'regex' and 'replacement' values required when using 'fix-regex'"
                    )
                try:
                    count = int(count)
                except ValueError:
                    raise SemgrepError(
                        "optional 'count' value must be an integer when using 'fix-regex'"
                    )
                try:
                    fixobj, new_file_offset = _regex_replace(
                        rule_match, file_offsets, regex, replacement, count
                    )
                except Exception as e:
                    raise SemgrepError(
                        f"unable to use regex to modify file {filepath} with fix '{fix}': {e}"
                    )
            else:
                continue
            # endif
            if not dryrun:
                _write_contents(rule_match.path, fixobj.fixed_contents)
                modified_files.add(filepath)
                modified_files_offsets[filepath] = new_file_offset
            else:
                rule_match.extra[
                    "fixed_lines"
                ] = fixobj.fixed_lines  # Monkey patch in fixed lines

    num_modified = len(modified_files)
    if len(modified_files):
        logger.info(
            f"successfully modified {num_modified} file{'s' if num_modified > 1 else ''}."
        )
    else:
        logger.info(f"no files modified.")
