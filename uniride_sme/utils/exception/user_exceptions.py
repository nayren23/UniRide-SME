"""Exceptions for UserBO endpoints"""

from uniride_sme.utils.exception.exceptions import ApiException


class UserNotFoundException(ApiException):
    """Exception for when user not found"""

    def __init__(self):
        super().__init__("USER_NOT_FOUND", 422)
