from typing import Any, Mapping, Sequence

_no_default = object()


class PathAccessError(Exception):
    """Raised when specified path (spec) cannot be accessed and no default is provided."""


def gloom(
    target: Sequence | Mapping | object | None,
    spec: str,
    default: Any = _no_default,
) -> Any:
    """
    Access a nested attribute, key or index of an object, mapping or sequence.

    Raises:
        PathAccessError: if the path cannot be accessed and no default is provided.

    """
    if target is None:
        if default is _no_default:
            msg = "Cannot access path as target is None."
            raise PathAccessError(msg)
        return default

    path_parts = spec.split(".")
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
                    if default is _no_default:
                        raise PathAccessError from e
                    return default
                except KeyError:
                    # Possibly mapping with numeric string keys
                    pass
            try:
                location = getitem(part)
                continue
            except KeyError as e:
                if default is _no_default:
                    raise PathAccessError from e
                return default
        try:
            location = getattr(location, part)
        except AttributeError as e:
            if default is _no_default:
                raise PathAccessError from e
            return default

    return location


def _is_digit_ascii(s: str) -> bool:
    """Check if all characters in the string are ASCII digits.
    This is faster and more correct than using str.isdigit() in our case."""
    return all("0" <= c <= "9" for c in s)
