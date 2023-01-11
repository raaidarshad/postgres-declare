from sqlalchemy import Engine

from postgres_declare.entities.entity import Entity
from postgres_declare.entities.grant import GrantableEntity


class Base:
    @classmethod
    def create_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        for entity in Entity.entities:
            entity._safe_create()

    @classmethod
    def grant_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        for entity in Entity.entities:
            if isinstance(entity, GrantableEntity):
                entity._safe_grant()

    @classmethod
    def run_all(cls, engine: Engine) -> None:
        Entity._engine = engine
        cls.create_all()
        cls.grant_all()

    @classmethod
    def drop_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        for entity in reversed(Entity.entities):
            entity._safe_drop()

    @classmethod
    def revoke_all(cls, engine: Engine | None = None) -> None:
        if engine:
            Entity._engine = engine
        for entity in reversed(Entity.entities):
            if isinstance(entity, GrantableEntity):
                entity._safe_revoke()
