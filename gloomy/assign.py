from typing import Any


from gloomy.errors import PathAccessError, PathAssignError
from gloomy.types import TargetObject, Path, _NO_DEFAULT
from gloomy.utils import _is_digit_ascii


def assign(
    obj: TargetObject,
    path: Path,
    val: Any,
    missing: Any = _NO_DEFAULT,
) -> Any:
    """
    Assign a value to a nested attribute, key or index of an object, mapping or sequence.
    """

    if missing is not _NO_DEFAULT:
        if not callable(missing):
            raise TypeError(f"expected missing to be callable, not {missing!r}")

    if isinstance(path, str):
        path_parts = tuple(path.split("."))
    elif isinstance(path, tuple):
        path_parts = path
    else:
        msg = f"Invalid path type: {type(path)}"
        raise ValueError(msg)

    location = obj
    last_idx = len(path_parts) - 1

    for i, part in enumerate(path_parts):
        is_destination = i == last_idx

        # Try to traverse if not at destination
        if not is_destination:
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

            # Traversal failed: only now compute the missing intermediate
            if missing is _NO_DEFAULT:
                raise PathAccessError
            to_assign = missing()
        else:
            to_assign = val

        # Assign value (either destination or missing intermediate)
        if setitem_fn := getattr(location, "__setitem__", None):
            if isinstance(part, int) or _is_digit_ascii(part):
                try:
                    setitem_fn(int(part), to_assign)
                    if is_destination:
                        break
                    location = to_assign
                    continue
                except (KeyError, IndexError, TypeError):
                    pass
            try:
                setitem_fn(part, to_assign)
                if is_destination:
                    break
                location = to_assign
                continue
            except (KeyError, TypeError):
                pass

        if not hasattr(location, "__dict__"):
            raise PathAssignError(f"Cannot assign to type {type(obj)!r}")

        setattr(location, part, to_assign)
        if is_destination:
            break
        location = to_assign

    return obj
