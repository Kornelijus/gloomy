from typing import Any, Callable
from glom import glom  # type: ignore[import-untyped]
from gloomy import gloom
import pytest
from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore[import-untyped]

# fmt: off
DICT_KEY_PATH_STR = "alpha.beta.gamma.delta.epsilon"
DICT_KEY_PATH_TUPLE = ("alpha", "beta", "gamma", "delta", "epsilon")
DICT_IN_EXISTS = {"alpha": {"beta": {"gamma": {"delta": {"epsilon": 123}}}}}
DICT_IN_MISSING = {"alpha": {"beta": {"gamma": {"delta": {"epsilon": None}}}}}
# fmt: on


def _manual_impl_dict_key_try_except(target: Any, spec: str, default=None):
    try:
        return target["alpha"]["beta"]["gamma"]["delta"]["epsilon"]
    except (TypeError, KeyError):
        return default


def _manual_impl_dict_key_get_chain(target: Any, spec: str, default=None):
    return target.get("alpha", {}).get("beta", {}).get("gamma", {}).get("delta", {}).get("epsilon", default)


@pytest.mark.parametrize(
    ("spec"),
    [
        pytest.param(DICT_KEY_PATH_STR, id="str"),
        pytest.param(DICT_KEY_PATH_TUPLE, id="tuple"),
    ],
)
@pytest.mark.parametrize(
    ("impl"),
    [
        pytest.param(_manual_impl_dict_key_try_except, id="manual-impl-try-except"),
        pytest.param(_manual_impl_dict_key_get_chain, id="manual-impl-get-chain"),
        pytest.param(gloom, id="gloomy"),
        pytest.param(glom, id="glom"),
    ],
)
def test_dict_key_exists(
    benchmark: BenchmarkFixture,
    impl: Callable,
    spec: tuple | str,
):
    result = benchmark(impl, target=DICT_IN_EXISTS, spec=spec, default=None)
    assert result == 123


@pytest.mark.parametrize(
    ("spec"),
    [
        pytest.param(DICT_KEY_PATH_STR, id="str"),
        pytest.param(DICT_KEY_PATH_TUPLE, id="tuple"),
    ],
)
@pytest.mark.parametrize(
    ("impl"),
    [
        pytest.param(_manual_impl_dict_key_try_except, id="manual-impl-try-except"),
        pytest.param(_manual_impl_dict_key_get_chain, id="manual-impl-get-chain"),
        pytest.param(gloom, id="gloomy"),
        pytest.param(glom, id="glom"),
    ],
)
def test_dict_key_missing(
    benchmark: BenchmarkFixture,
    impl: Callable | None,
    spec: tuple | str,
):
    result = benchmark(impl, target=DICT_IN_MISSING, spec=spec, default=None)
    assert result is None
