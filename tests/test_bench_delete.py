from typing import Any, Callable
from copy import deepcopy

import pytest
from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore[import-untyped]
from pydantic import BaseModel

from gloomy import delete
from glom import delete as glom_delete, Path  # type: ignore[import-untyped]

from tests.utils import Obj

pytestmark = [pytest.mark.bench]

# ---------------------------------------------------------------------------
# Glom adapter (converts tuple paths to glom.Path)
# ---------------------------------------------------------------------------


def _glom_delete(obj: Any, path: Any, **kwargs) -> Any:
    if isinstance(path, tuple):
        path = Path(*path)
    return glom_delete(obj, path, **kwargs)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SimpleModel(BaseModel):
    value: int
    extra: str = "keep"


class NestedModel(BaseModel):
    nested: SimpleModel
    metadata: dict[str, Any] = {}


class DeepModel(BaseModel):
    level1: NestedModel


# ---------------------------------------------------------------------------
# Manual baseline implementations
# ---------------------------------------------------------------------------


def _manual_delete_dict_shallow(obj: Any, path: Any, **kwargs) -> Any:
    del obj["epsilon"]
    return obj


def _manual_delete_dict_deep(obj: Any, path: Any, **kwargs) -> Any:
    del obj["alpha"]["beta"]["gamma"]["delta"]["epsilon"]
    return obj


def _manual_delete_list_index(obj: Any, path: Any, **kwargs) -> Any:
    del obj["items"][2]
    return obj


# ---------------------------------------------------------------------------
# Shallow dict deletions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
        pytest.param(_manual_delete_dict_shallow, id="manual-impl"),
    ],
)
def test_delete_dict_shallow(benchmark: BenchmarkFixture, impl: Callable):
    """1-level dict key deletion."""

    def setup():
        return {"alpha": 1, "beta": 2, "gamma": 3, "delta": 4, "epsilon": 5}

    path = "epsilon" if impl is _glom_delete else ("epsilon",)
    result = benchmark(lambda: impl(setup(), path))
    assert "epsilon" not in result


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_dict_2levels(benchmark: BenchmarkFixture, impl: Callable):
    """2-level dict key deletion."""

    def setup():
        return {"a": {"b": "target", "c": "keep"}}

    path = "a.b" if impl is _glom_delete else ("a", "b")
    result = benchmark(lambda: impl(setup(), path))
    assert "b" not in result["a"]


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_dict_3levels(benchmark: BenchmarkFixture, impl: Callable):
    """3-level dict key deletion."""

    def setup():
        return {"a": {"b": {"c": "target", "d": "keep"}}}

    path = "a.b.c" if impl is _glom_delete else ("a", "b", "c")
    result = benchmark(lambda: impl(setup(), path))
    assert "c" not in result["a"]["b"]


# ---------------------------------------------------------------------------
# Deep dict deletion (5 levels)
# ---------------------------------------------------------------------------

DEEP_DICT_PATH_STR = "alpha.beta.gamma.delta.epsilon"
DEEP_DICT_PATH_TUPLE = ("alpha", "beta", "gamma", "delta", "epsilon")


def _make_deep_dict() -> dict:
    return {"alpha": {"beta": {"gamma": {"delta": {"epsilon": "gone", "keep": "yes"}}}}}


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
        pytest.param(_manual_delete_dict_deep, id="manual-impl"),
    ],
)
def test_delete_dict_5levels(benchmark: BenchmarkFixture, impl: Callable):
    """5-level nested dict key deletion."""
    path = DEEP_DICT_PATH_STR if impl is _glom_delete else DEEP_DICT_PATH_TUPLE
    result = benchmark(lambda: impl(_make_deep_dict(), path))
    assert "epsilon" not in result["alpha"]["beta"]["gamma"]["delta"]
    assert result["alpha"]["beta"]["gamma"]["delta"]["keep"] == "yes"


# ---------------------------------------------------------------------------
# 10-level deep dict deletion
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_dict_10levels(benchmark: BenchmarkFixture, impl: Callable):
    """10-level nested dict key deletion."""
    data_template = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": "target", "k": "keep"}}}}}}}}}}
    path = "a.b.c.d.e.f.g.h.i.j" if impl is _glom_delete else ("a", "b", "c", "d", "e", "f", "g", "h", "i", "j")

    result = benchmark(lambda: impl(deepcopy(data_template), path))
    assert "j" not in result["a"]["b"]["c"]["d"]["e"]["f"]["g"]["h"]["i"]


# ---------------------------------------------------------------------------
# List index deletion
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
        pytest.param(_manual_delete_list_index, id="manual-impl"),
    ],
)
def test_delete_list_index(benchmark: BenchmarkFixture, impl: Callable):
    """Delete element from list at index 2."""

    def setup():
        return {"items": [10, 20, 30, 40, 50]}

    path = "items.2" if impl is _glom_delete else ("items", "2")
    result = benchmark(lambda: impl(setup(), path))
    assert result["items"] == [10, 20, 40, 50]


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_nested_list_element(benchmark: BenchmarkFixture, impl: Callable):
    """Delete element from nested list (dict -> list -> list)."""

    def setup():
        return {"rows": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}

    path = "rows.1.0" if impl is _glom_delete else ("rows", "1", "0")
    result = benchmark(lambda: impl(setup(), path))
    assert result["rows"][1] == [5, 6]


# ---------------------------------------------------------------------------
# Large collection deletions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_key_in_large_dict(benchmark: BenchmarkFixture, impl: Callable):
    """Delete a key from a dict with 1000 siblings."""

    def setup():
        d = {f"key{i}": i for i in range(1000)}
        d["target"] = "delete_me"
        return d

    path = "target" if impl is _glom_delete else ("target",)
    result = benchmark(lambda: impl(setup(), path))
    assert "target" not in result


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_element_from_large_list(benchmark: BenchmarkFixture, impl: Callable):
    """Delete element at index 500 from a 1001-element list."""

    def setup():
        return {"items": list(range(1001))}

    path = "items.500" if impl is _glom_delete else ("items", "500")
    result = benchmark(lambda: impl(setup(), path))
    assert len(result["items"]) == 1000
    assert result["items"][499] == 499
    assert result["items"][500] == 501


# ---------------------------------------------------------------------------
# Plain object attribute deletion
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_plain_object_attr(benchmark: BenchmarkFixture, impl: Callable):
    """Delete an attribute from a plain Python object."""

    def setup():
        return Obj(x=1, y=2, z=3)

    path = "x" if impl is _glom_delete else ("x",)
    result = benchmark(lambda: impl(setup(), path))
    assert not hasattr(result, "x")
    assert result.y == 2


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_nested_plain_object_attr(benchmark: BenchmarkFixture, impl: Callable):
    """Delete a nested attribute from plain Python objects."""

    def setup():
        return Obj(inner=Obj(val=42, keep=99))

    path = "inner.val" if impl is _glom_delete else ("inner", "val")
    result = benchmark(lambda: impl(setup(), path))
    assert not hasattr(result.inner, "val")
    assert result.inner.keep == 99


# ---------------------------------------------------------------------------
# Pydantic model field deletion (via dict field)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_pydantic_dict_field(benchmark: BenchmarkFixture, impl: Callable):
    """Delete a key from a dict field inside a Pydantic model."""

    def setup():
        return NestedModel(nested=SimpleModel(value=10), metadata={"remove": True, "keep": "yes"})

    path = "metadata.remove" if impl is _glom_delete else ("metadata", "remove")
    result = benchmark(lambda: impl(setup(), path))
    assert "remove" not in result.metadata
    assert result.metadata["keep"] == "yes"


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_pydantic_deep_dict_field(benchmark: BenchmarkFixture, impl: Callable):
    """Delete from dict field nested deep in Pydantic models."""

    def setup():
        return DeepModel(level1=NestedModel(nested=SimpleModel(value=5), metadata={"gone": 1, "stay": 2}))

    path = "level1.metadata.gone" if impl is _glom_delete else ("level1", "metadata", "gone")
    result = benchmark(lambda: impl(setup(), path))
    assert "gone" not in result.level1.metadata
    assert result.level1.metadata["stay"] == 2


# ---------------------------------------------------------------------------
# Mixed structure deletions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_mixed_dict_list_dict(benchmark: BenchmarkFixture, impl: Callable):
    """Delete key from dict inside a list inside a dict."""

    def setup():
        return {"outer": [{"remove": True, "keep": 1}, {"remove": True}]}

    path = "outer.0.remove" if impl is _glom_delete else ("outer", "0", "remove")
    result = benchmark(lambda: impl(setup(), path))
    assert "remove" not in result["outer"][0]
    assert result["outer"][0]["keep"] == 1
    assert "remove" in result["outer"][1]


# ---------------------------------------------------------------------------
# String vs tuple path (gloomy only)
# ---------------------------------------------------------------------------


def test_delete_gloomy_string_path(benchmark: BenchmarkFixture):
    """Benchmark gloomy with a string path."""

    def setup():
        return {"a": {"b": {"c": "target", "d": "keep"}}}

    result = benchmark(lambda: delete(setup(), "a.b.c"))
    assert "c" not in result["a"]["b"]


def test_delete_gloomy_tuple_path(benchmark: BenchmarkFixture):
    """Benchmark gloomy with a tuple path."""

    def setup():
        return {"a": {"b": {"c": "target", "d": "keep"}}}

    result = benchmark(lambda: delete(setup(), ("a", "b", "c")))
    assert "c" not in result["a"]["b"]


# ---------------------------------------------------------------------------
# ignore_missing overhead
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_ignore_missing_hit(benchmark: BenchmarkFixture, impl: Callable):
    """Deletion where the path exists (ignore_missing=True doesn't add overhead)."""

    def setup():
        return {"a": {"b": "target", "c": "keep"}}

    path = "a.b" if impl is _glom_delete else ("a", "b")
    result = benchmark(lambda: impl(setup(), path, ignore_missing=True))
    assert "b" not in result["a"]


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_ignore_missing_miss(benchmark: BenchmarkFixture, impl: Callable):
    """Deletion where the path is missing (ignore_missing=True returns early)."""

    def setup():
        return {"a": {"c": "keep"}}

    path = "a.b" if impl is _glom_delete else ("a", "b")
    result = benchmark(lambda: impl(setup(), path, ignore_missing=True))
    assert result == {"a": {"c": "keep"}}


# ---------------------------------------------------------------------------
# Realistic API-response scenario
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_glom_delete, id="glom"),
        pytest.param(delete, id="gloomy"),
    ],
)
def test_delete_realistic_api_response(benchmark: BenchmarkFixture, impl: Callable):
    """Realistic: scrub a sensitive field from a nested API response dict."""

    def setup():
        return {
            "status": "success",
            "data": {
                "users": [
                    {"id": 1, "name": "Alice", "ssn": "111-22-3333", "role": "admin"},
                    {"id": 2, "name": "Bob", "ssn": "444-55-6666", "role": "user"},
                    {"id": 3, "name": "Charlie", "ssn": "777-88-9999", "role": "user"},
                ]
            },
            "metadata": {"page": 1, "total": 3},
        }

    path = "data.users.1.ssn" if impl is _glom_delete else ("data", "users", "1", "ssn")
    result = benchmark(lambda: impl(setup(), path))
    assert "ssn" not in result["data"]["users"][1]
    assert result["data"]["users"][0]["ssn"] == "111-22-3333"
    assert result["data"]["users"][2]["ssn"] == "777-88-9999"
