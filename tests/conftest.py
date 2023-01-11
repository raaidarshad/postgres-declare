from typing import Optional, Type

import pytest
from sqlalchemy import Engine, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from postgres_declare.entities.database import Database
from postgres_declare.entities.database_content import DatabaseContent
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role
from postgres_declare.entities.schema import Schema
from tests.helpers import YieldFixture


@pytest.fixture(scope="module")
def engine() -> Engine:
    user = "postgres"
    password = "postgres"
    host = "127.0.0.1"
    port = 5432
    db_name = "postgres"
    return create_engine(f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}")


@pytest.fixture(scope="module")
def entity(engine: Engine) -> YieldFixture[Type[Entity]]:
    Entity._engine = engine
    yield Entity
    Entity.entities = []
    Entity.check_if_any_exist = False


@pytest.fixture(scope="module")
def simple_db(entity: Entity) -> YieldFixture[Database]:
    yield Database(name="simple_db")


@pytest.fixture(scope="module")
def simple_role(entity: Entity) -> YieldFixture[Role]:
    yield Role(name="simple_role")


schema_name = "simple_schema"


@pytest.fixture(scope="module")
def simple_schema(entity: Entity, simple_db: Database) -> YieldFixture[Schema]:
    yield Schema(name=schema_name, databases=[simple_db])


class MyBase(DeclarativeBase):
    pass


class SimpleTable(MyBase):
    __tablename__ = "simple_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]


class FancyTable(MyBase):
    __tablename__ = "fancy_table"
    __table_args__ = {"schema": schema_name}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]


@pytest.fixture(scope="module")
def simple_db_content(entity: Entity, simple_db: Database, simple_schema: Schema) -> YieldFixture[DatabaseContent]:
    yield DatabaseContent(
        name="simple_db_content", databases=[simple_db], schemas=[simple_schema], sqlalchemy_base=MyBase
    )
