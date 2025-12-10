from typing import Any

from gloomy.errors import PathAccessError
from gloomy.types import TargetObject, _NO_DEFAULT, Path
from gloomy.utils import _is_digit_ascii, _path_parts


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

    path_parts = _path_parts(spec)
    location = target

    for part in path_parts:
        # Get key/index of mapping/sequence
        if getitem := getattr(location, "__getitem__", None):
            if _is_digit_ascii(part):
                try:
                    # Sequence or mapping with int keys
                    location = getitem(int(part))
                    continue
                except IndexError as e:
                    if default is _NO_DEFAULT:
                        raise PathAccessError from e
                    return default
                except KeyError:
                    # Possibly mapping with numeric string keys
                    pass
            try:
                location = getitem(part)
                continue
            except KeyError as e:
                if default is _NO_DEFAULT:
                    raise PathAccessError from e
                return default
        try:
            location = getattr(location, part)
        except AttributeError as e:
            if default is _NO_DEFAULT:
                raise PathAccessError from e
            return default

    return location
