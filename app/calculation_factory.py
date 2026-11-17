"""Calculation types and the factory that creates the matching operation."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Type, Union


class CalculationType(str, Enum):
    """The supported calculation types. The values are what gets stored."""

    ADD = "Add"
    SUB = "Sub"
    MULTIPLY = "Multiply"
    DIVIDE = "Divide"


class Operation(ABC):
    """Base class for one kind of calculation (Strategy pattern)."""

    @abstractmethod
    def execute(self, a: float, b: float) -> float:
        """Apply the operation to a and b."""


class AddOperation(Operation):
    def execute(self, a: float, b: float) -> float:
        return a + b


class SubOperation(Operation):
    def execute(self, a: float, b: float) -> float:
        return a - b


class MultiplyOperation(Operation):
    def execute(self, a: float, b: float) -> float:
        return a * b


class DivideOperation(Operation):
    def execute(self, a: float, b: float) -> float:
        if b == 0:  # LBYL: check before dividing
            raise ValueError("Cannot divide by zero")
        return a / b


class CalculationFactory:
    """Creates the right Operation for a calculation type (Factory pattern)."""

    _operations: Dict[CalculationType, Type[Operation]] = {
        CalculationType.ADD: AddOperation,
        CalculationType.SUB: SubOperation,
        CalculationType.MULTIPLY: MultiplyOperation,
        CalculationType.DIVIDE: DivideOperation,
    }

    @classmethod
    def get_operation(cls, calculation_type: Union[CalculationType, str]) -> Operation:
        """Return an Operation for the type.

        Raises:
            ValueError: if the type is not one of the supported calculation types.
        """
        return cls._operations[CalculationType(calculation_type)]()

    @classmethod
    def calculate(cls, calculation_type: Union[CalculationType, str], a: float, b: float) -> float:
        """Pick the operation for the type and apply it to a and b."""
        return cls.get_operation(calculation_type).execute(a, b)