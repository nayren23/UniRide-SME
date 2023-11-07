# test_user_bo.py

import pytest

from uniride_sme.models.bo.user_bo import UserBO
from uniride_sme.utils.exception.user_exceptions import (
    UserNotFoundException,
    PasswordIncorrectException,
)

@pytest.fixture
def default_user():
    """Returns a User basic informations"""
    return UserBO(
        22,
        "bob123",
        "Bob",
        "Pignon",
        "bobpignon@gmail.com",
        "123", #mdp: 123
        "H",
        "612345678",
        "Salut c'est moi Bob"
    )

def test_get_from_db_user_not_exist(default_user: UserBO):
    with pytest.raises(UserNotFoundException):
        default_user.get_from_db()
