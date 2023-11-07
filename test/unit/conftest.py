# content of conftest.py

import pytest
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