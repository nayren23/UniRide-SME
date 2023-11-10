# content of conftest.py
import mock
import pytest
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2
from unittest.mock import patch
from uniride_sme import app
from uniride_sme.models.bo.user_bo import UserBO
from uniride_sme.connect_pg import connect
from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,
)

@pytest.fixture(scope='module')
def mock_connect():
    with patch('uniride_sme.connect_pg.connect') as mock:
        yield mock

@pytest.fixture(scope="function")
def connect_mock(mock_connect):
    mock_connect.return_value = psycopg2.connect(
        dbname="uniride_test",
        user=app.config["DB_USER"],
        password=app.config["DB_PWD"],
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"]
    )

def pytest_sessionfinish(session):
    # Supprimez la base de données temporaire une seule fois à la fin de tous les tests
    main_conn = psycopg2.connect(
        dbname="uniride_test",
        user=app.config["DB_USER"],
        password=app.config["DB_PWD"],
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"]
    )

    main_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)


    with main_conn.cursor() as cursor:
        cursor.execute(f"""DO $$ DECLARE
t_name text;
BEGIN
FOR t_name IN (SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()) 
LOOP
    EXECUTE 'TRUNCATE TABLE ' || t_name || ' CASCADE;';
END LOOP;
END $$;""")

    main_conn.close()


@pytest.fixture(scope="function")
def get_default_user(mock_connect):
    user = UserBO(
            login="user123",
            firstname="User",
            lastname="Default",
            student_email="defaultuser@iut.univ-paris8.fr",
            password="111AAaa@", #mdp: 123
            gender="H",
            phone_number="612345678",
            description="Yo"
        )
    try:
        user.add_in_db("111AAaa@", "")
    except InvalidInputException as e:
        user.u_id = 1
    return user
