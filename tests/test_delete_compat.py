from typing import Any, Callable
from copy import deepcopy

import pytest
from pydantic import BaseModel

from gloomy import delete
from glom import delete as glom_delete, Path  # type: ignore[import-untyped]
from glom import PathAccessError as GlomPathAccessError
from gloomy.errors import PathAccessError

from tests.utils import Obj


# ---------------------------------------------------------------------------
# Pydantic models for complex structure tests
# ---------------------------------------------------------------------------


class Address(BaseModel):
    street: str
    city: str
    zip_code: str | None = None


class Person(BaseModel):
    name: str
    age: int
    address: Address | None = None
    tags: list[str] = []


class Company(BaseModel):
    name: str
    employees: list[Person] = []
    locations: dict[str, Address] = {}
    metadata: dict[str, Any] = {}


class Organization(BaseModel):
    companies: list[Company] = []
    partners: dict[str, Company] = {}


# ---------------------------------------------------------------------------
# Glom adapter: glom.delete uses Path(...) for tuple paths
# ---------------------------------------------------------------------------


def _glom_delete(obj: Any, path: Any, **kwargs) -> Any:
    if isinstance(path, tuple):
        path = Path(*path)
    return glom_delete(obj, path, **kwargs)


# ---------------------------------------------------------------------------
# Parametrised compat tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(delete, id="gloomy"),
        pytest.param(_glom_delete, id="glom"),
    ],
)
class TestDeleteGlomCompat:
    # --- Error cases --------------------------------------------------------

    @pytest.mark.parametrize(
        ("obj", "path"),
        [
            pytest.param({"a": 1}, "b", id="missing-dict-key"),
            pytest.param({"a": {"b": 1}}, "a.c", id="missing-nested-dict-key"),
            pytest.param([1, 2, 3], "5", id="list-index-out-of-range"),
            pytest.param({}, "a.b", id="empty-dict-nested"),
        ],
    )
    def test_raises_path_access_error(self, impl: Callable, obj: Any, path: str):
        with pytest.raises((PathAccessError, GlomPathAccessError)):
            impl(deepcopy(obj), path)

    @pytest.mark.parametrize(
        ("obj", "path"),
        [
            pytest.param({"a": 1}, "b", id="missing-dict-key"),
            pytest.param({"a": {"b": 1}}, "a.c", id="missing-nested-dict-key"),
            pytest.param([1, 2, 3], "5", id="list-index-out-of-range"),
            pytest.param({}, "a.b", id="missing-intermediate"),
        ],
    )
    def test_ignore_missing_suppresses_error(self, impl: Callable, obj: Any, path: str):
        original = deepcopy(obj)
        result = impl(deepcopy(obj), path, ignore_missing=True)
        assert result == original

    # --- Dict operations ----------------------------------------------------

    def test_delete_dict_key(self, impl: Callable):
        data = {"a": 1, "b": 2}
        result = impl(data, "a")
        assert "a" not in result
        assert result["b"] == 2

    def test_delete_nested_dict_key(self, impl: Callable):
        data = {"outer": {"inner": 42, "keep": "yes"}}
        result = impl(data, "outer.inner")
        assert "inner" not in result["outer"]
        assert result["outer"]["keep"] == "yes"

    def test_delete_deep_nested_dict(self, impl: Callable):
        data = {"a": {"b": {"c": {"d": "target", "keep": 1}}}}
        path = ("a", "b", "c", "d")
        if impl is _glom_delete:
            path = Path(*path)
        result = impl(data, path)
        assert "d" not in result["a"]["b"]["c"]
        assert result["a"]["b"]["c"]["keep"] == 1

    # --- List operations ----------------------------------------------------

    def test_delete_list_item_by_index(self, impl: Callable):
        data = {"items": [10, 20, 30]}
        result = impl(data, "items.1")
        assert result["items"] == [10, 30]

    def test_delete_first_list_item(self, impl: Callable):
        data = {"items": ["a", "b", "c"]}
        result = impl(data, "items.0")
        assert result["items"] == ["b", "c"]

    def test_delete_last_list_item(self, impl: Callable):
        data = {"items": [1, 2, 3]}
        result = impl(data, "items.2")
        assert result["items"] == [1, 2]

    # --- Object attribute operations ----------------------------------------

    def test_delete_plain_object_attribute(self, impl: Callable):
        obj = Obj(x=1, y=2)
        result = impl(obj, "x")
        assert not hasattr(result, "x")
        assert result.y == 2

    def test_delete_nested_plain_object_attribute(self, impl: Callable):
        obj = Obj(inner=Obj(val=42, keep=99))
        path = ("inner", "val")
        if impl is _glom_delete:
            path = Path(*path)
        result = impl(obj, path)
        assert not hasattr(result.inner, "val")
        assert result.inner.keep == 99

    # --- Pydantic model operations ------------------------------------------

    def test_delete_pydantic_field(self, impl: Callable):
        """Delete an optional field value from a pydantic model by setting through delattr"""
        # Pydantic models don't support delattr for required fields;
        # test with metadata dict inside a model instead
        company = Company(name="Acme", metadata={"foo": "bar", "baz": 42})
        path = ("metadata", "foo")
        if impl is _glom_delete:
            path = Path(*path)
        result = impl(company, path)
        assert "foo" not in result.metadata
        assert result.metadata["baz"] == 42

    def test_delete_in_nested_pydantic_dict(self, impl: Callable):
        company = Company(
            name="Acme",
            locations={
                "hq": Address(street="1 Main St", city="NYC"),
                "branch": Address(street="2 Oak Ave", city="LA"),
            },
        )
        path = ("locations", "branch")
        if impl is _glom_delete:
            path = Path(*path)
        result = impl(company, path)
        assert "branch" not in result.locations
        assert "hq" in result.locations

    def test_delete_in_dict_of_models(self, impl: Callable):
        data: dict[str, Any] = {
            "users": {
                "alice": {"age": 30, "role": "admin"},
                "bob": {"age": 25, "role": "user"},
            }
        }
        path = ("users", "alice", "role")
        if impl is _glom_delete:
            path = Path(*path)
        result = impl(data, path)
        assert "role" not in result["users"]["alice"]
        assert result["users"]["alice"]["age"] == 30
        assert result["users"]["bob"]["role"] == "user"

    # --- Mixed structure operations -----------------------------------------

    def test_delete_through_dict_list_dict(self, impl: Callable):
        data = {"outer": [{"key": "val", "other": 1}, {"key": "val2"}]}
        path = ("outer", "0", "key")
        if impl is _glom_delete:
            path = Path(*path)
        result = impl(data, path)
        assert "key" not in result["outer"][0]
        assert result["outer"][0]["other"] == 1
        assert result["outer"][1]["key"] == "val2"

    def test_delete_in_complex_nested_structure(self, impl: Callable):
        data = {
            "organizations": [
                Organization(
                    partners={
                        "main": Company(name="MainCo", metadata={"secret": "value", "public": "data"}),
                        "other": Company(name="OtherCo"),
                    }
                )
            ]
        }
        path = ("organizations", "0", "partners", "main", "metadata", "secret")
        if impl is _glom_delete:
            path = Path(*path)
        result = impl(data, path)
        assert "secret" not in result["organizations"][0].partners["main"].metadata
        assert result["organizations"][0].partners["main"].metadata["public"] == "data"

    # --- Return value -------------------------------------------------------

    def test_returns_original_object(self, impl: Callable):
        data = {"a": 1, "b": 2}
        result = impl(data, "a")
        assert result is data

    def test_returns_original_on_ignore_missing(self, impl: Callable):
        data = {"a": 1}
        result = impl(data, "missing_key", ignore_missing=True)
        assert result is data

    # --- Path format --------------------------------------------------------

    def test_string_path(self, impl: Callable):
        data = {"a": {"b": "delete_me", "c": "keep"}}
        result = impl(deepcopy(data), "a.b")
        assert "b" not in result["a"]
        assert result["a"]["c"] == "keep"

    def test_tuple_path(self, impl: Callable):
        data = {"a": {"b": "delete_me", "c": "keep"}}
        path: Any = ("a", "b")
        if impl is _glom_delete:
            path = Path("a", "b")
        result = impl(deepcopy(data), path)
        assert "b" not in result["a"]
        assert result["a"]["c"] == "keep"

    def test_string_and_tuple_path_equivalent(self, impl: Callable):
        data1 = {"x": {"y": {"z": "gone"}}}
        data2 = deepcopy(data1)

        result1 = impl(data1, "x.y.z")
        path2: Any = ("x", "y", "z")
        if impl is _glom_delete:
            path2 = Path("x", "y", "z")
        result2 = impl(data2, path2)

        assert result1 == result2

    # --- Numeric string keys ------------------------------------------------

    def test_delete_list_element_by_string_index(self, impl: Callable):
        data = [10, 20, 30, 40]
        result = impl(data, "2")
        assert result == [10, 20, 40]

    def test_delete_nested_list_element(self, impl: Callable):
        data = {"rows": [[1, 2, 3], [4, 5, 6]]}
        path = ("rows", "1", "0")
        if impl is _glom_delete:
            path = Path(*path)
        result = impl(data, path)
        assert result["rows"][1] == [5, 6]
        assert result["rows"][0] == [1, 2, 3]

    # --- Edge: ignore_missing with partial path -----------------------------

    def test_ignore_missing_returns_obj_on_missing_intermediate(self, impl: Callable):
        data = {"a": {}}
        result = impl(data, "a.b.c", ignore_missing=True)
        assert result is data
        assert data == {"a": {}}

    def test_ignore_missing_still_deletes_when_path_exists(self, impl: Callable):
        data = {"a": {"b": "target", "c": "keep"}}
        result = impl(data, "a.b", ignore_missing=True)
        assert "b" not in result["a"]
        assert result["a"]["c"] == "keep"
