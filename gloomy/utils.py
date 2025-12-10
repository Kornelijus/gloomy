from gloomy.types import Path


def _is_digit_ascii(s: str) -> bool:
    """Check if all characters in the string are ASCII digits.
    This is faster and more correct than using str.isdigit() in our case."""
    return all("0" <= c <= "9" for c in s)


def _path_parts(path: Path) -> tuple[str, ...]:
    match path:
        case tuple():
            return path
        case str():
            return tuple(path.split("."))
        case _:
            msg = f"Invalid path type: {type(path)}"
            raise ValueError(msg)
