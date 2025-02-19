from typing import Any, Dict, List, Sequence, Set, Tuple, Optional, Collection
from typing import NewType

FileExtension = NewType("FileExtension", str)
Language = NewType("Language", str)

Shebang = str

Mode = NewType("Mode", str)
# TODO: type Mode?
JOIN_MODE = ...

class LanguageDefinition:
    """
    Mirrors schema of lang.json (see lang/README.md) for each language
    """

    id: Language
    name: str
    keys: Collection[str]
    exts: Collection[FileExtension]
    reverse_exts: Collection[str]
    shebangs: Collection[Shebang]

class _LanguageData:
    def __init__(self) -> None: ...

# TODO: type
LANGUAGE = ...

# TODO: type
ALLOWED_GLOB_TYPES = ...
