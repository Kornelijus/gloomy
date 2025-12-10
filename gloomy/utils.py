from gloomy.types import Path
from typing import Generator


def _is_digit_ascii(s: str) -> bool:
    """Check if all characters in the string are ASCII digits.
    This is faster and more correct than using str.isdigit() in our case."""
    return all("0" <= c <= "9" for c in s)


def _path_parts(path: Path) -> Generator[str, None, None]:
    match path:
        case tuple():
            yield from path
        case str():
            yield from path.split(".")
        case _:
            msg = f"Invalid path type: {type(path)}"
            raise ValueError(msg)
