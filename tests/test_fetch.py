from typing import Any, ContextManager

from gloomy.errors import PathAccessError
from tests.utils import Obj
from contextlib import nullcontext as does_not_raise
import pytest
from gloomy import gloom


@pytest.mark.parametrize(
    ("target", "spec", "expected"),
    [
        ([1], "0", 1),
        ({0: 1}, "0", 1),
        ({"0": 1}, "0", 1),
        ({"a": 123}, "a", 123),
        (Obj(a=123), "a", 123),
        ({"a": {"b": {"c": 123}}}, "a.b.c", 123),
        ({"a": Obj(b=Obj(c=123))}, "a.b.c", 123),
        ([{"li": [{"foo": "bar"}]}], "0.li.0.foo", "bar"),
    ],
)
def test_valid_paths(target: Any, spec: str, expected: Any):
    result = gloom(target, spec, default=None)
    assert result == expected


@pytest.mark.parametrize(
    ("target", "spec", "expectation"),
    [
        ({}, "a.b.c", pytest.raises(PathAccessError)),
        ({"abc": None}, "abc", does_not_raise()),
        ({"0": None}, "0", does_not_raise()),
    ],
)
def test_raises_path_access_error(target: Any, spec: str, expectation: ContextManager):
    with expectation:
        gloom(target, spec)
