from typing import Any, Callable
from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore[import-untyped]
from gloomy import gloom
from glom import glom  # type: ignore[import-untyped]
from functools import partial
import pytest

from tests.utils import Obj


@pytest.mark.parametrize(
    ("impl"),
    [
        pytest.param(partial(glom, default=None), id="glom"),
        pytest.param(partial(gloom, default=None), id="gloom"),
        pytest.param(None, id="manual-impl"),
    ],
)
class TestBenchmark:
    def test_dict_key_missing(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str):
            return target.get("missing")

        kwargs = dict(target={}, spec="missing")
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result is None

    def test_dict_key_exists(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str):
            try:
                return target["a"]["b"]["c"]["d"]["e"]["f"]["g"]["h"]["i"]
            except (TypeError, KeyError):
                return None

        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": 123}}}}}}}}}

        kwargs = dict(target=data, spec="a.b.c.d.e.f.g.h.i")
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result == 123

    def test_obj_attr_missing(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str):
            return getattr(target, "missing", None)

        kwargs = dict(target=Obj(), spec="missing")
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result is None

    def test_obj_attr_exists_int(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str):
            try:
                return target.a.b.c
            except AttributeError:
                return None

        kwargs = dict(target=Obj(a=Obj(b=Obj(c=123))), spec="a.b.c")
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result == 123

    def test_obj_attr_list_element_missing(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str):
            try:
                return target.a[0].b
            except (AttributeError, IndexError):
                return None

        kwargs = dict(target=Obj(a=[]), spec="a.0.b")
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result is None

    def test_obj_attr_list_element_exists_int(
        self,
        benchmark: BenchmarkFixture,
        impl: Callable | None,
    ):
        def _manual_impl(target: Any, spec: str):
            try:
                return target.a[0].b
            except (AttributeError, IndexError):
                return None

        kwargs = dict(target=Obj(a=[Obj(b=123)]), spec="a.0.b")
        result = benchmark(impl or _manual_impl, **kwargs)
        assert result == 123
