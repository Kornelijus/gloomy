from typing import Any
from tests.utils import Obj
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
    result = gloom(target, spec)
    assert result == expected
