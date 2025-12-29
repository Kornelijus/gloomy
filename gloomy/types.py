from typing import Final, Mapping, Sequence, TypeAlias


TargetObject: TypeAlias = Sequence | Mapping | object | None
Path: TypeAlias = str | tuple[str, ...]
_NO_DEFAULT: Final = object()
