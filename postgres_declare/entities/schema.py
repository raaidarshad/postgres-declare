from typing import Sequence

from sqlalchemy import TextClause, text

from postgres_declare.entities.database import Database
from postgres_declare.entities.database_entity import DatabaseSqlEntity
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role


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

    def _create_statements(self) -> Sequence[TextClause]:
        statement = f"CREATE SCHEMA {self.name}"

        if self.owner:
            statement = f"{statement} AUTHORIZATION {self.owner.name}"

        return [text(statement)]

    def _exists_statement(self) -> TextClause:
        return text("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=:schema)").bindparams(schema=self.name)

    def _drop_statements(self) -> Sequence[TextClause]:
        return [text(f"DROP SCHEMA {self.name}")]
