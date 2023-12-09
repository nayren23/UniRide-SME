"""Exceptions for TripBO endpoints"""

from uniride_sme.utils.exception.exceptions import ApiException


class TripAlreadyBookedException(ApiException):
    """Exception for when the trip already exists"""

    def __init__(self):
        super().__init__("TRIP_ALREADY_BOOKED", 403)


class BookingNotFoundException(ApiException):
    """Exception for when the trip isn't found"""

    def __init__(self):
        super().__init__("BOOKING_NOT_FOUND", 422)
