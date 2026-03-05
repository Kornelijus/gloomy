from gloomy.types import Path
from typing import Generator


def _is_digit_ascii(s: str) -> bool:
    """Check if all characters in the string are ASCII digits.
    isdecimal() first for fast short-circuit on non-digit strings;
    isascii() guards against non-ASCII decimal chars like Arabic-Indic digits."""
    return s.isdecimal() and s.isascii()


def _path_parts(path: Path) -> Generator[str, None, None]:
    match path:
        case tuple():
            yield from path
        case str():
            yield from path.split(".")
        case _:
            msg = f"Invalid path type: {type(path)}"
            raise ValueError(msg)
