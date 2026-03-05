from typing import Any

from gloomy.errors import PathAccessError
from gloomy.types import TargetObject, _NO_DEFAULT, Path
from gloomy.utils import _is_digit_ascii


def gloom(
    target: TargetObject,
    spec: Path,
    default: Any = _NO_DEFAULT,
) -> Any:
    """
    Access a nested attribute, key or index of an object, mapping or sequence.

    Raises:
        PathAccessError: if the path cannot be accessed and no default is provided.

    """
    if target is None:
        if default is _NO_DEFAULT:
            msg = "Cannot access path as target is None."
            raise PathAccessError(msg)
        return default

    if isinstance(spec, str):
        path_parts: list[str] | tuple = spec.split(".")
    elif isinstance(spec, tuple):
        path_parts = spec
    else:
        msg = f"Invalid path type: {type(spec)}"
        raise ValueError(msg)

    location = target

    for part in path_parts:
        # Fast-path for the most common container: plain dict with string keys.
        # Avoids bound-method creation and the _is_digit_ascii check entirely.
        if type(location) is dict:
            try:
                location = location[part]
                continue
            except KeyError as ke:
                # Also coerce digit strings to int (handles {0: v} with path "0")
                if isinstance(part, str):
                    try:
                        location = location[int(part)]
                        continue
                    except (ValueError, KeyError):
                        pass
                if default is _NO_DEFAULT:
                    raise PathAccessError from ke
                return default

        # General path: check the TYPE for __getitem__ — avoids allocating a
        # bound method object and is faster than getattr(instance, ..., None).
        elif hasattr(type(location), "__getitem__"):
            if isinstance(part, int) or _is_digit_ascii(part):
                try:
                    location = location[int(part)]
                    continue
                except IndexError as e:
                    if default is _NO_DEFAULT:
                        raise PathAccessError from e
                    return default
                except KeyError:
                    pass
            try:
                location = location[part]
                continue
            except KeyError as e:
                if default is _NO_DEFAULT:
                    raise PathAccessError from e
                return default

        # Attribute access (plain objects, dataclasses, Pydantic models, …)
        else:
            try:
                location = getattr(location, part)
            except AttributeError as e:
                if default is _NO_DEFAULT:
                    raise PathAccessError from e
                return default

    return location
