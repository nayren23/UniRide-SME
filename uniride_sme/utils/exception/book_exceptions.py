"""Exceptions for TripBO endpoints"""

from uniride_sme.utils.exception.exceptions import ForbiddenException, InvalidInputException


class TripAlreadyBookedException(ForbiddenException):
    """Exception for when the trip already exists"""

    def __init__(self):
        super().__init__("TRIP_ALREADY_BOOKED")


class BookingNotFoundException(InvalidInputException):
    """Exception for when the trip isn't found"""

    def __init__(self):
        super().__init__("BOOKING_NOT_FOUND")


class BookingAlreadyRespondedException(InvalidInputException):
    """Exception for when the trip isn't found"""

    def __init__(self):
        super().__init__("BOOKING_ALREADY_RESPONDED")
