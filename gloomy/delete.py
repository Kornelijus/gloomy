from gloomy.errors import PathAccessError, PathDeleteError
from gloomy.types import TargetObject, Path
from gloomy.utils import _is_digit_ascii


def delete(
    obj: TargetObject,
    path: Path,
    ignore_missing: bool = False,
) -> TargetObject:
    """
    Delete a nested attribute, key or index from an object, mapping or sequence.
    """
    match path:
        case str():
            path_parts = tuple(path.split("."))
        case tuple():
            path_parts = path
        case _:
            msg = f"Invalid path type: {type(path)}"
            raise ValueError(msg)

    location = obj
    path_len = len(path_parts)

    for i, part in enumerate(path_parts):
        is_destination = i == path_len - 1

        if not is_destination:
            # Mirror assign.py traversal: try getitem, fall back to getattr.
            # This is intentionally more permissive than gloom.py so that
            # types with __getitem__ (e.g. Pydantic models) can still be
            # navigated via attribute access when the key lookup fails.
            if getitem := getattr(location, "__getitem__", None):
                if _is_digit_ascii(part):
                    try:
                        location = getitem(int(part))
                        continue
                    except (IndexError, KeyError):
                        pass
                else:
                    try:
                        location = getitem(part)
                        continue
                    except KeyError:
                        pass

            try:
                location = getattr(location, part)
                continue
            except AttributeError:
                pass

            # All traversal attempts failed
            if ignore_missing:
                return obj
            raise PathAccessError

        # ------------------------------------------------------------------
        # Destination: delete the key/attribute
        # ------------------------------------------------------------------

        if delitem_fn := getattr(location, "__delitem__", None):
            if _is_digit_ascii(part):
                try:
                    delitem_fn(int(part))
                    break
                except IndexError:
                    if ignore_missing:
                        break
                    raise PathAccessError
                except (KeyError, TypeError):
                    pass  # fall through to string key or delattr
            try:
                delitem_fn(part)
                break
            except KeyError:
                if ignore_missing:
                    break
                raise PathAccessError
            except TypeError:
                pass  # fall through to delattr

        try:
            delattr(location, part)
            break
        except AttributeError:
            if ignore_missing:
                break
            raise PathAccessError
        except TypeError as e:
            raise PathDeleteError(f"Cannot delete from type {type(location)!r}") from e

    return obj
