from typing import Sequence

import pytest
from sqlalchemy import Engine

from postgres_declare.base import Base
from postgres_declare.entities.entity import Entity
from postgres_declare.entities.grant import Grant, GrantableEntity, Privilege
from postgres_declare.entities.role import Role
from postgres_declare.exceptions import EntityExistsError
from tests.helpers import YieldFixture


class MockGrantable(GrantableEntity):
    def __init__(
        self,
        name: str,
        depends_on: Sequence[Entity] | None = None,
        check_if_exists: bool | None = None,
        mock_exists: bool = True,
    ):
        # manually calling __init__ for both, only other case that works is no __init__ here
        # but we want to make sure all the kwargs show up correctly in IDE hints
        Entity.__init__(self, name=name, depends_on=depends_on, check_if_exists=check_if_exists)
        GrantableEntity.__init__(self, name=name)
        self.mock_exists = mock_exists

    def _create(self) -> None:
        self.engine()

    def _exists(self) -> bool:
        self.engine()
        return self.mock_exists

    def _grant(self) -> None:
        self.engine()

    def _revoke(self) -> None:
        self.engine()

    def _drop(self) -> None:
        self.engine()


class MockRole(Role):
    def __init__(self, name: str, mock_exists: bool = True):
        super().__init__(name=name)
        self.mock_exists = mock_exists

    def _exists(self) -> bool:
        return self.mock_exists


# TODO these mocks need to be a bit more sensible and have grants for some
# of them! should add a test to check for that too


@pytest.fixture
def grantable_entity() -> YieldFixture[MockGrantable]:
    yield MockGrantable(name="mock_grantable_single")
    Entity.entities = []
    Entity.check_if_any_exist = False
    Entity._engine = None


@pytest.fixture
def mock_role() -> YieldFixture[MockRole]:
    yield MockRole(name="mock_role", mock_exists=True)


@pytest.fixture
def mock_role_does_not_exist() -> YieldFixture[MockRole]:
    yield MockRole(name="nothere", mock_exists=False)


@pytest.fixture
def grantable_entity_does_not_exist(mock_role: MockRole) -> YieldFixture[MockGrantable]:
    mg = MockGrantable(name="mock_grantable_does_not_exist", mock_exists=False)
    mg.grant(grants=[Grant(privileges=[Privilege.SELECT], grantees=[mock_role])])
    yield mg
    Entity.entities = []
    Entity.check_if_any_exist = False
    Entity._engine = None


@pytest.fixture
def simple_grant(mock_role: MockRole) -> YieldFixture[Grant]:
    yield Grant(privileges=[Privilege.SELECT, Privilege.INSERT], grantees=[mock_role])


@pytest.fixture
def grantable_with_grant(grantable_entity: MockGrantable, simple_grant: Grant) -> YieldFixture[MockGrantable]:
    grantable_entity.grant([simple_grant])
    yield grantable_entity


@pytest.fixture
def grantable_with_grant_to_nonexistent_grantees(
    grantable_entity: MockGrantable, mock_role_does_not_exist: MockRole
) -> YieldFixture[MockGrantable]:
    grant_with_nonexistent_grantees = Grant(privileges=[Privilege.SELECT], grantees=[mock_role_does_not_exist])
    grantable_entity.grant([grant_with_nonexistent_grantees])
    yield grantable_entity


def test_grant(grantable_entity: MockGrantable, simple_grant: Grant) -> None:
    grantable_entity.grant([simple_grant])
    assert grantable_entity.grants[0] == simple_grant


def test_grant_all(grantable_with_grant: MockGrantable, engine: Engine) -> None:
    Base.grant_all(engine)


def test_grant_all_error_if_self_does_not_exist(grantable_entity_does_not_exist: MockGrantable, engine: Engine) -> None:
    with pytest.raises(EntityExistsError):
        Base.grant_all(engine)


def test_grant_all_error_if_grantees_do_not_exist(
    grantable_with_grant_to_nonexistent_grantees: MockGrantable, engine: Engine
) -> None:
    with pytest.raises(EntityExistsError):
        Base.grant_all(engine)


def test_revoke_all(grantable_with_grant: MockGrantable, engine: Engine) -> None:
    Base.revoke_all(engine)


def test_revoke_error_if_self_does_not_exist(grantable_entity_does_not_exist: MockGrantable, engine: Engine) -> None:
    with pytest.raises(EntityExistsError):
        Base.revoke_all(engine)


def test_revoke_error_if_grantees_do_not_exist(
    grantable_with_grant_to_nonexistent_grantees: MockGrantable, engine: Engine
) -> None:
    with pytest.raises(EntityExistsError):
        Base.revoke_all(engine)
