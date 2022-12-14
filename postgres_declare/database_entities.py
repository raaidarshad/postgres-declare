from typing import Sequence, Type

from sqlalchemy import Inspector, TextClause, inspect, text
from sqlalchemy.orm import DeclarativeBase

from postgres_declare.base_entity import Entity
from postgres_declare.cluster_entities import Database, Role
from postgres_declare.mixins import SQLMixin


class DatabaseEntity(Entity):
    def __init__(
        self,
        name: str,
        databases: Sequence[Database],
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
    ):
        self.databases: Sequence[Database] = databases
        super().__init__(name=name, depends_on=depends_on, check_if_exists=check_if_exists)


class DatabaseSqlEntity(SQLMixin, DatabaseEntity):
    def create(self) -> None:
        for db in self.databases:
            self._commit_sql(engine=db.db_engine(), statements=self.create_statements())

    def exists(self) -> bool:
        return all(
            [self._fetch_sql(engine=db.db_engine(), statement=self.exists_statement())[0][0] for db in self.databases]
        )

    def remove(self) -> None:
        for db in self.databases:
            self._commit_sql(engine=db.db_engine(), statements=self.remove_statements())


class Schema(DatabaseSqlEntity):
    def __init__(
        self,
        name: str,
        databases: Sequence[Database],
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
        owner: Role | None = None,
    ):
        self.owner = owner
        super().__init__(name=name, depends_on=depends_on, databases=databases, check_if_exists=check_if_exists)

    def create_statements(self) -> Sequence[TextClause]:
        statement = f"CREATE SCHEMA {self.name}"

        if self.owner:
            statement = f"{statement} AUTHORIZATION {self.owner.name}"

        return [text(statement)]

    def exists_statement(self) -> TextClause:
        return text("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=:schema)").bindparams(schema=self.name)

    def remove_statements(self) -> Sequence[TextClause]:
        return [text(f"DROP SCHEMA {self.name}")]


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

    def create(self) -> None:
        for db in self.databases:
            self.base.metadata.create_all(db.db_engine())

    def exists(self) -> bool:
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

    def remove(self) -> None:
        for db in self.databases:
            self.base.metadata.drop_all(db.db_engine())


class Grant(DatabaseSqlEntity):
    pass


class Policy(DatabaseSqlEntity):
    # have this be the thing that can enable RLS?
    pass
