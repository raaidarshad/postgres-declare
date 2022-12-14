import pytest

from postgres_declare.cluster_entities import Database
from postgres_declare.database_entities import DatabaseContent, Schema


def test_does_not_exist(simple_db_content: DatabaseContent, simple_db: Database) -> None:
    # need the database to exist for this and the next two tests
    simple_db.safe_create()
    assert not simple_db_content.exists()


@pytest.mark.order(after="test_does_not_exist")
def test_create(simple_db_content: DatabaseContent, simple_schema: Schema) -> None:
    # need the schema to exist for this and the next test
    simple_schema.safe_create()
    simple_db_content.safe_create()
    assert simple_db_content.exists()


@pytest.mark.order(after="test_create")
def test_remove(simple_db_content: DatabaseContent, simple_db: Database) -> None:
    simple_db_content.safe_remove()
    assert not simple_db_content.exists()
    # clean up database
    simple_db.safe_remove()
