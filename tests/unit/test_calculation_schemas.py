from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.calculation_factory import CalculationType
from app.schemas import CalculationCreate, CalculationRead

VALID = {"a": 10, "b": 4, "type": "Divide"}


def test_valid_calculation_create():
    calculation = CalculationCreate(**VALID)
    assert calculation.a == 10.0
    assert calculation.b == 4.0
    assert calculation.type is CalculationType.DIVIDE


@pytest.mark.parametrize(
    "given, expected",
    [
        ("Add", CalculationType.ADD),
        ("add", CalculationType.ADD),
        ("ADD", CalculationType.ADD),
        ("  sub ", CalculationType.SUB),
        ("multiply", CalculationType.MULTIPLY),
        ("DIVIDE", CalculationType.DIVIDE),
        (CalculationType.ADD, CalculationType.ADD),
    ],
)
def test_type_is_normalized(given, expected):
    assert CalculationCreate(a=1, b=2, type=given).type is expected


@pytest.mark.parametrize(
    "bad_type",
    ["Power", "subtract", "", "   ", "Add Sub", None, 5],
)
def test_invalid_types_are_rejected(bad_type):
    with pytest.raises(ValidationError):
        CalculationCreate(a=1, b=2, type=bad_type)


@pytest.mark.parametrize(
    "calculation_type, b",
    [("Divide", 0), ("divide", 0.0), ("DIVIDE", "0"), ("Divide", -0.0)],
)
def test_zero_divisor_is_rejected(calculation_type, b):
    with pytest.raises(ValidationError, match="divide by zero"):
        CalculationCreate(a=10, b=b, type=calculation_type)


@pytest.mark.parametrize("calculation_type", ["Add", "Sub", "Multiply"])
def test_zero_is_allowed_when_not_dividing(calculation_type):
    assert CalculationCreate(a=10, b=0, type=calculation_type).b == 0


def test_zero_dividend_is_allowed():
    assert CalculationCreate(a=0, b=5, type="Divide").a == 0


@pytest.mark.parametrize(
    "field, value",
    [
        ("a", "abc"),
        ("b", "abc"),
        ("a", None),
        ("b", None),
        ("a", ""),
        ("a", float("nan")),
        ("b", float("inf")),
        ("a", float("-inf")),
        ("b", [1]),
    ],
)
def test_bad_operands_are_rejected(field, value):
    with pytest.raises(ValidationError):
        CalculationCreate(**{**VALID, field: value})


@pytest.mark.parametrize("missing", ["a", "b", "type"])
def test_missing_fields_are_rejected(missing):
    data = {key: value for key, value in VALID.items() if key != missing}
    with pytest.raises(ValidationError):
        CalculationCreate(**data)


def test_numeric_strings_are_accepted():
    calculation = CalculationCreate(a="2.5", b="2", type="Add")
    assert (calculation.a, calculation.b) == (2.5, 2.0)


def test_the_error_names_the_bad_field():
    with pytest.raises(ValidationError) as error:
        CalculationCreate(a="x", b=1, type="Add")
    assert error.value.errors()[0]["loc"] == ("a",)


def make_row(**overrides):
    """Stands in for a saved Calculation row."""
    row = {
        "id": 1,
        "a": 10.0,
        "b": 4.0,
        "type": "Divide",
        "result": 2.5,
        "user_id": 3,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    return SimpleNamespace(**{**row, **overrides})


def test_read_copies_the_saved_fields():
    calculation = CalculationRead.model_validate(make_row())
    assert (calculation.id, calculation.a, calculation.b) == (1, 10.0, 4.0)
    assert calculation.type is CalculationType.DIVIDE
    assert calculation.result == 2.5
    assert calculation.user_id == 3


def test_read_exposes_only_the_expected_fields():
    calculation = CalculationRead.model_validate(make_row())
    assert set(calculation.model_dump()) == {
        "id", "a", "b", "type", "result", "user_id", "created_at",
    }


def test_user_id_is_optional_when_reading():
    assert CalculationRead.model_validate(make_row(user_id=None)).user_id is None


def test_read_serializes_the_type_as_plain_text():
    data = CalculationRead.model_validate(make_row()).model_dump(mode="json")
    assert data["type"] == "Divide"


def test_read_rejects_an_unknown_stored_type():
    with pytest.raises(ValidationError):
        CalculationRead.model_validate(make_row(type="Power"))