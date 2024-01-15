"""test_user_service.py"""
from datetime import datetime
from unittest.mock import MagicMock
import pytest

from uniride_sme.service.user_service import authenticate, _validate_login, _validate_student_email
from uniride_sme.utils.exception.exceptions import MissingInputException, InvalidInputException
from uniride_sme.model.bo.user_bo import UserBO


def test_authenticate_missing_login():
    """Test authenticate when login is missing"""
    with pytest.raises(MissingInputException):
        authenticate(None, "password")


def test_authenticate_missing_password():
    """Test authenticate when password is missing"""
    with pytest.raises(MissingInputException):
        authenticate("login", None)


@pytest.fixture
def mock_get_user_by_login(monkeypatch):
    """Mock get_user_by_login"""
    mock = MagicMock()
    monkeypatch.setattr("uniride_sme.service.user_service.get_user_by_login", mock)
    return mock


@pytest.fixture
def mock_verify_password(monkeypatch):
    """Mock verify_password"""
    mock = MagicMock()
    monkeypatch.setattr("uniride_sme.service.user_service._verify_password", mock)
    return mock


@pytest.mark.parametrize("login, password", [("user1", "pass1"), ("user2", "pass2")])
def test_authenticate_success(mock_get_user_by_login, mock_verify_password, login, password):
    """Test authenticate is working correctly"""
    mock_get_user_by_login.return_value = UserBO(
        1,
        "user1",
        "u",
        "s",
        "user@gmail.com",
        "f",
        "M",
        "0612345678",
        "",
        "",
        datetime.now(),
        datetime.now(),
        "yes",
        "",
        "",
        "",
    )
    mock_verify_password.return_value = True

    user = authenticate(login, password)

    # Vérifiez que les mocks ont été appelés
    mock_get_user_by_login.assert_called_once_with(login)
    mock_verify_password.assert_called_once_with(password, user.password)
    assert user is not None


def test_add_user_valid_data():
    # Testez add_user avec des données valides
    pass


def test_validate_login_invalid(mock_get_query):
    """Test validate_login when login is invalid"""
    mock_get_query.return_value = [[1]]
    with pytest.raises(InvalidInputException):
        _validate_login("takenlogin")


def test_validate_student_email_missing():
    """Test validate_student_email when student_email is missing"""
    with pytest.raises(MissingInputException) as excinfo:
        _validate_student_email(None)
    assert "EMAIL_MISSING" in str(excinfo.value)


def test_validate_student_email_invalid_format():
    """Test validate_student_email when email format is invalide"""
    invalid_emails = ["invalidemail", "invalid@university", "invalid@university.c"]
    for email in invalid_emails:
        with pytest.raises(InvalidInputException) as excinfo:
            _validate_student_email(email)
        assert "EMAIL_INVALID_FORMAT" in str(excinfo.value)


def test_validate_student_email_too_long():
    """Test validate_student_email when email is too long"""
    email = "a" * 245 + "@domain.com"
    with pytest.raises(InvalidInputException) as excinfo:
        _validate_student_email(email)
    assert "EMAIL_TOO_LONG" in str(excinfo.value)


def test_validate_student_email_invalid_domain():
    """Test validate_student_email when email domain doesn't correspond
    to 'university.com' (the university domain defined for tests)"""
    email = "validemail@invalid.com"
    with pytest.raises(InvalidInputException) as excinfo:
        _validate_student_email(email)
    assert "EMAIL_INVALID_DOMAIN" in str(excinfo.value)


def test_validate_student_email_already_taken(mock_get_query):
    """Test validate_student_email when email is already used"""
    mock_get_query.return_value = [[1]]  # Simulate that the email is already taken
    email = "takenemail@university.com"
    with pytest.raises(InvalidInputException) as excinfo:
        _validate_student_email(email)
    assert "EMAIL_TAKEN" in str(excinfo.value)
