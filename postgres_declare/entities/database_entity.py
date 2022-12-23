from typing import Sequence

from postgres_declare.entities.base_entity import Entity
from postgres_declare.entities.database import Database
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
    # TODO maybe inherit from grantable, maybe do it per entity?
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