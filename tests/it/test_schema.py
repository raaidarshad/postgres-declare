import pytest
from sqlalchemy import Engine

from postgres_declare.base import Base
from postgres_declare.entities.database import Database
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role
from postgres_declare.entities.schema import Schema


def test_does_not_exist(simple_schema: Schema, simple_db: Database) -> None:
    simple_db._safe_create()
    assert not simple_schema._exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(simple_schema: Schema) -> None:
    simple_schema._safe_create()
    assert simple_schema._exists()


@pytest.mark.order(after="test_create")
def test_drop(simple_schema: Schema, simple_db: Database) -> None:
    simple_schema._safe_drop()
    assert not simple_schema._exists()
    # clean up database
    simple_db._safe_drop()


@pytest.mark.order(after="test_drop")
def test_dependency_inputs(engine: Engine) -> None:
    Entity.entities = []
    Entity.check_if_any_exist = False
    existing_role = Role(name="existing_role_for_schema")
    existing_db = Database(name="foobar")
    Schema(name="has_owner", databases=[existing_db], owner=existing_role)
    Base.create_all(engine)
    Base.drop_all()
