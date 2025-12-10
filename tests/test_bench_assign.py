from typing import Any, Callable
from copy import deepcopy
from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore[import-untyped]

from gloomy import assign

from glom import assign as glom_assign  # type: ignore[import-untyped]
import pytest

# fmt: off
DICT_KEY_PATH_STR = "alpha.beta.gamma.delta.epsilon"
DICT_KEY_PATH_TUPLE = ("alpha", "beta", "gamma", "delta", "epsilon")
DICT_IN = {"alpha": {"beta": {"gamma": {"delta": {"epsilon": None}}}}}
DICT_OUT = {"alpha": {"beta": {"gamma": {"delta": {"epsilon": 123}}}}}
# fmt: on


def _manual_impl(obj: Any, path: str, val: Any, **kwargs):
    obj["alpha"]["beta"]["gamma"]["delta"]["epsilon"] = val
    return obj


@pytest.mark.parametrize(
    ("impl"),
    [
        pytest.param(glom_assign, id="glom"),
        pytest.param(assign, id="gloomy"),
        pytest.param(_manual_impl, id="manual-impl"),
    ],
)
def test_assign_dict_value(
    benchmark: BenchmarkFixture,
    impl: Callable,
):
    kwargs = {"obj": deepcopy(DICT_IN), "path": DICT_KEY_PATH_STR, "val": 123}

    if impl is assign:
        kwargs["path"] = DICT_KEY_PATH_TUPLE

    expected = DICT_OUT
    result = benchmark(impl, **kwargs)
    assert result == expected
