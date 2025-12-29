# VIBECODED

from typing import Any, Callable
from copy import deepcopy

import pytest
from pydantic import BaseModel

from gloomy import assign
from glom import assign as glom_assign, Path  # type: ignore[import-untyped]
from glom import PathAssignError as GlomPathAssignError, PathAccessError as GlomPathAccessError
from gloomy.errors import PathAssignError, PathAccessError


class Address(BaseModel):
    street: str
    city: str
    zip_code: str | None = None


class Person(BaseModel):
    name: str
    age: int
    address: Address | None = None


class Company(BaseModel):
    name: str
    employees: list[Person] = []
    locations: dict[str, Address] = {}


class Organization(BaseModel):
    companies: list[Company] = []
    partners: dict[str, Company] = {}


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(assign, id="gloomy"),
        pytest.param(glom_assign, id="glom"),
    ],
)
class TestAssignGlomCompat:
    @pytest.mark.parametrize(
        ("obj", "path"),
        [
            (None, "a"),
            ("abc", "a"),
            (123, "a"),
            ([], "1"),
        ],
    )
    def test_raises_path_assign_error(self, impl: Callable, obj: Any, path: str):
        """Test assignment when target is None"""
        with pytest.raises((PathAssignError, GlomPathAssignError)):
            impl(obj, path, 1)

    @pytest.mark.parametrize(
        ("obj", "path"),
        [
            ({"a": 123}, "b.a"),
        ],
    )
    def test_raises_path_access_error(self, impl: Callable, obj: Any, path: str):
        """Test assignment when target is None"""
        with pytest.raises((PathAccessError, GlomPathAccessError)):
            impl(obj, path, 1)

    def test_assign_nested_dict_list_pydantic(self, impl: Callable):
        """Test assignment through dict -> list -> pydantic model"""
        data = {
            "orgs": [
                Organization(
                    companies=[
                        Company(
                            name="TechCorp",
                            employees=[
                                Person(name="Alice", age=30, address=Address(street="123 Main", city="NYC")),
                                Person(name="Bob", age=25),
                            ],
                        )
                    ]
                )
            ]
        }

        # Assign to nested pydantic model attribute through dict and list
        path = ("orgs", "0", "companies", "0", "employees", "1", "age")
        if impl is glom_assign:
            path = Path(*path)
        result = impl(data, path, 26)

        assert result["orgs"][0].companies[0].employees[1].age == 26
        assert result["orgs"][0].companies[0].employees[0].age == 30  # unchanged

    def test_assign_dict_str_model(self, impl: Callable):
        """Test assignment through dict[str, Model]"""
        org = Organization(
            partners={
                "north": Company(name="North Inc"),
                "south": Company(name="South LLC"),
            }
        )

        path = ("partners", "north", "name")
        if impl is glom_assign:
            path = Path(*path)
        result = impl(org, path, "North Industries")

        assert result.partners["north"].name == "North Industries"
        assert result.partners["south"].name == "South LLC"  # unchanged

    def test_assign_list_model_nested(self, impl: Callable):
        """Test assignment to nested list of models"""
        company = Company(
            name="MegaCorp",
            employees=[
                Person(name="Charlie", age=35, address=Address(street="456 Oak", city="LA")),
                Person(name="Diana", age=28, address=Address(street="789 Pine", city="SF")),
            ],
        )

        path = ("employees", "1", "address", "zip_code")
        if impl is glom_assign:
            path = Path(*path)
        result = impl(company, path, "94102")

        assert result.employees[1].address.zip_code == "94102"
        assert result.employees[0].address.zip_code is None  # unchanged

    def test_assign_complex_nested_path(self, impl: Callable):
        """Test very complex nested path: dict -> list -> model -> dict -> model"""
        data = {
            "organizations": [
                Organization(
                    companies=[
                        Company(
                            name="GlobalTech",
                            locations={
                                "hq": Address(street="100 Tech Way", city="Austin"),
                                "branch": Address(street="200 Branch St", city="Seattle"),
                            },
                        )
                    ]
                )
            ]
        }

        path = ("organizations", "0", "companies", "0", "locations", "branch", "city")
        if impl is glom_assign:
            path = Path(*path)
        result = impl(data, path, "Portland")

        assert result["organizations"][0].companies[0].locations["branch"].city == "Portland"
        assert result["organizations"][0].companies[0].locations["hq"].city == "Austin"  # unchanged

    def test_assign_model_list_in_dict(self, impl: Callable):
        """Test assignment to model inside list which is in a dict"""
        data = {
            "teams": {
                "engineering": [
                    Person(name="Eve", age=32),
                    Person(name="Frank", age=29),
                ],
                "sales": [
                    Person(name="Grace", age=27),
                ],
            }
        }

        path = ("teams", "engineering", "0", "age")
        if impl is glom_assign:
            path = Path(*path)
        result = impl(data, path, 33)

        assert result["teams"]["engineering"][0].age == 33
        assert result["teams"]["engineering"][1].age == 29  # unchanged
        assert result["teams"]["sales"][0].age == 27  # unchanged

    def test_assign_deeply_nested_mixed(self, impl: Callable):
        """Test deeply nested mixed structures"""
        org = Organization(
            partners={
                "main": Company(
                    name="MainCo",
                    employees=[
                        Person(name="Henry", age=40, address=Address(street="321 Elm", city="Boston", zip_code="02101"))
                    ],
                    locations={"office": Address(street="500 Corp Blvd", city="Boston")},
                )
            }
        )

        # Assign through: model -> dict[str, model] -> list[model] -> model -> model
        path = ("partners", "main", "employees", "0", "address", "zip_code")
        if impl is glom_assign:
            path = Path(*path)
        result = impl(org, path, "02102")

        assert result.partners["main"].employees[0].address.zip_code == "02102"

    def test_assign_model_to_none_address(self, impl: Callable):
        """Test assignment when intermediate model field is None"""
        person = Person(name="Iris", age=24, address=None)

        # Should raise because address is None and we have no missing handler
        path = ("address", "city")
        if impl is glom_assign:
            path = Path(*path)
        with pytest.raises(Exception):  # PathAccessError or AttributeError
            impl(person, path, "Chicago")

    def test_assign_with_missing_callback(self, impl: Callable):
        """Test assignment with missing callback to create intermediate objects in dict"""
        # Use a dict where we can create missing intermediate values
        data: dict = {"config": {}}

        def create_nested_dict():
            return {}

        path = ("config", "database", "host")
        if impl is glom_assign:
            path = Path(*path)
            result = impl(data, path, "localhost", missing=create_nested_dict)
        else:
            result = impl(data, path, "localhost", missing=create_nested_dict)

        assert result["config"]["database"]["host"] == "localhost"

    def test_assign_with_missing_pydantic_in_dict(self, impl: Callable):
        """Test assignment with missing callback creating pydantic models in dict structure"""
        data: dict = {"companies": {}}

        def create_company():
            return Company(name="", employees=[], locations={})

        path = ("companies", "tech", "name")
        if impl is glom_assign:
            path = Path(*path)
            result = impl(data, path, "TechCorp", missing=create_company)
        else:
            result = impl(data, path, "TechCorp", missing=create_company)

        assert result["companies"]["tech"].name == "TechCorp"
        assert isinstance(result["companies"]["tech"], Company)

    def test_assign_list_index_in_pydantic(self, impl: Callable):
        """Test numeric string index on list field in pydantic model"""
        company = Company(
            name="StartupInc",
            employees=[
                Person(name="Kelly", age=26),
                Person(name="Leo", age=31),
                Person(name="Mia", age=28),
            ],
        )

        path = ("employees", "2", "name")
        if impl is glom_assign:
            path = Path(*path)
        result = impl(company, path, "Mia Chen")

        assert result.employees[2].name == "Mia Chen"
        assert result.employees[0].name == "Kelly"
        assert result.employees[1].name == "Leo"

    def test_assign_returns_original_object(self, impl: Callable):
        """Test that assign returns the same object (mutates in place)"""
        data = {"value": {"nested": 10}}

        path = ("value", "nested")
        if impl is glom_assign:
            path = Path(*path)
        result = impl(data, path, 20)

        assert result is data
        assert data["value"]["nested"] == 20

    def test_assign_string_path_vs_tuple_path(self, impl: Callable):
        """Test both string and tuple path formats"""
        data = {"level1": {"level2": {"level3": 100}}}

        # String path
        result1 = impl(deepcopy(data), "level1.level2.level3", 200)
        assert result1["level1"]["level2"]["level3"] == 200

        # Tuple path / Path
        if impl is glom_assign:
            path = Path("level1", "level2", "level3")
        else:
            path = ("level1", "level2", "level3")
        result2 = impl(deepcopy(data), path, 300)
        assert result2["level1"]["level2"]["level3"] == 300
