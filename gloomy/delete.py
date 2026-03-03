from typing import Any

from gloomy.errors import PathAccessError, PathDeleteError
from gloomy.types import TargetObject, Path


def delete(
    obj: TargetObject,
    path: Path,
    ignore_missing: bool = False,
    *,
    _int=int,
    _getattr=getattr,
) -> TargetObject:
    """
    Delete a nested attribute, key or index from an object, mapping or sequence.
    """
    if isinstance(path, str):
        path_parts: list[str] | tuple[str, ...] = path.split(".")
    elif isinstance(path, tuple):
        path_parts = path
    else:
        msg = f"Invalid path type: {type(path)}"
        raise ValueError(msg)

    n = len(path_parts)
    last_part = path_parts[-1]
    # Typed as Any: location is a duck-typed cursor whose concrete type changes
    # at each traversal step. Direct subscript/delitem calls below are guarded
    # by except TypeError for non-subscriptable types.
    location: Any = obj

    # ------------------------------------------------------------------
    # Traversal: walk all parts except the last.
    # range(n-1) is O(1) to create and avoids allocating a slice copy.
    # ------------------------------------------------------------------
    for i in range(n - 1):
        part = path_parts[i]
        if part.isdecimal():
            try:
                location = location[_int(part)]
                continue
            except (IndexError, KeyError):
                pass
            except TypeError:
                pass  # not subscriptable, fall through to string then attr

        try:
            location = location[part]
            continue
        except (TypeError, KeyError):
            pass  # not subscriptable or key miss, fall through to attr

        try:
            location = _getattr(location, part)
            continue
        except AttributeError:
            pass

        if ignore_missing:
            return obj
        raise PathAccessError

    # ------------------------------------------------------------------
    # Destination: delete last_part from location
    # ------------------------------------------------------------------
    if last_part.isdecimal():
        try:
            del location[_int(last_part)]
            return obj
        except IndexError:
            if ignore_missing:
                return obj
            raise PathDeleteError
        except (KeyError, TypeError):
            pass  # fall through to string key or delattr

    try:
        del location[last_part]
        return obj
    except KeyError:
        if ignore_missing:
            return obj
        raise PathDeleteError
    except TypeError:
        pass  # not subscriptable, fall through to delattr

    try:
        delattr(location, last_part)
        return obj
    except AttributeError:
        if ignore_missing:
            return obj
        raise PathDeleteError
    except TypeError as e:
        raise PathDeleteError(f"Cannot delete from type {type(location)!r}") from e
