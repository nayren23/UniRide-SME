# content of conftest.py
import json
from unittest.mock import patch

import mock
import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

import uniride_sme
from uniride_sme import app
from uniride_sme.api import user_api
from uniride_sme.config import TestingConfig
from uniride_sme.connect_pg import connect
from uniride_sme.models.bo.user_bo import UserBO
from uniride_sme.utils.exception.exceptions import InvalidInputException


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    # Setup testing config
    app.config.from_object(TestingConfig)

    # Register blueprints here
    app.register_blueprint(user_api.user)


def pytest_sessionfinish(session):
    """Connect to the testing database and delete data added during tests"""

    # Connect to the testing database
    main_conn = psycopg2.connect(dbname=app.config["DB_NAME"], user=app.config["DB_USER"], password=app.config["DB_PWD"], host=app.config["DB_HOST"], port=app.config["DB_PORT"])

    main_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    # Delete all contents from tables in the testing database
    with main_conn.cursor() as cursor:
        cursor.execute(f"set search_path to uniride;")
        cursor.execute(
            f"""DO $$ DECLARE
t_name text;
BEGIN
FOR t_name IN (SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()) 
LOOP
    EXECUTE 'TRUNCATE TABLE ' || t_name || ' RESTART IDENTITY CASCADE;';
END LOOP;
END $$;"""
        )

    main_conn.close()


# Do rollback for each test
@pytest.fixture(scope="function", autouse=True)
def db_transaction(connect_mock):
    cursor = connect_mock.cursor()
    cursor.execute("BEGIN;")

    yield

    cursor.execute("ROLLBACK;")
    cursor.close()


# Create a test Flask app for testing
@pytest.fixture(scope="module")
def test_app():
    return app


# Mock connect function from connect_pg.py
@pytest.fixture(scope="module")
def mock_connect():
    """Override 'connect' from connect_pg.py for testing"""
    with patch("uniride_sme.connect_pg.connect") as mock:
        yield mock


# Connect the testing db
@pytest.fixture(scope="module", autouse=True)
def connect_mock(mock_connect):
    """Connect to the testing database"""
    db_connection = psycopg2.connect(dbname=app.config["DB_NAME"], user=app.config["DB_USER"], password=app.config["DB_PWD"], host=app.config["DB_HOST"], port=app.config["DB_PORT"])
    mock_connect.return_value = db_connection
    return db_connection


@pytest.fixture(scope="module", autouse=True)
def add_default_user(connect_mock):
    # Create default user for testing
    try:
        user = UserBO(
            login="user123",
            firstname="User",
            lastname="Default",
            student_email="defaultuser@iut.univ-paris8.fr",
            password="111AAaa@",
            gender="H",
            phone_number="612345678",
            description="Yo",  # mdp: 123
        ).add_in_db("111AAaa@", "")
    except InvalidInputException as e:
        pass


# Return the testing_client, use it to test your APIs
@pytest.fixture(scope="module")
def test_client(connect_mock):
    return uniride_sme.app.test_client()


@pytest.fixture(scope="function")
def get_default_user(connect_mock, add_default_user):
    """
    Return the default user
    """
    # It is the same user that was generated in pytest_configure
    user = UserBO(
        user_id=1,
        login="user123",
        firstname="User",
        lastname="Default",
        student_email="defaultuser@iut.univ-paris8.fr",
        password="111AAaa@",
        gender="H",
        phone_number="612345678",
        description="Yo",  # mdp: 123
    )
    user.get_from_db()
    return user


@pytest.fixture(scope="module")
def get_token(test_client):
    data = {"login": "user123", "password": "111AAaa@"}

    # Make a POST request to the authentication endpoint
    response = test_client.post("/user/auth", json=data)

    token = json.loads(response.data).get("token")
    return token
