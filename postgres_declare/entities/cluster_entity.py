from postgres_declare.entities.entity import Entity
from postgres_declare.sqlmixin import SQLMixin


class ClusterEntity(SQLMixin, Entity):
    def _create(self) -> None:
        self._commit_sql(engine=self.__class__.engine(), statements=self._create_statements())

    def _exists(self) -> bool:
        rows = self._fetch_sql(engine=self.__class__.engine(), statement=self._exists_statement())
        return rows[0][0]  # type: ignore

    def _drop(self) -> None:
        self._commit_sql(engine=self.__class__.engine(), statements=self._drop_statements())
