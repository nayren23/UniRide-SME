# content of conftest.py

import pytest
from uniride_sme import app
from uniride_sme.models.bo.user_bo import UserBO


@pytest.fixture(scope="module", autouse=True)
def add_default_user():
    UserBO(
        login="user123",
        firstname="User",
        lastname="Default",
        student_email="defaultuser@gmail.com",
        password="123", #mdp: 123
        gender="H",
        phone_number="612345678",
        description="Yo"
    ).add_in_db("123", "")

@pytest.fixture(scope='session')
def temp_db():
    conn = psycopg2.connect(
        dbname=app.config["DB_NAME"], user=app.config["DB_USER"], password=app.config["DB_PWD"], host=app.config["DB_HOST"], port=app.config["DB_PORT"]
    )

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    temp_db_name = 'test_db_temp'

    with conn.cursor() as cursor:
        cursor.execute(f'CREATE DATABASE {temp_db_name}')

    conn.close()

    temp_conn = psycopg2.connect(
        dbname=temp_db_name, user=app.config["DB_USER"], password=app.config["DB_PWD"], host=app.config["DB_HOST"], port=app.config["DB_PORT"]
    )

    yield temp_conn

    temp_conn.close()
    with conn.cursor() as cursor:
        cursor.execute(f'DROP DATABASE IF EXISTS {temp_db_name}')
