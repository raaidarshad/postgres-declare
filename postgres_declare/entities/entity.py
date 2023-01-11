from abc import ABC, abstractmethod
from inspect import signature
from typing import Any, Sequence

from sqlalchemy import Engine

from postgres_declare.exceptions import EntityExistsError, NoEngineError


class Entity(ABC):
    entities: list["Entity"] = []
    check_if_any_exist: bool = False
    _engine: Engine | None = None

    def __init__(
        self,
        name: str,
        depends_on: Sequence["Entity"] | None = None,
        check_if_exists: bool | None = None,
    ):
        # TODO have "name" be a str class that validates via regex for valid postgres names
        self.name = name

        # explicit None check because False requires different behavior
        if check_if_exists is None:
            self.check_if_exists = self.__class__.check_if_any_exist
        else:
            self.check_if_exists = check_if_exists

        if not depends_on:
            depends_on = []
        self.depends_on: Sequence["Entity"] = depends_on

        self.__class__._register(self)

    @classmethod
    def _register(cls, entity: "Entity") -> None:
        cls.entities.append(entity)

    @classmethod
    def engine(cls) -> Engine:
        if cls._engine:
            return cls._engine
        else:
            raise NoEngineError(
                "There is no SQLAlchemy Engine present. `Base._engine` must have "
                "a valid engine. This should be passed via the `_create_all` method."
            )

    @abstractmethod
    def _create(self) -> None:
        pass

    def _safe_create(self) -> None:
        if not self._exists():
            self._create()
        else:
            if self.check_if_exists or self.check_if_any_exist:
                raise EntityExistsError(
                    f"There is already a {self.__class__.__name__} with the "
                    f"name {self.name}. If you want to proceed anyway, set "
                    f"the `check_if_exists` parameter to False. This will "
                    f"simply skip over the existing entity."
                )
            else:
                # TODO log that we no-op?
                pass

    @abstractmethod
    def _exists(self) -> bool:
        pass

    @abstractmethod
    def _drop(self) -> None:
        pass

    def _safe_drop(self) -> None:
        if self._exists():
            self._drop()
        else:
            if self.check_if_exists or self.check_if_any_exist:
                raise EntityExistsError(
                    f"There is no {self.__class__.__name__} with the "
                    f"name {self.name} to remove. If you want to proceed "
                    f"anyway, set the `check_if_exists` parameter to False. "
                    f"This will simply skip over the removal of this "
                    f"entity that does not exist in the cluster."
                )
            else:
                # TODO log that we no-op?
                pass

    def _get_passed_args(self) -> dict[str, Any]:
        # grab all the arguments to __init__ that aren't in the superclass and have a non-None value
        return {
            k: v
            for k, v in vars(self).items()
            if (k not in signature(self.__class__.__bases__[0].__init__).parameters) and (v is not None)  # type: ignore
        }
