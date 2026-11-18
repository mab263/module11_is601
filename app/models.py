"""SQLAlchemy models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.calculation_factory import CalculationFactory, CalculationType
from app.database import Base


class User(Base):
    """A registered user. Only a password hash is stored, never the password."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# Built from the enum, so the allowed values live in one place.
_TYPE_VALUES = ", ".join(f"'{t.value}'" for t in CalculationType)


class Calculation(Base):
    """One calculation, stored together with its result."""

    __tablename__ = "calculations"
    __table_args__ = (
        CheckConstraint(f"type IN ({_TYPE_VALUES})", name="ck_calculations_type"),
        CheckConstraint(
            f"NOT (type = '{CalculationType.DIVIDE.value}' AND b = 0)",
            name="ck_calculations_no_zero_divisor",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    a: Mapped[float] = mapped_column(Float)
    b: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String(20))
    result: Mapped[float] = mapped_column(Float)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    @classmethod
    def create(
        cls,
        calculation_type,
        a: float,
        b: float,
        user_id: Optional[int] = None,
    ) -> "Calculation":
        """Build a Calculation, using the factory to compute the result to store.

        Raises:
            ValueError: if the type is unsupported or the calculation is invalid
                (for example, dividing by zero).
        """
        calculation_type = CalculationType(calculation_type)
        result = CalculationFactory.calculate(calculation_type, a, b)
        return cls(a=a, b=b, type=calculation_type.value, result=result, user_id=user_id)