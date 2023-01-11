from typing import Sequence, Type

from sqlalchemy import Inspector, inspect
from sqlalchemy.orm import DeclarativeBase

from postgres_declare.entities.database import Database
from postgres_declare.entities.database_entity import DatabaseEntity
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.schema import Schema


class DatabaseContent(DatabaseEntity):
    def __init__(
        self,
        name: str,
        sqlalchemy_base: Type[DeclarativeBase],
        databases: Sequence[Database],
        schemas: Sequence[Schema] | None = None,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
    ):
        super().__init__(name=name, depends_on=depends_on, databases=databases, check_if_exists=check_if_exists)
        self.base = sqlalchemy_base
        # schemas doesn't do anything since __table_args__ in sqlalchemy defines the schema
        # BUT it helps to have it as a dependency here to remind the user to make schemas they intend to use
        self.schemas = schemas

    def _create(self) -> None:
        for db in self.databases:
            self.base.metadata.create_all(db.db_engine())

    def _exists(self) -> bool:
        tables_in_db = []
        for db in self.databases:
            inspector: Inspector = inspect(db.db_engine())
            tables_in_db.append(
                all(
                    [
                        inspector.has_table(table_name=table.name, schema=table.schema)
                        for table in self.base.metadata.tables.values()
                    ]
                )
            )
        return all(tables_in_db)

    def _drop(self) -> None:
        for db in self.databases:
            self.base.metadata.drop_all(db.db_engine())
