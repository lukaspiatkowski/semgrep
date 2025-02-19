from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from enum import Enum
from pathlib import Path
import semgrep.rule_match as rule_match

OK_EXIT_CODE = ...
FINDINGS_EXIT_CODE = ...
FATAL_EXIT_CODE = 2
UNPARSEABLE_YAML_EXIT_CODE = ...
MISSING_CONFIG_EXIT_CODE = ...

class Level(Enum):
    ERROR = ...  # Always an error
    WARN = ...  # Only an error if "strict" is set

class SemgrepError(Exception):
    """
    Parent class of all exceptions we anticipate in Semgrep commands

    All Semgrep Exceptions are caught and their error messages
    are displayed to the user.

    For pretty-printing, exceptions should override `__str__`.
    """

    def __init__(
        self, *args: object, code: int = FATAL_EXIT_CODE, level: Level = Level.ERROR
    ) -> None: ...
    def semgrep_error_type(self) -> str: ...
    def to_dict(self) -> Dict[str, Any]: ...

class LegacySpan: ...

class SemgrepCoreError(SemgrepError):
    code: int
    path: Path
    start: rule_match.CoreLocation
    end: rule_match.CoreLocation
    message: str

class FilesNotFoundError(SemgrepError): ...

class ErrorWithSpan(SemgrepError):
    """
    In general, you should not be constructing ErrorWithSpan directly, and instead be constructing a subclass
    that sets the code.

    Error which will print context from the Span. You should provide the most specific span possible,
    eg. if the error is an invalid key, provide exactly the span for that key. You can then expand what's printed
    with span.with_context(...). Conversely, if you don't want to display the entire span, you can use `span.truncate`

    The __str__ method produces the pretty-printed error.
    Here is what the generated error will look like:

        <level>: <short_msg>
          --> <span.filename>:<span.start.line>
        1 | rules:
        2 |   - id: eqeq-is-bad
        3 |     pattern-inside: foo(...)
          |     ^^^^^^^^^^^^^^
        4 |     patterns:
        5 |       - pattern-not: 1 == 1
        = help: <help>
        <long_msg>

    :param short_msg: 1 or 2 word description of the problem (eg. missing key)
    :param level: How bad is the problem? error,warn, etc.
    :param spans: A list of spans to display for context.
    :help help: An optional hint about how to fix the problem
    :cause cause: The underlying exception
    """

    ...

class InvalidRuleSchemaError(ErrorWithSpan): ...
class UnknownLanguageError(ErrorWithSpan): ...

class SemgrepInternalError(Exception):
    """
    Parent class of internal semgrep exceptions that should be handled internally and converted into `SemgrepError`s

    Classes that inherit from SemgrepInternalError should begin with `_`
    """

    ...

# TODO: diff with the one above?
class _UnknownLanguageError(SemgrepInternalError): ...

# TODO: type?
ERROR_MAP = ...
