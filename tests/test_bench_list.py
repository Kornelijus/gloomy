from typing import Callable
from glom import glom, Path as GlomPath  # type: ignore[import-untyped]
from gloomy import gloom
import pytest
from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore[import-untyped]

# fmt: off
LIST_INDEX_PATH_STR = "0.1.2.3.4"
LIST_INDEX_PATH_TUPLE = (0, 1, 2, 3, 4)
LIST_IN_EXISTS = [[None, [None, None, [None, None, None, [None, None, None, None, 123]]]]]
LIST_IN_MISSING = [[None, [None, None, [None, None, None, [None, None, None, None, None]]]]]
# fmt: on


@pytest.mark.parametrize(
    ("spec"),
    [
        pytest.param(LIST_INDEX_PATH_STR, id="str"),
        pytest.param(LIST_INDEX_PATH_TUPLE, id="tuple"),
    ],
)
@pytest.mark.parametrize(
    ("impl"),
    [
        pytest.param(gloom, id="gloomy"),
        pytest.param(glom, id="glom"),
    ],
)
def test_list_index_exists(
    benchmark: BenchmarkFixture,
    impl: Callable,
    spec: tuple | str,
):
    if impl is glom and isinstance(spec, tuple):
        spec = GlomPath(*spec)
    result = benchmark(impl, target=LIST_IN_EXISTS, spec=spec, default=None)
    assert result == 123


@pytest.mark.parametrize(
    ("spec"),
    [
        pytest.param(LIST_INDEX_PATH_STR, id="str"),
        pytest.param(LIST_INDEX_PATH_TUPLE, id="tuple"),
    ],
)
@pytest.mark.parametrize(
    ("impl"),
    [
        pytest.param(gloom, id="gloomy"),
        pytest.param(glom, id="glom"),
    ],
)
def test_list_index_missing(
    benchmark: BenchmarkFixture,
    impl: Callable | None,
    spec: tuple | str,
):
    if impl is glom and isinstance(spec, tuple):
        spec = GlomPath(*spec)
    result = benchmark(impl, target=LIST_IN_MISSING, spec=spec, default=None)
    assert result is None
