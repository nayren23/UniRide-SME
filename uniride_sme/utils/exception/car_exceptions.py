"""Exceptions for CarBO endpoints"""
from uniride_sme.utils.exception.exceptions import ApiException

class CarAlreadyExist(ApiException):
    """Exception for when an invalid intermediate car is encountered"""

    def __init__(self):
        super().__init__("CAR_ALREADY_EXIST", 422)
