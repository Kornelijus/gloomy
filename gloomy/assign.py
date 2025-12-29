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
        missing_val = missing() if missing is not _NO_DEFAULT else _NO_DEFAULT
        to_assign = val if is_destination else missing_val

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

        # Assign value (either destination or missing intermediate)
        if to_assign is _NO_DEFAULT:
            raise PathAccessError

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
            # setitem_fn(part, to_assign)
            # if is_destination:
            # break
            # location = to_assign
            # continue

        if not hasattr(location, "__dict__"):
            raise PathAssignError(f"Cannot assign to type {type(obj)!r}")

        if setattr_fn := getattr(location, "__setattr__", None):
            setattr_fn(part, to_assign)
            if is_destination:
                break
            location = to_assign
            continue

        raise PathAccessError

    return obj
