from typing import Any, Callable
from glom import glom  # type: ignore[import-untyped]
from gloomy import gloom
import pytest
from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore[import-untyped]

from tests.utils import Obj


def _manual_impl_obj_attr_try_except(target: Any, spec: str, **kwargs):
    try:
        return target.a.b.c
    except AttributeError:
        return None


def _manual_impl_obj_hasattr_chain(target: Any, spec: str, **kwargs):
    if hasattr(target, "a") and hasattr(target.a, "b") and hasattr(target.a.b, "c"):
        return target.a.b.c
    return None


@pytest.mark.parametrize(
    ("impl"),
    [
        pytest.param(_manual_impl_obj_attr_try_except, id="manual-impl-try-except"),
        pytest.param(_manual_impl_obj_hasattr_chain, id="manual-impl-hasattr-chain"),
        pytest.param(gloom, id="gloomy"),
        pytest.param(glom, id="glom"),
    ],
)
def test_obj_attr_exists(
    benchmark: BenchmarkFixture,
    impl: Callable,
):
    kwargs = dict(target=Obj(a=Obj(b=Obj(c=123))), spec="a.b.c", default=None)
    if impl is gloom:
        kwargs["spec"] = ("a", "b", "c")

    result = benchmark(impl, **kwargs)
    assert result == 123


@pytest.mark.parametrize(
    ("impl"),
    [
        pytest.param(_manual_impl_obj_attr_try_except, id="manual-impl-try-except"),
        pytest.param(_manual_impl_obj_hasattr_chain, id="manual-impl-hasattr-chain"),
        pytest.param(gloom, id="gloomy"),
        pytest.param(glom, id="glom"),
    ],
)
def test_obj_attr_missing(
    benchmark: BenchmarkFixture,
    impl: Callable,
):
    kwargs = dict(target=Obj(a=Obj(b=Obj(c=None))), spec="a.b.c", default=None)
    if impl is gloom:
        kwargs["spec"] = ("a", "b", "c")

    result = benchmark(impl, **kwargs)
    assert result is None
