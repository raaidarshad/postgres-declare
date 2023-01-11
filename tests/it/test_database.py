import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import Engine

from postgres_declare.base import Base
from postgres_declare.entities.database import Database
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role


def test_does_not_exist(simple_db: Database) -> None:
    assert not simple_db._exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(simple_db: Database) -> None:
    simple_db._safe_create()
    assert simple_db._exists()


@pytest.mark.order(after="test_create")
def test_drop(simple_db: Database) -> None:
    simple_db._safe_drop()
    assert not simple_db._exists()


@given(
    allow_connections=st.booleans(),
    connection_limit=st.integers(min_value=-1, max_value=100),
    is_template=st.booleans(),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.order(after="test_drop")
def test_inputs(allow_connections: bool, connection_limit: int, is_template: bool, engine: Engine) -> None:
    Entity._engine = engine
    temp_db = Database(
        name="bar", allow_connections=allow_connections, connection_limit=connection_limit, is_template=is_template
    )
    temp_db._safe_create()
    temp_db._safe_drop()


@pytest.mark.parametrize("template", ["template0", "template1"])
@pytest.mark.order(after="test_drop")
def test_specific_inputs(template: str, engine: Engine) -> None:
    Entity._engine = engine
    temp_db = Database(name="foobar", template=template)
    temp_db._safe_create()
    temp_db._safe_drop()


@pytest.mark.order(after="test_drop")
def test_dependency_inputs(engine: Engine) -> None:
    existing_role = Role(name="existing_role_for_db")
    Database(name="has_owner", owner=existing_role)
    Base.create_all(engine)
    Base.drop_all()
