from typing import Any, Mapping, Sequence

_no_default = object()
_sentinel = object()


class PathAccessError(Exception):
    """Raised when specified path (spec) cannot be accessed and no default is provided."""


def gloom(
    target: Sequence | Mapping | object | None,
    spec: str,
    default: Any = _no_default,
) -> Any:
    """
    Access a nested attribute, key or index of an object.

    Raises:
        PathAccessError: if no default is provided.
        ValueError: If object in path contains

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
        if getattr(location, "__getitem__", None):
            if isinstance(location, Mapping):
                try:
                    location = location[part]
                    continue
                except KeyError as e:
                    if default is _no_default:
                        raise PathAccessError from e
                    return default
            if isinstance(location, Sequence):
                try:
                    location = location[int(part)]
                    continue
                except IndexError as e:
                    if default is _no_default:
                        raise PathAccessError from e
                    return default
            else:
                msg = f"Unsupported type: {type(location)}"
                raise ValueError(msg)

        try:
            location = getattr(location, part)
        except AttributeError as e:
            if default is _no_default:
                raise PathAccessError from e
            return default

    return location
