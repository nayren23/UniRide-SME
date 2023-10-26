"""Exceptions for UserBO endpoints"""

from models.exception.exceptions import ApiException


class InvalidInputException(ApiException):
    def __init__(self, message):
        super().__init__(message, 422)


class MissingInputException(ApiException):
    def __init__(self, message):
        super().__init__(message, 400)
