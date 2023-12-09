"""Exceptions for TripBO endpoints"""

from uniride_sme.utils.exception.exceptions import ApiException


class TripNotFoundException(ApiException):
    """Exception for when the trip isn't found"""

    def __init__(self):
        super().__init__("TRIP_NOT_FOUND", 422)


class TripAlreadyExistsException(ApiException):
    """Exception for when the trip already exists"""

    def __init__(self):
        super().__init__("TRIP_ALREADY_EXISTS", 422)
