from typing import Any, Callable
from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore[import-untyped]

from gloomy.gloom import gloom
from gloomyrs import gloom_rusty
from glom import glom  # type: ignore[import-untyped]
import pytest

from tests.utils import Obj


@pytest.mark.parametrize(
    ("impl"),
    [
        pytest.param(glom, id="glom"),
        pytest.param(gloom, id="gloom"),
        pytest.param(gloom_rusty, id="gloom-rusty"),
        pytest.param(None, id="manual-impl"),
    ],
)
class TestBenchmark:
    def test_dict_key_missing(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str, **kwargs):
            return target.get("missing")

        kwargs = dict(target={}, spec="missing", default=None)
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result is None

    def test_dict_key_exists(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str, **kwargs):
            try:
                return target["a"]["b"]["c"]["d"]["e"]["f"]["g"]["h"]["i"]
            except (TypeError, KeyError):
                return None

        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": 123}}}}}}}}}

        kwargs = dict(target=data, spec="a.b.c.d.e.f.g.h.i", default=None)
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result == 123

    def test_obj_attr_missing(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str, **kwargs):
            return getattr(target, "missing", None)

        kwargs = dict(target=Obj(), spec="missing", default=None)
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result is None

    def test_obj_attr_exists_int(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str, **kwargs):
            try:
                return target.a.b.c
            except AttributeError:
                return None

        kwargs = dict(target=Obj(a=Obj(b=Obj(c=123))), spec="a.b.c", default=None)
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result == 123

    def test_obj_attr_list_element_missing(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str, **kwargs):
            try:
                return target.a[0].b
            except (AttributeError, IndexError):
                return None

        kwargs = dict(target=Obj(a=[]), spec="a.0.b", default=None)
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result is None

    def test_obj_attr_list_element_exists_int(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str, **kwargs):
            try:
                return target.a[0].b
            except (AttributeError, IndexError):
                return None

        kwargs = dict(target=Obj(a=[Obj(b=123)]), spec="a.0.b", default=None)
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result == 123
