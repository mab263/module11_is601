import pytest
from sqlalchemy import CheckConstraint

from app.calculation_factory import CalculationType
from app.models import Calculation


@pytest.mark.parametrize(
    "calculation_type, a, b, expected",
    [
        ("Add", 2, 3, 5),
        ("Sub", 5, 3, 2),
        ("Multiply", 4, 5, 20),
        ("Divide", 10, 4, 2.5),
    ],
)
def test_create_stores_the_inputs_and_the_computed_result(calculation_type, a, b, expected):
    calculation = Calculation.create(calculation_type, a, b)
    assert (calculation.a, calculation.b) == (a, b)
    assert calculation.type == calculation_type
    assert calculation.result == pytest.approx(expected)
    assert calculation.user_id is None


@pytest.mark.parametrize("calculation_type", [CalculationType.ADD, "Add"])
def test_create_accepts_the_enum_or_its_string_value(calculation_type):
    assert Calculation.create(calculation_type, 1, 2).type == "Add"


def test_create_can_attach_a_user():
    assert Calculation.create("Add", 1, 2, user_id=7).user_id == 7


@pytest.mark.parametrize("bad_type", ["Power", "add", None])
def test_create_rejects_unsupported_types(bad_type):
    with pytest.raises(ValueError):
        Calculation.create(bad_type, 1, 2)


def test_create_rejects_a_zero_divisor():
    with pytest.raises(ValueError, match="divide by zero"):
        Calculation.create("Divide", 10, 0)


def test_table_has_the_expected_columns():
    assert set(Calculation.__table__.columns.keys()) == {
        "id", "a", "b", "type", "result", "user_id", "created_at",
    }


@pytest.mark.parametrize("column_name", ["a", "b", "type", "result"])
def test_required_columns_are_not_nullable(column_name):
    assert Calculation.__table__.c[column_name].nullable is False


def test_user_id_is_an_optional_foreign_key_to_users():
    column = Calculation.__table__.c.user_id
    foreign_key = next(iter(column.foreign_keys))
    assert column.nullable is True
    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"


def test_check_constraints_are_defined():
    names = {
        constraint.name
        for constraint in Calculation.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert names == {"ck_calculations_type", "ck_calculations_no_zero_divisor"}