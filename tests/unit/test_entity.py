from typing import Any, Sequence

import pytest
from sqlalchemy import Engine

from postgres_declare.base import Base
from postgres_declare.entities.entity import Entity
from postgres_declare.exceptions import EntityExistsError, NoEngineError
from tests.helpers import YieldFixture

########################
# FIXTURES AND CLASSES #
########################


class MockEntity(Entity):
    def __init__(
        self,
        name: str,
        depends_on: Sequence["Entity"] | None = None,
        check_if_exists: bool | None = None,
        mock_exists: bool = True,
        mock_kwarg_1: str | None = None,
        mock_kwarg_2: str | None = None,
    ):
        self.mock_exists = mock_exists
        self.mock_kwarg_1 = mock_kwarg_1
        self.mock_kwarg_2 = mock_kwarg_2
        super().__init__(name=name, depends_on=depends_on, check_if_exists=check_if_exists)

    def _create(self) -> None:
        self.engine()

    def _exists(self) -> bool:
        self.engine()
        return self.mock_exists

    def _drop(self) -> None:
        self.engine()


class ChildMockEntity(MockEntity):
    def __init__(self, mock_kwarg_3: str | None = None, mock_kwarg_4: str | None = None, *args: Any, **kwargs: Any):
        self.mock_kwarg_3 = mock_kwarg_3
        self.mock_kwarg_4 = mock_kwarg_4
        super().__init__(*args, **kwargs)


@pytest.fixture
def mock_entity_exists() -> YieldFixture[MockEntity]:
    yield MockEntity("mock_exists")
    Entity.entities = []
    Entity.check_if_any_exist = False
    Entity._engine = None


@pytest.fixture
def mock_entity_does_not_exist() -> YieldFixture[MockEntity]:
    yield MockEntity("mock_does_not_exist", mock_exists=False)
    Entity.entities = []
    Entity.check_if_any_exist = False
    Entity._engine = None


#########
# TESTS #
#########


def test_entity_register(mock_entity_exists: MockEntity) -> None:
    assert mock_entity_exists in Entity.entities


def test_entity_register_order(mock_entity_exists: MockEntity) -> None:
    another_mock = MockEntity("another_one", depends_on=[mock_entity_exists])

    assert Entity.entities[0] == mock_entity_exists
    assert Entity.entities[1] == another_mock


def test_entity_no_engine(mock_entity_exists: MockEntity) -> None:
    with pytest.raises(NoEngineError):
        mock_entity_exists._create()
    with pytest.raises(NoEngineError):
        mock_entity_exists._exists()


def test_entity_get_passed_args() -> None:
    kwargs = dict(name="test", mock_exists=True, mock_kwarg_1="foo", mock_kwarg_2="bar")
    new_mock = MockEntity(**kwargs)  # type: ignore
    check_kwargs = new_mock._get_passed_args()
    # remove "name" before check because it isn't a child class argument, so it shouldn't be in the fn output
    kwargs.pop("name")
    assert kwargs == check_kwargs


def test_entity_get_passed_args_inherited() -> None:
    kwargs = dict(name="merp", mock_kwarg_3="derp", mock_kwarg_4="flerp")
    new_mock = ChildMockEntity(**kwargs)
    check_kwargs = new_mock._get_passed_args()
    # remove "name" before check because it isn't a child class argument, so it shouldn't be in the fn output
    kwargs.pop("name")
    assert kwargs == check_kwargs


def test_entity_does_not_exist(mock_entity_does_not_exist: MockEntity, engine: Engine) -> None:
    Entity._engine = engine
    assert not mock_entity_does_not_exist._exists()


def test_entity_create_if_not_exist(mock_entity_exists: MockEntity, engine: Engine) -> None:
    Base.create_all(engine)
    assert mock_entity_exists._exists()


def test_entity_create_if_not_check_if_exists(mock_entity_exists: MockEntity, engine: Engine) -> None:
    Base.create_all(engine)  # should simply no op, nothing to assert really


def test_entity_create_if_check_if_exists(mock_entity_exists: MockEntity, engine: Engine) -> None:
    mock_entity_exists.check_if_exists = True
    with pytest.raises(EntityExistsError):
        Base.create_all(engine)


def test_entity_create_if_error_if_any_exist(mock_entity_exists: MockEntity, engine: Engine) -> None:
    Entity.check_if_any_exist = True
    with pytest.raises(EntityExistsError):
        Base.create_all(engine)


def test_entity_drop_if_exists(mock_entity_exists: MockEntity, engine: Engine) -> None:
    Base.drop_all(engine)  # should simply no op, nothing to assert really


def test_entity_drop_error_if_does_not_exist(mock_entity_does_not_exist: MockEntity, engine: Engine) -> None:
    mock_entity_does_not_exist.check_if_exists = True
    with pytest.raises(EntityExistsError):
        Base.drop_all(engine)


def test_entity_drop_error_if_any_does_not_exist(mock_entity_does_not_exist: MockEntity, engine: Engine) -> None:
    Entity.check_if_any_exist = True
    with pytest.raises(EntityExistsError):
        Base.drop_all(engine)
