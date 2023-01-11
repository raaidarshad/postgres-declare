from typing import Sequence

from sqlalchemy import Engine, TextClause, create_engine, text

from postgres_declare.entities.cluster_entity import ClusterEntity
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role


class Database(ClusterEntity):
    def __init__(
        self,
        name: str,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
        owner: Role | None = None,
        template: str | None = None,
        # encoding: str | None = None,
        # strategy: str | None = None,
        # locale: str | None = None,
        # lc_collate: str | None = None,
        # lc_ctype: str | None = None,
        # icu_locale: str | None = None,
        # locale_provider: str | None = None,
        # collation_version: str | None = None,
        # tablespace: str | None = None,
        allow_connections: bool | None = None,
        connection_limit: int | None = None,
        is_template: bool | None = None,
        # oid: str | None = None,
    ):
        self.owner = owner
        self.template = template
        # self.encoding = encoding
        # self.strategy = strategy
        # self.locale = locale
        # self.lc_collate = lc_collate
        # self.lc_ctype = lc_ctype
        # self.icu_locale = icu_locale
        # self.locale_provider = locale_provider
        # self.collation_version = collation_version
        # self.tablespace = tablespace
        self.allow_connections = allow_connections
        self.connection_limit = connection_limit
        self.is_template = is_template
        # self.oid = oid

        self._db_engine: Engine | None = None

        super().__init__(name=name, depends_on=depends_on, check_if_exists=check_if_exists)

    def _create_statements(self) -> Sequence[TextClause]:
        statement = f"CREATE DATABASE {self.name}"

        props = self._get_passed_args()

        # append the arguments to the sql statement
        for k, v in props.items():
            # case owner and type Role, use role.name
            match k, v:
                case "owner", v:
                    statement = f"{statement} OWNER={v.name}"
                case "grants", _:
                    pass
                case k, v:
                    statement = f"{statement} {k.upper()}={v}"

        return [text(statement)]

    def _exists_statement(self) -> TextClause:
        return text("SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname=:db)").bindparams(db=self.name)

    def _drop_statements(self) -> Sequence[TextClause]:
        statements = []
        if self.is_template:
            # cannot drop a template, must set is_template to false before drop
            statements.append(text(f"ALTER DATABASE {self.name} is_template false"))
        statements.append(text(f"DROP DATABASE {self.name} (FORCE)"))
        return statements

    def db_engine(self) -> Engine:
        # database entities will reference this as the engine to use
        if not self._db_engine:
            # grab everything but db name from the cluster engine
            host = self.__class__.engine().url.host
            port = self.__class__.engine().url.port
            user = self.__class__.engine().url.username
            pw = self.__class__.engine().url.password

            # then create a new engine
            self._db_engine = create_engine(f"postgresql+psycopg://{user}:{pw}@{host}:{port}/{self.name}")
        return self._db_engine
