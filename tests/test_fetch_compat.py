from typing import Any, Callable
import pytest
from tests.utils import Obj
from gloomy import gloom
from glom import glom, Path as GlomPath  # type: ignore[import-untyped]


def _glom_impl(target, spec, **kwargs):
    if isinstance(spec, tuple):
        spec = GlomPath(*spec)
    return glom(target, spec, **kwargs)


@pytest.mark.parametrize(
    ("impl"),
    [
        pytest.param(gloom, id="gloomy"),
        pytest.param(_glom_impl, id="glom"),
    ],
)
class TestFetchGlomCompat:
    @pytest.mark.parametrize(
        ("target", "spec", "expected"),
        [
            pytest.param([123], "0", 123, id="list-index"),
            pytest.param([123], (0,), 123, id="list-index-tuple-path-int"),
            pytest.param([123], ("0",), 123, id="list-index-tuple-path-int"),
            pytest.param(
                {0: 1},
                "0",
                1,
                id="dict-int-index-path-str",
                marks=pytest.mark.xfail(reason="glom doesn't support string-to-int key coercion for str path"),
            ),
            pytest.param(
                {0: 1},
                (0,),
                1,
                id="dict-int-index-path-tuple",
            ),
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
    def test_fetch_matches(self, impl: Callable, target: Any, spec: str, expected: Any):
        result = impl(target, spec, default=None)
        assert result == expected
