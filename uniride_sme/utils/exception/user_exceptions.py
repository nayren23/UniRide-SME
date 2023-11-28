"""Exceptions for UserBO endpoints"""

from uniride_sme.utils.exception.exceptions import ApiException


class UserNotFoundException(ApiException):
    """Exception for when the user isn't found"""

    def __init__(self):
        super().__init__("USER_NOT_FOUND", 422)


class EmailAlreadyVerifiedException(ApiException):
    """Exception for when the email is already verified"""

    def __init__(self):
        super().__init__("EMAIL_ALREADY_VERIFIED", 403)


class PasswordIncorrectException(ApiException):
    """Exception for when password is incorrect"""

    def __init__(self):
        super().__init__("PASSWORD_INCORRECT", 422)


class AttributeUnchangedException(ApiException):
    """Exception for when the new attribut is the same os the old one"""

    def __init__(self, message):
        super().__init__(message + "_NEW_OLD_SAME", 422)
