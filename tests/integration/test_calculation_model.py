from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.models import Calculation, User
from app.schemas import CalculationCreate, CalculationRead
from app.security import hash_password


def make_user(session, username="alice", email="alice@example.com"):
    """Save a user so calculations have someone to belong to."""
    user = User(username=username, email=email, password_hash=hash_password("secret123"))
    session.add(user)
    session.commit()
    return user


def save(session, calculation_type, a, b, user_id=None):
    """Build a calculation with the factory-computed result and save it."""
    calculation = Calculation.create(calculation_type, a, b, user_id=user_id)
    session.add(calculation)
    session.commit()
    session.refresh(calculation)
    return calculation


def submit(session, a, b, calculation_type, user_id=None):
    """Validate the input with the schema, then save it, like a real request would."""
    data = CalculationCreate(a=a, b=b, type=calculation_type)
    return save(session, data.type, data.a, data.b, user_id)


def count_calculations(session):
    return session.scalar(select(func.count()).select_from(Calculation))


def test_saved_calculation_gets_an_id_and_a_timestamp(db_session):
    calculation = save(db_session, "Add", 2, 3)
    assert calculation.id is not None
    assert datetime.now(timezone.utc) - calculation.created_at < timedelta(minutes=1)


@pytest.mark.parametrize(
    "calculation_type, a, b, expected",
    [
        ("Add", 2, 3, 5),
        ("Sub", 5, 3, 2),
        ("Multiply", 4, 5, 20),
        ("Divide", 10, 4, 2.5),
    ],
)
def test_saved_data_round_trips(db_session, calculation_type, a, b, expected):
    calculation_id = save(db_session, calculation_type, a, b).id
    db_session.expire_all()
    loaded = db_session.get(Calculation, calculation_id)
    assert (loaded.a, loaded.b, loaded.type) == (a, b, calculation_type)
    assert loaded.result == pytest.approx(expected)


def test_stored_result_matches_the_factory_result(db_session):
    calculation_id = save(db_session, "Divide", 10, 4).id
    row = db_session.execute(
        text("SELECT a, b, type, result FROM calculations WHERE id = :id"),
        {"id": calculation_id},
    ).one()
    assert tuple(row) == (10.0, 4.0, "Divide", 2.5)


def test_calculation_without_a_user_has_no_user_id(db_session):
    calculation_id = save(db_session, "Add", 1, 1).id
    stored = db_session.execute(
        text("SELECT user_id FROM calculations WHERE id = :id"),
        {"id": calculation_id},
    ).scalar_one()
    assert stored is None


def test_calculation_can_belong_to_a_user(db_session):
    user_id = make_user(db_session).id
    calculation_id = save(db_session, "Add", 1, 1, user_id=user_id).id
    db_session.expire_all()
    assert db_session.get(Calculation, calculation_id).user_id == user_id


def test_a_user_can_have_many_calculations(db_session):
    alice = make_user(db_session, "alice", "alice@example.com")
    bob = make_user(db_session, "bob", "bob@example.com")
    for number in (1, 2, 3):
        save(db_session, "Add", number, number, user_id=alice.id)
    save(db_session, "Multiply", 4, 5, user_id=bob.id)

    rows = db_session.execute(
        select(User.username, func.count(Calculation.id))
        .join(Calculation, Calculation.user_id == User.id)
        .group_by(User.username)
        .order_by(User.username)
    ).all()
    assert [tuple(row) for row in rows] == [("alice", 3), ("bob", 1)]


def test_unknown_user_is_rejected_by_the_foreign_key(db_session):
    with pytest.raises(IntegrityError) as error:
        save(db_session, "Add", 1, 2, user_id=999999)
    assert "foreign key" in str(error.value.orig)
    assert "Key (user_id)=(999999)" in str(error.value.orig)
    db_session.rollback()
    assert count_calculations(db_session) == 0


def test_deleting_a_user_deletes_their_calculations(db_session):
    alice = make_user(db_session, "alice", "alice@example.com")
    bob = make_user(db_session, "bob", "bob@example.com")
    save(db_session, "Add", 1, 1, user_id=alice.id)
    save(db_session, "Sub", 5, 2, user_id=alice.id)
    bobs_calculation_id = save(db_session, "Multiply", 4, 5, user_id=bob.id).id

    db_session.delete(alice)
    db_session.commit()
    db_session.expire_all()

    remaining = db_session.scalars(select(Calculation)).all()
    assert [calculation.id for calculation in remaining] == [bobs_calculation_id]


@pytest.mark.parametrize("bad_type", ["Power", "add", ""])
def test_database_rejects_an_unknown_type(db_session, bad_type):
    db_session.add(Calculation(a=1, b=2, type=bad_type, result=3))
    with pytest.raises(IntegrityError) as error:
        db_session.commit()
    assert "ck_calculations_type" in str(error.value.orig)
    db_session.rollback()
    assert count_calculations(db_session) == 0


def test_database_rejects_a_zero_divisor(db_session):
    db_session.add(Calculation(a=1, b=0, type="Divide", result=0))
    with pytest.raises(IntegrityError) as error:
        db_session.commit()
    assert "ck_calculations_no_zero_divisor" in str(error.value.orig)
    db_session.rollback()
    assert count_calculations(db_session) == 0


@pytest.mark.parametrize(
    "calculation_type, a, b, expected",
    [("Add", 5, 0, 5), ("Divide", 0, 5, 0)],
)
def test_zero_is_stored_where_it_is_valid(db_session, calculation_type, a, b, expected):
    saved = save(db_session, calculation_type, a, b)
    assert saved.result == pytest.approx(expected)


@pytest.mark.parametrize("missing", ["a", "b", "type", "result"])
def test_required_columns_cannot_be_null(db_session, missing):
    values = {"a": 1, "b": 2, "type": "Add", "result": 3}
    del values[missing]
    db_session.add(Calculation(**values))
    with pytest.raises(IntegrityError) as error:
        db_session.commit()
    assert f'null value in column "{missing}"' in str(error.value.orig)


@pytest.mark.parametrize(
    "a, b, calculation_type",
    [
        (1, 2, "Power"),
        (1, 2, "subtract"),
        (1, 0, "Divide"),
        ("abc", 2, "Add"),
        (float("nan"), 2, "Add"),
    ],
)
def test_invalid_input_is_rejected_before_anything_is_saved(
    db_session, a, b, calculation_type
):
    with pytest.raises(ValidationError):
        submit(db_session, a, b, calculation_type)
    assert count_calculations(db_session) == 0


def test_type_is_normalized_before_saving(db_session):
    saved = submit(db_session, 10, 4, "divide")
    assert saved.type == "Divide"
    assert saved.result == pytest.approx(2.5)


def test_read_schema_from_a_saved_calculation(db_session):
    user = make_user(db_session)
    saved = save(db_session, "Multiply", 4, 5, user_id=user.id)
    public = CalculationRead.model_validate(saved)
    assert public.id == saved.id
    assert (public.a, public.b, public.result) == (4.0, 5.0, 20.0)
    assert public.type.value == "Multiply"
    assert public.user_id == user.id
    assert public.created_at.tzinfo is not None