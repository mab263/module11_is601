import pytest

from app.calculation_factory import (
    AddOperation,
    CalculationFactory,
    CalculationType,
    DivideOperation,
    MultiplyOperation,
    Operation,
    SubOperation,
)


def test_supported_types():
    assert {t.value for t in CalculationType} == {"Add", "Sub", "Multiply", "Divide"}


@pytest.mark.parametrize(
    "calculation_type, expected_class",
    [
        (CalculationType.ADD, AddOperation),
        (CalculationType.SUB, SubOperation),
        (CalculationType.MULTIPLY, MultiplyOperation),
        (CalculationType.DIVIDE, DivideOperation),
        ("Add", AddOperation),
        ("Sub", SubOperation),
        ("Multiply", MultiplyOperation),
        ("Divide", DivideOperation),
    ],
)
def test_factory_chooses_the_correct_operation(calculation_type, expected_class):
    assert type(CalculationFactory.get_operation(calculation_type)) is expected_class


@pytest.mark.parametrize("calculation_type", list(CalculationType))
def test_every_type_has_an_operation(calculation_type):
    assert isinstance(CalculationFactory.get_operation(calculation_type), Operation)


@pytest.mark.parametrize(
    "calculation_type, a, b, expected",
    [
        ("Add", 2, 3, 5),
        ("Add", -2, 2, 0),
        ("Add", 0.1, 0.2, 0.3),
        ("Sub", 5, 3, 2),
        ("Sub", 3, 5, -2),
        ("Multiply", 4, 5, 20),
        ("Multiply", -2, 3, -6),
        ("Multiply", 7, 0, 0),
        ("Divide", 10, 4, 2.5),
        ("Divide", -9, 3, -3),
        ("Divide", 0, 5, 0),
    ],
)
def test_calculate(calculation_type, a, b, expected):
    assert CalculationFactory.calculate(calculation_type, a, b) == pytest.approx(expected)


def test_divide_by_zero_is_rejected():
    with pytest.raises(ValueError, match="divide by zero"):
        CalculationFactory.calculate(CalculationType.DIVIDE, 10, 0)


@pytest.mark.parametrize("bad_type", ["Power", "", "add", "subtract", "DIVIDE", None, 5])
def test_unknown_types_are_rejected(bad_type):
    with pytest.raises(ValueError):
        CalculationFactory.get_operation(bad_type)


def test_the_base_operation_is_abstract():
    with pytest.raises(TypeError):
        Operation()