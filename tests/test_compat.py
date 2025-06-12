from typing import Any, Callable
import pytest
from tests.utils import Obj
from gloomy import gloom
from glom import glom  # type: ignore[import-untyped]


# @pytest.mark.xfail
@pytest.mark.parametrize(
    ("impl"),
    [
        pytest.param(gloom, id="gloomy"),
        pytest.param(glom, id="glom"),
    ],
)
@pytest.mark.parametrize(
    ("target", "spec", "expected"),
    [
        pytest.param([123], "0", 123, id="list-index"),
        pytest.param([123], (0,), None, id="list-index-tuple-path-int", marks=pytest.mark.xfail),
        pytest.param([123], ("0",), None, id="list-index-tuple-path-int", marks=pytest.mark.xfail),
        # ({0: 1}, "0", 1),
        # ({0: 1}, (0,), 1),
        ({"0123": 1}, "0123", 1),
        ({"a": 123}, "a", 123),
        (Obj(a=123), "a", 123),
        ({"a": {"b": {"c": 123}}}, "a.b.c", 123),
        ({"a": {"b": {"c": 123}}}, ("a", "b", "c"), 123),
        ({"a": Obj(b=Obj(c=123))}, "a.b.c", 123),
        ({"a": Obj(b=Obj(c=123))}, ("a", "b", "c"), 123),
        ([{"li": [{"foo": "bar"}]}], "0.li.0.foo", "bar"),
    ],
)
def test_compat_glom(impl: Callable, target: Any, spec: str, expected: Any):
    result = impl(target, spec, default=None)
    assert result == expected
