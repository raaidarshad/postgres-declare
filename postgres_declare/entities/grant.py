from abc import abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from itertools import chain
from typing import Sequence

from sqlalchemy import TextClause, text

from postgres_declare.entities.entity import Entity
from postgres_declare.entities.role import Role
from postgres_declare.exceptions import EntityExistsError


class Privilege(StrEnum):
    ALL_PRIVILEGES = "ALL PRIVILEGES"
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    TRUNCATE = "TRUNCATE"
    REFERENCES = "REFERENCES"
    TRIGGER = "TRIGGER"
    USAGE = "USAGE"
    CREATE = "CREATE"
    CONNECT = "CONNECT"
    TEMPORARY = "TEMPORARY"
    EXECUTE = "EXECUTE"
    ALTER_SYSTEM = "ALTER SYSTEM"


@dataclass
class Grant:
    privileges: Sequence[Privilege]
    grantees: Sequence[Role]


class GrantableEntity(Entity):
    def __init__(self, name: str, depends_on: Sequence[Entity] | None = None, check_if_exists: bool | None = None):
        super().__init__(name=name, depends_on=depends_on, check_if_exists=check_if_exists)
        self.grants: list[Grant] = []

    def grant(self, grants: Sequence[Grant]) -> None:
        self.grants.extend(grants)
        # ensure entity order is correct
        this_index = self.entities.index(self)
        for grant in grants:
            for grantee in grant.grantees:
                grantee_index = self.entities.index(grantee)
                if grantee_index > this_index:
                    self.entities.insert(this_index, self.entities.pop(grantee_index))

    @abstractmethod
    def _grant(self) -> None:
        pass

    def _safe_grant(self) -> None:
        if self.grants:
            grantees_and_existence = chain.from_iterable(
                [[(grantee, grantee._exists()) for grantee in grant.grantees] for grant in self.grants]
            )
            try:
                _, grantees_exist = zip(*grantees_and_existence)
            except ValueError:
                grantees_exist = ()
            if self._exists() and all(grantees_exist):
                self._grant()
            elif not self._exists():
                raise EntityExistsError(
                    f"There is no {self.__class__.__name__} with the "
                    f"name {self.name} to grant privileges to. The "
                    f"entity must exist before granting privileges."
                )
            elif not all(grantees_exist):
                # loop over every grantee that doesn't exist
                missing_grantees = [grantee.name for (grantee, existence) in grantees_and_existence if not existence]
                formatted_missing_grantees = ", ".join(missing_grantees)
                raise EntityExistsError(
                    f"There are no {Role.__class__.__name__}s with the "
                    f"following names: {formatted_missing_grantees}. "
                    f"These must exist before granting privileges."
                )

    def _grant_statements(self) -> Sequence[TextClause]:
        # TODO check privileges for the type, or just let postgres handle the error?
        return [
            text(
                f"GRANT {self._format_privileges(grant)} ON {self.__class__.__name__.upper()} {self.name} TO {self._format_grantees(grant)}"
            )
            for grant in self.grants
        ]

    @abstractmethod
    def _revoke(self) -> None:
        pass

    def _safe_revoke(self) -> None:
        if self.grants:
            grantees_and_existence = chain.from_iterable(
                [[(grantee, grantee._exists()) for grantee in grant.grantees] for grant in self.grants]
            )
            try:
                _, grantees_exist = zip(*grantees_and_existence)
            except ValueError:
                grantees_exist = ()
            if self._exists() and all(grantees_exist):
                self._revoke()
            elif not self._exists():
                raise EntityExistsError(
                    f"There is no {self.__class__.__name__} with the "
                    f"name {self.name} to revoke privileges from. The "
                    f"entity must exist before revoking privileges."
                )
            elif not all(grantees_exist):
                # loop over every grantee that doesn't exist
                missing_grantees = [grantee.name for (grantee, existence) in grantees_and_existence if not existence]
                formatted_missing_grantees = ", ".join(missing_grantees)
                raise EntityExistsError(
                    f"There are no {Role.__class__.__name__}s with the "
                    f"following names: {formatted_missing_grantees}. "
                    f"These must exist before revoking privileges."
                )

    def _revoke_statements(self) -> Sequence[TextClause]:
        return [
            text(
                f"REVOKE {self._format_privileges(grant)} ON {self.__class__.__name__.upper()} {self.name} FROM {self._format_grantees(grant)}"
            )
            for grant in self.grants
        ]

    @staticmethod
    def _format_privileges(grant: Grant) -> str:
        return ", ".join([p for p in grant.privileges])

    @staticmethod
    def _format_grantees(grant: Grant) -> str:
        return ", ".join([r.name for r in grant.grantees])
