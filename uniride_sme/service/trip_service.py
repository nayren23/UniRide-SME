"""Address service module"""

from datetime import datetime
from math import ceil
from typing import List

from uniride_sme import app
from uniride_sme import connect_pg
from uniride_sme.model.bo.address_bo import AddressBO
from uniride_sme.model.bo.trip_bo import TripBO
from uniride_sme.model.dto.address_dto import AddressDTO
from uniride_sme.model.dto.address_dto import AddressSimpleDTO
from uniride_sme.model.dto.trip_dto import TripDTO
from uniride_sme.service.address_service import (
    check_address_exigeance,
    set_latitude_longitude_from_address,
    address_exists,
    check_address_existence,
    concatene_address,
)
from uniride_sme.utils.exception.address_exceptions import InvalidIntermediateAddressException
from uniride_sme.utils.exception.trip_exceptions import (
    InvalidInputException,
    MissingInputException,
    TripAlreadyExistsException,
    TripNotFoundException,
)
from uniride_sme.utils.trip_status import TripStatus


def add_in_db(trip: TripBO):
    """Insert the trip in the database"""

    # Check if the address already exists
    trip_exists(trip)
    check_address_existence(trip.departure_address)
    check_address_existence(trip.arrival_address)
    calculate_price(trip)

    # validate values
    validate_total_passenger_count(trip.total_passenger_count)
    validate_timestamp_proposed(trip.timestamp_proposed)
    validate_status(trip.status)
    validate_price(trip.price)
    validate_user_id(trip.user_id)
    validate_address_depart_id_equals_address_arrival_id(
        trip.departure_address, trip.arrival_address
    )  # i need this function to check if the trip is viable

    query = (
        "INSERT INTO uniride.ur_trip (t_total_passenger_count,"
        "t_timestamp_proposed, t_status, t_price, t_user_id, t_address_depart_id, t_address_arrival_id) "
        " VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING t_id"
    )

    values = (
        trip.total_passenger_count,
        trip.timestamp_proposed,
        trip.status,
        trip.price,
        trip.user_id,
        trip.departure_address.id,
        trip.arrival_address.id,
    )

    conn = connect_pg.connect()
    trip_id = connect_pg.execute_command(conn, query, values)

    trip.id = trip_id


def validate_total_passenger_count(total_passenger_count):
    """Check if the total passenger count is valid"""
    if total_passenger_count is None:
        raise MissingInputException("TOTAL_PASSENGER_COUNT_CANNOT_BE_NULL")
    if total_passenger_count < 0:
        raise InvalidInputException("TOTAL_PASSENGER_COUNT_CANNOT_BE_NEGATIVE")
    if total_passenger_count > 4:  # TODO: change the number of seats in the car DB
        raise InvalidInputException("TOTAL_PASSENGER_COUNT_TOO_HIGH")


def validate_timestamp_proposed(timestamp_proposed):
    """Check if the timestamp proposed is valid"""
    if timestamp_proposed is None:
        raise MissingInputException("TIMESTAMP_PROPOSED_CANNOT_BE_NULL")
    try:
        datetime.strptime(timestamp_proposed, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        raise InvalidInputException("INVALID_TIMESTAMP_FORMAT") from e

    if datetime.strptime(timestamp_proposed, "%Y-%m-%d %H:%M:%S") < datetime.now():
        raise InvalidInputException("INVALID_TIMESTAMP_PROPOSED")


def validate_status(status):
    """Check if the status is valid"""
    if status is None:
        raise MissingInputException("STATUS_CANNOT_BE_NULL")
    if status < 0:
        raise InvalidInputException("STATUS_CANNOT_BE_NEGATIVE")


def validate_price(price):
    """Check if the price is valid"""
    if price is None:
        raise MissingInputException("PRICE_CANNOT_BE_NULL")
    if price < 0:
        raise InvalidInputException("PRICE_CANNOT_BE_NEGATIVE")


def validate_user_id(user_id):
    """Check if the user id is valid"""
    if user_id is None:
        raise MissingInputException("USER_ID_CANNOT_BE_NULL")
    if user_id < 0:
        raise InvalidInputException("USER_ID_CANNOT_BE_NEGATIVE")


def validate_address_depart_id_equals_address_arrival_id(departure_address: AddressBO, arrival_address: AddressBO):
    """Check if the address depart id is not equal to the address arrival id"""
    if departure_address.id == arrival_address.id:
        raise InvalidInputException("ADDRESS_DEPART_ID_CANNOT_BE_EQUALS_TO_ADDRESS_ARRIVAL_ID")

    university_address_bo = AddressBO(
        street_number=app.config["UNIVERSITY_STREET_NUMBER"],
        street_name=app.config["UNIVERSITY_STREET_NAME"],
        city=app.config["UNIVERSITY_CITY"],
        postal_code=app.config["UNIVERSITY_POSTAL_CODE"],
    )

    id_departure = address_exists(
        departure_address.street_number, departure_address.street_name, departure_address.city
    )
    id_arrival = address_exists(arrival_address.street_number, arrival_address.street_name, arrival_address.city)
    id_university = address_exists(
        university_address_bo.street_number, university_address_bo.street_name, university_address_bo.city
    )

    if id_university not in (id_departure, id_arrival):
        raise InvalidInputException("ADDRESS_DEPART_OR_ADDRESS_ARRIVAL_MUST_BE_EQUALS_TO_UNIVERSITY_ADDRESS")


def calculate_price(trip: TripBO):
    """Calculate the price of the trip"""

    origin = (trip.departure_address.latitude, trip.departure_address.longitude)
    destination = (trip.arrival_address.latitude, trip.arrival_address.longitude)
    distance = trip.route_checker.get_distance(origin, destination)

    rate_per_km = app.config["RATE_PER_KM"]
    cost_per_km = app.config["COST_PER_KM"]
    base_rate = app.config["BASE_RATE"]

    # Calculating the total cost of the trip
    total_cost = (distance * cost_per_km) + (distance * rate_per_km)

    # The recommended fare is capped at 1.5 times the base fare
    recommended_price = min(total_cost, base_rate * 1.5)

    # Reduce the price by 20%
    final_price = ceil(recommended_price * 0.8)

    trip.price = final_price


def trip_exists(trip: TripBO):
    """Check if the trip with address already exists in the database"""

    query = """
    SELECT t_id
    FROM uniride.ur_trip
    WHERE t_user_id = %s AND t_address_depart_id = %s AND t_address_arrival_id = %s AND t_timestamp_proposed = %s AND t_total_passenger_count = %s
    """

    conn = connect_pg.connect()
    trip_id = connect_pg.get_query(
        conn,
        query,
        (
            trip.user_id,
            trip.departure_address.id,
            trip.arrival_address.id,
            trip.timestamp_proposed,
            trip.total_passenger_count,
        ),
    )
    connect_pg.disconnect(conn)

    if trip_id:
        raise TripAlreadyExistsException()


def get_trips(trip: TripBO, departure_or_arrived_latitude, departure__or_arrived_longitude, condition_where):
    """Get the trips from the database"""

    query = f"""
        SELECT
            t.t_id AS trip_id,
            t.t_total_passenger_count AS total_passenger_count,
            t.t_timestamp_proposed AS proposed_date,
            t.t_status AS trip_status,
            t.t_price AS trip_price,
            t.t_user_id AS user_id,
            t.t_address_depart_id AS departure_address_id,
            t.t_address_arrival_id AS arrival_address_id,
            departure_address.a_latitude AS departure_latitude,
            departure_address.a_longitude AS departure_longitude,
            arrival_address.a_latitude AS arrival_latitude,
            arrival_address.a_longitude AS arrival_longitude
        FROM
            uniride.ur_trip t
        JOIN
            uniride.ur_address departure_address ON t.t_address_depart_id = departure_address.a_id
        JOIN
            uniride.ur_address arrival_address ON t.t_address_arrival_id = arrival_address.a_id
        WHERE
            {condition_where}
            AND t.t_timestamp_proposed BETWEEN 
            (TIMESTAMP %s - INTERVAL '1 hour') 
            AND 
            (TIMESTAMP %s + INTERVAL '1 hour')
            AND t.t_total_passenger_count >= %s
            AND t.t_status = %s
            ;
    """

    conn = connect_pg.connect()
    trips = connect_pg.get_query(
        conn,
        query,
        (
            departure_or_arrived_latitude,
            departure__or_arrived_longitude,
            trip.timestamp_proposed,
            trip.timestamp_proposed,
            trip.total_passenger_count,
            TripStatus.PENDING.value,
        ),
    )
    connect_pg.disconnect(conn)

    return trips


def get_trips_for_university_address(trip_bo: TripBO, depart_address_bo, address_arrival_bo, university_address_bo):
    """Get the trips for the university address"""
    point_intermediaire_departure = (depart_address_bo.latitude, depart_address_bo.longitude)
    intermediate_point_arrival = (address_arrival_bo.latitude, address_arrival_bo.longitude)
    university_point = (university_address_bo.latitude, university_address_bo.longitude)

    if point_intermediaire_departure == university_point:
        condition_where = "(departure_address.a_latitude = %s AND departure_address.a_longitude = %s)"
    elif intermediate_point_arrival == university_point:
        condition_where = "(arrival_address.a_latitude = %s AND arrival_address.a_longitude = %s)"
    else:
        # If an intermediate address is not the university, raise an exception
        raise InvalidIntermediateAddressException
    # Get the trips
    trips = get_trips(trip_bo, university_address_bo.latitude, university_address_bo.longitude, condition_where)

    available_trips: List[TripDTO] = []

    for trip in trips:
        (
            trip_id,
            total_passenger_count,
            proposed_date,
            _,
            trip_price,
            user_id,
            departure_address_id,
            arrival_address_id,
            departure_latitude,
            departure_longitude,
            arrival_latitude,
            arrival_longitude,
        ) = trip
        departure_point = (departure_latitude, departure_longitude)
        arrival_point = (arrival_latitude, arrival_longitude)

        is_viable = trip_bo.route_checker.check_if_route_is_viable(
            departure_point, arrival_point, point_intermediaire_departure
        )
        if is_viable:
            price = trip_price * trip_bo.total_passenger_count

            departure_address = AddressBO(address_id=departure_address_id)
            arrival_address = AddressBO(address_id=arrival_address_id)

            check_address_existence(departure_address)
            check_address_existence(arrival_address)

            address_dtos = {
                "departure": AddressDTO(
                    id=departure_address_id,
                    latitude=departure_latitude,
                    longitude=departure_longitude,
                    address_name=concatene_address(
                        departure_address.street_number,
                        departure_address.street_name,
                        departure_address.city,
                        departure_address.postal_code,
                    ),
                ),
                "arrival": AddressDTO(
                    id=arrival_address_id,
                    latitude=arrival_latitude,
                    longitude=arrival_longitude,
                    address_name=concatene_address(
                        arrival_address.street_number,
                        arrival_address.street_name,
                        arrival_address.city,
                        arrival_address.postal_code,
                    ),
                ),
            }

            trip_dto = TripDTO(
                trip_id=trip_id,
                address=address_dtos,
                driver_id=user_id,
                price=price,
                proposed_date=str(proposed_date),
                total_passenger_count=total_passenger_count,
            )
            available_trips.append(trip_dto)

    return available_trips


def get_driver_trips(user_id):
    """Get the current trips for the driver"""

    query = """
        SELECT t_id, t_address_depart_id, t_address_arrival_id,t_price
        FROM uniride.ur_trip
        WHERE t_user_id = %s
        AND t_status = %s
    """
    values = (user_id, TripStatus.PENDING.value)
    conn = connect_pg.connect()
    driver_current_trips = connect_pg.get_query(conn, query, values)

    connect_pg.disconnect(conn)

    return driver_current_trips


def format_get_current_driver_trips(trip: TripBO, driver_current_trips, user_id):
    """Format the current trips for the driver"""

    available_trips = []

    for current_trip in driver_current_trips:
        t_id, t_address_depart_id, t_address_arrival_id, price = current_trip

        trip.departure_address = AddressBO(address_id=t_address_depart_id)
        trip.arrival_address = AddressBO(address_id=t_address_arrival_id)

        check_address_existence(trip.departure_address)
        check_address_existence(trip.arrival_address)

        address_dtos = {
            "departure": AddressSimpleDTO(
                id=trip.departure_address.id,
                name=concatene_address(
                    trip.departure_address.street_number,
                    trip.departure_address.street_name,
                    trip.departure_address.city,
                    trip.departure_address.postal_code,
                ),
            ),
            "arrival": AddressSimpleDTO(
                id=trip.arrival_address.id,
                name=concatene_address(
                    trip.arrival_address.street_number,
                    trip.arrival_address.street_name,
                    trip.arrival_address.city,
                    trip.arrival_address.postal_code,
                ),
            ),
        }
        trip_dto = TripDTO(
            trip_id=t_id,
            address=address_dtos,
            driver_id=user_id,
            price=price,
        )
        available_trips.append(trip_dto)

    return available_trips


def check_if_trip_exists(trip_bo: TripBO):
    """Check if the trip exists in the database"""

    query = """
    SELECT *
    FROM uniride.ur_trip
    WHERE t_id = %s
    """

    conn = connect_pg.connect()
    trip = connect_pg.get_query(conn, query, (trip_bo.id,))
    connect_pg.disconnect(conn)

    if trip:
        trip_bo.id = (trip[0][0],)
        trip_bo.total_passenger_count = (trip[0][1],)
        trip_bo.timestamp_creation = (trip[0][2],)
        trip_bo.timestamp_proposed = (trip[0][3],)
        trip_bo.status = (trip[0][4],)
        trip_bo.price = (trip[0][5],)
        trip_bo.user_id = (trip[0][6],)
        trip_bo.departure_address.id = (trip[0][7],)
        trip_bo.arrival_address.id = trip[0][8]
        return True
    raise TripNotFoundException()


def get_available_trips_to(trip: TripBO):
    """Get the available trips"""

    # We check if the address is valid
    check_address_exigeance(trip.departure_address)
    check_address_exigeance(trip.arrival_address)

    set_latitude_longitude_from_address(trip.departure_address)
    set_latitude_longitude_from_address(trip.arrival_address)

    university_address_bo = AddressBO(
        street_number=app.config["UNIVERSITY_STREET_NUMBER"],
        street_name=app.config["UNIVERSITY_STREET_NAME"],
        city=app.config["UNIVERSITY_CITY"],
        postal_code=app.config["UNIVERSITY_POSTAL_CODE"],
    )

    # We check if the address is valid
    check_address_exigeance(university_address_bo)

    set_latitude_longitude_from_address(university_address_bo)

    validate_total_passenger_count(trip.total_passenger_count)
    validate_timestamp_proposed(trip.timestamp_proposed)

    available_trips = get_trips_for_university_address(
        trip, trip.departure_address, trip.arrival_address, university_address_bo
    )

    return available_trips
