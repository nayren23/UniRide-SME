"""Book service module"""
import psycopg2

from uniride_sme import connect_pg
from uniride_sme.model.bo.book_bo import BookBO
from uniride_sme.model.dto.book_dto import BookDTO
from uniride_sme.service import trip_service
from uniride_sme.utils.exception.exceptions import InvalidInputException, ForbiddenException
from uniride_sme.utils.exception.book_exceptions import (
    TripAlreadyBookedException,
    BookingNotFoundException,
    BookingAlreadyRespondedException,
)


def _validate_passenger_count(trip, passenger_count):
    if passenger_count <= 0:
        raise InvalidInputException("PASSENGER_COUNT_TOO_LOW")

    if passenger_count > trip["total_passenger_count"] - trip["passenger_count"]:
        raise InvalidInputException("PASSENGER_COUNT_TOO_HIGH")


def book_trip(trip_id, user_id, passenger_count):
    """Book a trip"""
    trip = trip_service.get_trip_by_id(trip_id)
    if user_id == trip["driver_id"]:
        raise ForbiddenException("DRIVER_CANNOT_BOOK_HIS_OWN_TRIP")
    _validate_passenger_count(trip, passenger_count)

    query = "INSERT INTO uniride.ur_join(u_id, t_id, r_passenger_count) VALUES (%s, %s, %s);"
    values = (user_id, trip_id, passenger_count)
    try:
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, values)
        connect_pg.disconnect(conn)
    except psycopg2.errors.UniqueViolation as e:
        raise TripAlreadyBookedException() from e


def get_booking_by_id(trip_id, user_id):
    """Get booking by id"""
    conn = connect_pg.connect()
    query = "SELECT * FROM uniride.ur_join WHERE t_id = %s AND u_id = %s"
    values = (trip_id, user_id)
    booking = connect_pg.get_query(conn, query, values, True)
    connect_pg.disconnect(conn)
    if not booking:
        raise BookingNotFoundException()
    return booking[0]


def respond_booking(trip_id, driver_id, booker_id, response):
    """Respond to a booking request"""
    if response not in (-1, 1):
        raise InvalidInputException("INVALID_RESPONSE")

    trip = trip_service.get_trip_by_id(trip_id)
    if trip["driver_id"] != driver_id:
        raise ForbiddenException("ONLY_DRIVER_CAN_RESPOND")

    booking = get_booking_by_id(trip_id, booker_id)
    if booking["r_accepted"]:
        raise BookingAlreadyRespondedException()

    _validate_passenger_count(trip, booking["r_passenger_count"])

    query = "UPDATE uniride.ur_join SET r_accepted = %s WHERE t_id = %s AND u_id = %s"
    values = (response, trip_id, booker_id)
    conn = connect_pg.connect()
    connect_pg.execute_command(conn, query, values)
    connect_pg.disconnect(conn)


def get_bookings(user_id):
    """Return all bookings of a driver"""
    query = "SELECT u_id, t_id, r_accepted, r_passenger_count, r_date_requested FROM uniride.ur_join natural join uniride.ur_trip where ur_trip.t_user_id = %s"
    values = (user_id,)
    conn = connect_pg.connect()
    result = connect_pg.get_query(conn, query, values, True)
    connect_pg.disconnect(conn)
    bookings = []
    for booking in result:
        bookings.append(
            BookBO(
                user_id=booking["u_id"],
                trip_id=booking["t_id"],
                accepted=booking["r_accepted"],
                passenger_count=booking["r_passenger_count"],
                date_requested=booking["r_date_requested"],
            )
        )
    return bookings


def get_books_dtos(user_id):
    """Return all bookings of a driver"""
    book_bos = get_bookings(user_id)
    book_dtos = []
    for book_bo in book_bos:
        book_dtos.append(
            BookDTO(
                user_id=book_bo.user_id,
                trip_id=book_bo.trip_id,
                accepted=book_bo.accepted,
                passenger_count=book_bo.passenger_count,
                date_requested=book_bo.date_requested,
            )
        )
    return book_dtos
