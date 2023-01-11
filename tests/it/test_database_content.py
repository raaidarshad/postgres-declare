import pytest

from postgres_declare.entities.database import Database
from postgres_declare.entities.database_content import DatabaseContent
from postgres_declare.entities.schema import Schema


def test_does_not_exist(simple_db_content: DatabaseContent, simple_db: Database) -> None:
    # need the database to exist for this and the next two tests
    simple_db._safe_create()
    assert not simple_db_content._exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(simple_db_content: DatabaseContent, simple_schema: Schema) -> None:
    # need the schema to exist for this and the next test
    simple_schema._safe_create()
    simple_db_content._safe_create()
    assert simple_db_content._exists()


@pytest.mark.order(after="test_create")
def test_drop(simple_db_content: DatabaseContent, simple_db: Database) -> None:
    simple_db_content._safe_drop()
    assert not simple_db_content._exists()
    # clean up database
    simple_db._safe_drop()
