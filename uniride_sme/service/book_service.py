"""Book service module"""
import random
from datetime import datetime

from uniride_sme import connect_pg
from uniride_sme.model.bo.address_bo import AddressBO
from uniride_sme.model.bo.book_bo import BookBO
from uniride_sme.model.dto.book_dto import BookDTO
from uniride_sme.model.dto.trip_dto import TripShortDTO
from uniride_sme.model.dto.user_dto import UserShortDTO
from uniride_sme.service import trip_service
from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,
    MissingInputException,
    ForbiddenException,
)
from uniride_sme.utils.exception.book_exceptions import (
    TripAlreadyBookedException,
    BookingNotFoundException,
    BookingAlreadyRespondedException,
)
from uniride_sme.utils.file import get_encoded_file


def _validate_passenger_count(trip, passenger_count) -> None:
    if passenger_count is None:
        raise MissingInputException("PASSENGER_COUNT_MISSING")

    if passenger_count <= 0:
        raise InvalidInputException("PASSENGER_COUNT_TOO_LOW")

    if passenger_count > trip["total_passenger_count"] - trip["passenger_count"]:
        raise InvalidInputException("PASSENGER_COUNT_TOO_HIGH")


def _validate_user_id(trip, user_id) -> None:
    if not user_id:
        raise MissingInputException("USER_ID_MISSING")

    if user_id == trip["driver_id"]:
        raise ForbiddenException("DRIVER_CANNOT_BOOK_HIS_OWN_TRIP")


def _validate_trip_availability(trip) -> None:
    departure_date = datetime.strptime(trip["departure_date"], "%Y-%m-%d %H:%M:%S")
    if trip["status"] != 1 or departure_date < datetime.now():
        raise ForbiddenException("TRIP_NOT_AVAILABLE")


def _check_trip_already_booked(trip_id, user_id) -> None:
    conn = connect_pg.connect()
    query = "SELECT * FROM uniride.ur_join WHERE t_id = %s AND u_id = %s"
    values = (trip_id, user_id)
    bookings = connect_pg.get_query(conn, query, values, True)
    connect_pg.disconnect(conn)
    for booking in bookings:
        if booking["j_accepted"] != -2:
            raise TripAlreadyBookedException()
    if len(bookings) > 3:
        raise ForbiddenException("BOOKED_TOO_MANY_TIMES")


def book_trip(trip_id, user_id, passenger_count) -> None:
    """Book a trip"""
    trip = trip_service.get_trip_by_id(trip_id)

    _validate_trip_availability(trip)
    _validate_user_id(trip, user_id)
    _validate_passenger_count(trip, passenger_count)

    _check_trip_already_booked(trip_id, user_id)

    query = "INSERT INTO uniride.ur_join(u_id, t_id, j_passenger_count) VALUES (%s, %s, %s);"
    values = (user_id, trip_id, passenger_count)
    conn = connect_pg.connect()
    connect_pg.execute_command(conn, query, values)
    connect_pg.disconnect(conn)


def get_booking_by_id(trip_id, user_id):
    """Get booking by id"""
    if not trip_id:
        raise MissingInputException("TRIP_ID_MISSING")
    if not user_id:
        raise MissingInputException("USER_ID_MISSING")

    conn = connect_pg.connect()
    query = "SELECT * FROM uniride.ur_join WHERE t_id = %s AND u_id = %s"
    values = (trip_id, user_id)
    booking = connect_pg.get_query(conn, query, values, True)
    connect_pg.disconnect(conn)

    if not booking:
        raise BookingNotFoundException()
    book_bo = BookBO(
        user_id=booking[0]["u_id"],
        trip_id=booking[0]["t_id"],
        accepted=booking[0]["j_accepted"],
        passenger_count=booking[0]["j_passenger_count"],
        date_requested=booking[0]["j_date_requested"],
        joined=booking[0]["j_joined"],
        verification_code=booking[0]["j_verification_code"],
    )
    return book_bo


def _validate_driver_id(trip, driver_id) -> None:
    if not driver_id:
        raise MissingInputException("DRIVER_ID_MISSING")

    if driver_id != trip["driver_id"]:
        raise ForbiddenException("ONLY_DRIVER_CAN_RESPOND")


def _validate_response(response) -> None:
    if not response:
        raise MissingInputException("RESPONSE_MISSING")

    if response not in (-1, 1):
        raise InvalidInputException("RESPONSE_INVALID")


def _validate_booking_status(accepted) -> None:
    if accepted:
        raise BookingAlreadyRespondedException()


def respond_booking(trip_id, driver_id, booker_id, response) -> None:
    """Respond to a booking request"""
    _validate_response(response)

    trip = trip_service.get_trip_by_id(trip_id)

    _validate_driver_id(trip, driver_id)
    _validate_trip_availability(trip)
    booking = get_booking_by_id(trip_id, booker_id)
    _validate_booking_status(booking.accepted)

    query = "UPDATE uniride.ur_join SET"

    if response == 1:
        _validate_passenger_count(trip, booking.passenger_count)
        query += " j_verification_code = %s,"
        values = (random.randint(1000, 9999),)

    query += " j_accepted = %s WHERE t_id = %s AND u_id = %s"
    values += (response, trip_id, booker_id)

    conn = connect_pg.connect()
    connect_pg.execute_command(conn, query, values)
    connect_pg.disconnect(conn)


def get_bookings(user_id) -> list[BookDTO]:
    """Return all bookings of a driver"""
    if not user_id:
        raise MissingInputException("USER_ID_MISSING")

    query = """
        SELECT 
            j.j_accepted, 
            j.j_passenger_count, 
            j.j_date_requested,
            t.t_id,
            t.t_timestamp_proposed,
            departure.a_id AS departure_a_id,
            departure.a_street_number AS departure_a_street_number,
            departure.a_street_name AS departure_a_street_name,
            departure.a_city AS departure_a_city,
            departure.a_postal_code AS departure_a_postal_code,
            arrival.a_id AS arrival_a_id,
            arrival.a_street_number AS arrival_a_street_number,
            arrival.a_street_name AS arrival_a_street_name,
            arrival.a_city AS arrival_a_city,
            arrival.a_postal_code AS arrival_a_postal_code,
            u.u_id,
            u.u_firstname,
            u.u_lastname,
            u.u_profile_picture
        FROM 
            uniride.ur_join j
        JOIN
            uniride.ur_trip t on j.t_id = t.t_id
        JOIN 
            uniride.ur_address departure ON t.t_address_departure_id = departure.a_id
        JOIN 
            uniride.ur_address arrival ON t.t_address_arrival_id = arrival.a_id 
        JOIN 
            uniride.ur_user u on j.u_id = u.u_id
        WHERE
            t.t_user_id = %s
        """

    values = (user_id,)
    conn = connect_pg.connect()
    result = connect_pg.get_query(conn, query, values, True)
    connect_pg.disconnect(conn)
    bookings = []
    for booking in result:
        user = UserShortDTO(
            id=booking["u_id"],
            firstname=booking["u_firstname"],
            lastname=booking["u_lastname"],
            profile_picture=get_encoded_file(booking["u_profile_picture"], "PFP_UPLOAD_FOLDER"),
        )
        departure_address = AddressBO(
            id=booking["departure_a_id"],
            street_number=booking["departure_a_street_number"],
            street_name=booking["departure_a_street_name"],
            city=booking["departure_a_city"],
            postal_code=booking["departure_a_postal_code"],
        ).get_full_address()

        arrival_address = AddressBO(
            id=booking["arrival_a_id"],
            street_number=booking["arrival_a_street_number"],
            street_name=booking["arrival_a_street_name"],
            city=booking["arrival_a_city"],
            postal_code=booking["arrival_a_postal_code"],
        ).get_full_address()

        trip = TripShortDTO(
            trip_id=booking["t_id"],
            departure_address=departure_address,
            arrival_address=arrival_address,
            departure_date=booking["t_timestamp_proposed"],
        )

        bookings.append(
            BookDTO(
                user=user,
                trip=trip,
                accepted=booking["j_accepted"],
                passenger_count=booking["j_passenger_count"],
                date_requested=booking["j_date_requested"],
            )
        )
    return bookings


def cancel_request_trip(user_id, trip_id) -> None:
    """Cancel request trip"""
    if user_id is None:
        raise MissingInputException("USER_ID_MISSING")
    if trip_id is None:
        raise MissingInputException("TRIP_ID_MISSING")
    conn = connect_pg.connect()
    query = "UPDATE uniride.ur_join SET j_accepted=-2 WHERE u_id = %s AND t_id = %s"
    connect_pg.execute_command(conn, query, (user_id, trip_id))
    connect_pg.disconnect(conn)


def _validate_trip_started(trip) -> None:
    if trip["status"] != 4:
        raise ForbiddenException("TRIP_NOT_STARTED")


def _validate_booking(booking: BookBO, verification_code: int) -> None:
    if not booking:
        raise BookingNotFoundException()

    if booking.joined:
        raise ForbiddenException("PASSENGER_AlREADY_JOINED")

    if booking.accepted != 1:
        raise ForbiddenException("BOOKING_NOT_ACCEPTED")

    if booking.verification_code != verification_code:
        raise ForbiddenException("INVALID_VERIFICATION_CODE")


def join(trip_id, driver_id, booker_id, verification_code) -> None:
    """Respond to a booking request"""
    trip = trip_service.get_trip_by_id(trip_id)
    _validate_trip_started(trip)
    _validate_driver_id(trip, driver_id)

    booking = get_booking_by_id(trip_id, booker_id)
    _validate_booking(booking, verification_code)

    conn = connect_pg.connect()
    query = "UPDATE uniride.ur_join SET j_joined = true WHERE t_id = %s AND u_id = %s"
    values = (trip_id, booker_id)
    connect_pg.execute_command(conn, query, values)
    connect_pg.disconnect(conn)


def get_verification_code(trip_id, user_id) -> int:
    """Get verification code"""
    trip = trip_service.get_trip_by_id(trip_id)
    _validate_trip_started(trip)
    if not user_id:
        raise MissingInputException("USER_ID_MISSING")

    conn = connect_pg.connect()
    query = "SELECT j_accepted, j_verification_code FROM uniride.ur_join WHERE t_id = %s AND u_id = %s"
    values = (trip_id, user_id)
    booking = connect_pg.get_query(conn, query, values, True)
    connect_pg.disconnect(conn)

    if not booking:
        raise BookingNotFoundException()
    if booking[0]["j_accepted"] != 1:
        raise ForbiddenException("BOOKING_NOT_ACCEPTED")

    return booking[0]["j_verification_code"]


def get_booking(trip_id, user_id) -> BookBO:
    """Get last booking of a user for a trip"""
    if not trip_id:
        raise MissingInputException("TRIP_ID_MISSING")
    if not user_id:
        raise MissingInputException("USER_ID_MISSING")

    conn = connect_pg.connect()
    query = "SELECT * FROM uniride.ur_join WHERE t_id = %s AND u_id = %s ORDER BY j_date_requested DESC"
    values = (trip_id, user_id)
    booking = connect_pg.get_query(conn, query, values, True)
    connect_pg.disconnect(conn)

    if not booking:
        raise BookingNotFoundException()

    book_bo = BookBO(
        user_id=booking[0]["u_id"],
        trip_id=booking[0]["t_id"],
        accepted=booking[0]["j_accepted"],
        passenger_count=booking[0]["j_passenger_count"],
        date_requested=booking[0]["j_date_requested"],
        joined=booking[0]["j_joined"],
        verification_code=booking[0]["j_verification_code"],
    )
    return book_bo
