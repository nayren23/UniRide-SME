# test_user_bo.py

import pytest

from uniride_sme import connect_pg
from uniride_sme.models.bo.user_bo import UserBO
from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,
    MissingInputException,
)
from uniride_sme.utils.exception.user_exceptions import (
    UserNotFoundException,
)

@pytest.fixture(scope="function")
def get_user(mock_connect):
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

def test_get_from_db_user_not_found_with_default_user():
    with pytest.raises(UserNotFoundException):
        UserBO(
            login="bob123",
            firstname="Bob",
            lastname="Pignon",
            student_email="bobpignon@iut.univ-paris8.fr",
            password="123",
            gender="H",
            phone_number="612345678",
            description="Salut c'est moi Bob"
        ).get_from_db()

def test_get_from_db_with_default_user(get_default_user: UserBO):
    assert get_default_user.u_id == 1
    assert get_default_user.u_login == 'user123'
    assert get_default_user.u_student_email == 'defaultuser@iut.univ-paris8.fr'

def test_get_from_db_missing_input_with_default_user(get_default_user: UserBO):
    get_default_user.u_id = None
    get_default_user.u_login = None

    with pytest.raises(MissingInputException):
        get_default_user.get_from_db()

def test_validate_login_missing_input(get_default_user):
    user = get_default_user
    user.u_login = None
    with pytest.raises(MissingInputException) as exc_info:
        user._validate_login()

    assert str(exc_info.value) == "LOGIN_MISSING"

def test_validate_login_too_long(get_default_user):
    user = get_default_user
    user.u_login = "a" * 51

    with pytest.raises(InvalidInputException) as exc_info:
        user._validate_login()

    assert str(exc_info.value) == "LOGIN_TOO_LONG"

def test_validate_login_taken(get_default_user, get_user):
    user = get_default_user
    second_user = get_user

    with pytest.raises(InvalidInputException) as exc_info:
        second_user._validate_login()

    assert str(exc_info.value) == "LOGIN_TAKEN"

def test_validate_login_invalid_characters(get_default_user):
    user = get_default_user
    user.u_login = "user@name"

    with pytest.raises(InvalidInputException) as exc_info:
        user._validate_login()

    assert str(exc_info.value) == "LOGIN_INVALID_CHARACTERS"

def test_validate_student_email_missing_input(get_default_user):
    user = get_default_user
    user.u_student_email = None

    with pytest.raises(MissingInputException) as exc_info:
        user._validate_student_email()

    assert str(exc_info.value) == "EMAIL_MISSING"

def test_validate_student_email_invalid_format(get_default_user):
    user = get_default_user
    user.u_student_email = "invalid_email"

    with pytest.raises(InvalidInputException) as exc_info:
        user._validate_student_email()

    # Vérifier le message d'exception
    assert str(exc_info.value) == "EMAIL_INVALID_FORMAT"


def test_validate_student_email_too_long(get_default_user):
    user = get_default_user
    user.u_student_email = "a" * 255 + "@example.com"

    with pytest.raises(InvalidInputException) as exc_info:
        user._validate_student_email()

    assert str(exc_info.value) == "EMAIL_TOO_LONG"


def test_validate_firstname_missing_input(get_default_user):
    user = get_default_user

    with pytest.raises(MissingInputException) as exc_info:
        user._validate_name(None, "FIRSTNAME")

    assert str(exc_info.value) == "FIRSTNAME_MISSING"

def test_validate_firstname_too_long(get_default_user):
    user = get_default_user

    with pytest.raises(InvalidInputException) as exc_info:
        user._validate_name("A" * 51, "FIRSTNAME")

    assert str(exc_info.value) == "FIRSTNAME_TOO_LONG"

def test_validate_firstname_invalid_characters(get_default_user):
    user = get_default_user

    with pytest.raises(InvalidInputException) as exc_info:
        user._validate_name("User123", "FIRSTNAME")

    assert str(exc_info.value) == "FIRSTNAME_INVALID_CHARACTERS"

def test_validate_lastname_missing_input(get_default_user):
    user = get_default_user

    with pytest.raises(MissingInputException) as exc_info:
        user._validate_name(None, "LASTNAME")

    assert str(exc_info.value) == "LASTNAME_MISSING"

def test_validate_gender_missing_input(get_default_user):
    user = get_default_user
    user.u_gender = ""

    with pytest.raises(MissingInputException) as exc_info:
        user._validate_gender()

    assert str(exc_info.value) == "GENDER_MISSING"

def test_validate_gender_invalid(get_default_user):
    user = get_default_user

    user.u_gender = "Invalid"
    with pytest.raises(InvalidInputException) as exc_info:
        user._validate_gender()

    assert str(exc_info.value) == "GENDER_INVALID"

def test_validate_gender_valid(get_default_user):
    user = get_default_user

    user.u_gender = "N"
    user._validate_gender()

    user.u_gender = "F"
    user._validate_gender()

    user.u_gender = "H"
    user._validate_gender()

def test_validate_phone_number_valid(get_default_user):
    user = get_default_user

    user.u_phone_number = "123456789"
    user._validate_phone_number()

def test_validate_phone_number_invalid(get_default_user):
    user = get_default_user

    user.u_phone_number = "invalid"
    with pytest.raises(InvalidInputException) as exc_info:
        user._validate_phone_number()

    assert str(exc_info.value) == "PHONE_NUMBER_INVALID"

def test_validate_phone_number_empty(get_default_user):
    user = get_default_user

    user.u_phone_number = ""
    user._validate_phone_number()

def test_validate_phone_number_none(get_default_user):
    user = get_default_user

    user.u_phone_number = None
    user._validate_phone_number()

def test_validate_description_valid(get_default_user):
    # Vous pouvez utiliser la fixture comme un paramètre de test
    user = get_default_user

    # Appeler la méthode avec une description valide (moins de 500 caractères) et vérifier qu'aucune exception n'est levée
    user.u_description = "This is a valid description."
    user._validate_description()

def test_validate_description_too_long(get_default_user):
    # Vous pouvez utiliser la fixture comme un paramètre de test
    user = get_default_user

    # Appeler la méthode avec une description trop longue et attendre une InvalidInputException
    user.u_description = "A" * 501
    with pytest.raises(InvalidInputException) as exc_info:
        user._validate_description()

    # Vérifier le message d'exception
    assert str(exc_info.value) == "DESCRIPTION_TOO_LONG"

def test_validate_description_empty(get_default_user):
    # Vous pouvez utiliser la fixture comme un paramètre de test
    user = get_default_user

    # Appeler la méthode avec une description vide et vérifier qu'aucune exception n'est levée
    user.u_description = ""
    user._validate_description()

def test_validate_description_none(get_default_user):
    # Vous pouvez utiliser la fixture comme un paramètre de test
    user = get_default_user

    # Appeler la méthode avec une description à None et vérifier qu'aucune exception n'est levée
    user.u_description = None
    user._validate_description()

def test_validate_password_valid(get_default_user):
    # Vous pouvez utiliser la fixture comme un paramètre de test
    user = get_default_user

    # Appeler la méthode avec un mot de passe valide et vérifier qu'aucune exception n'est levée
    password_confirmation = "111AAaa@"
    user._validate_password(password_confirmation)

def test_validate_password_missing_input(get_default_user):
    # Vous pouvez utiliser la fixture comme un paramètre de test
    user = get_default_user

    # Appeler la méthode avec un mot de passe manquant et attendre une MissingInputException
    password_confirmation = "111AAaa@"
    user.u_password = None
    with pytest.raises(MissingInputException) as exc_info:
        user._validate_password(password_confirmation)

    # Vérifier le message d'exception
    assert str(exc_info.value) == "PASSWORD_MISSING"

def test_validate_password_confirmation_missing_input(get_default_user):
    user = get_default_user
    password_confirmation = None
    with pytest.raises(MissingInputException) as exc_info:
        user._validate_password(password_confirmation)

    assert str(exc_info.value) == "PASSWORD_CONFIRMATION_MISSING"

def test_validate_password_invalid(get_default_user):
    user = get_default_user

    password_confirmation = "invalid_password"
    user.u_password = "invalid_password"
    with pytest.raises(InvalidInputException) as exc_info:
        user._validate_password(password_confirmation)

    assert str(exc_info.value) == "PASSWORD_INVALID"

def test_validate_password_not_matching(get_default_user):
    user = get_default_user

    password_confirmation = "mismatched_password"
    with pytest.raises(InvalidInputException) as exc_info:
        user._validate_password(password_confirmation)

    assert str(exc_info.value) == "PASSWORD_NOT_MATCHING"

def test_verify_student_email_missing_input(get_default_user):
    user = get_default_user

    user.u_student_email = None
    with pytest.raises(MissingInputException) as exc_info:
        user.verify_student_email()

    assert str(exc_info.value) == "EMAIL_MISSING"


def test_verify_student_email_not_owned(get_default_user, monkeypatch):
    user = get_default_user
    def mock_get_query_not_owned(conn, query, params):
        return []

    monkeypatch.setattr(connect_pg, 'get_query', mock_get_query_not_owned)

    with pytest.raises(InvalidInputException) as exc_info:
        user.verify_student_email()

    assert str(exc_info.value) == "EMAIL_NOT_OWNED"

def test_verify_student_email_already_verified(get_default_user, monkeypatch):
    user = get_default_user

    def mock_get_query_already_verified(conn, query, params):
        return [(True,)]

    monkeypatch.setattr(connect_pg, 'get_query', mock_get_query_already_verified)

    with pytest.raises(InvalidInputException) as exc_info:
        user.verify_student_email()

    assert str(exc_info.value) == "EMAIL_ALREADY_VERIFIED"

# def test_authenticate_success(get_default_user):
#     user = get_default_user

#     user.authentificate()

def test_authenticate_missing_login(get_default_user):
    user = get_default_user
    user.u_login = None

    with pytest.raises(MissingInputException) as exc_info:
        user.authentificate()

    assert str(exc_info.value) == "LOGIN_MISSING"

def test_authenticate_missing_password(get_default_user):
    user = get_default_user
    user.u_password = None

    with pytest.raises(MissingInputException) as exc_info:
        user.authentificate()

    assert str(exc_info.value) == "PASSWORD_MISSING"


