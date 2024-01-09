"""Trip service module"""

from datetime import datetime, timedelta
from math import ceil
from typing import List

from uniride_sme import app
from uniride_sme import connect_pg
from uniride_sme.model.bo.address_bo import AddressBO
from uniride_sme.model.bo.trip_bo import TripBO
from uniride_sme.model.dto.address_dto import AddressDTO, AddressSimpleDTO
from uniride_sme.model.dto.user_dto import PassengerInfosDTO
from uniride_sme.model.dto.trip_dto import TripDTO, TripDetailedDTO,PassengerTripDTO
from uniride_sme.service.car_service import get_car_info_by_user_id
from uniride_sme.service.address_service import (
    check_address_exigeance,
    set_latitude_longitude_from_address,
    address_exists,
    check_address_existence,
)
from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,
    MissingInputException,
    ForbiddenException,
)
from uniride_sme.utils.exception.address_exceptions import InvalidIntermediateAddressException
from uniride_sme.utils.exception.trip_exceptions import (
    TripAlreadyExistsException,
    TripNotFoundException,
)
from uniride_sme.utils.trip_status import TripStatus
from uniride_sme.utils.maths_formulas import haversine
from uniride_sme.utils.file import get_encoded_file


def add_trip(trip: TripBO):
    """Insert the trip in the database"""

    # Check if the address already exists
    trip_exists(trip)
    check_address_existence(trip.departure_address)
    check_address_existence(trip.arrival_address)
    # calculate_price(trip)
    trip.price = 0.0
    # validate values
    # validate_total_passenger_count(trip.total_passenger_count, trip.user_id)
    validate_total_passenger_count(trip.total_passenger_count)
    validate_timestamp_proposed(trip.timestamp_proposed)
    validate_status(trip.status)
    validate_price(trip.price)
    validate_user_id(trip.user_id)
    validate_address_departure_id_equals_address_arrival_id(
        trip.departure_address, trip.arrival_address
    )  # i need this function to check if the trip is viable

    query = (
        "INSERT INTO uniride.ur_trip (t_total_passenger_count,"
        "t_timestamp_proposed, t_status, t_price, t_user_id, t_address_departure_id, t_address_arrival_id) "
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
    connect_pg.disconnect(conn)
    trip.id = trip_id


def validate_total_passenger_count(total_passenger_count):
    """Check if the total passenger count is valid"""
    if total_passenger_count is None:
        raise MissingInputException("TOTAL_PASSENGER_COUNT_CANNOT_BE_NULL")
    if total_passenger_count < 0:
        raise InvalidInputException("TOTAL_PASSENGER_COUNT_CANNOT_BE_NEGATIVE")
    # info_car = get_car_info_by_user_id(user_id)
    # if total_passenger_count > info_car[0].get("v_total_places"):
    if total_passenger_count > 4:
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


def validate_address_departure_id_equals_address_arrival_id(departure_address: AddressBO, arrival_address: AddressBO):
    """Check if the address departure id is not equal to the address arrival id"""
    if departure_address.id == arrival_address.id:
        raise InvalidInputException("ADDRESS_DEPARTURE_ID_CANNOT_BE_EQUALS_TO_ADDRESS_ARRIVAL_ID")

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
        raise InvalidInputException("ADDRESS_DEPARTURE_OR_ADDRESS_ARRIVAL_MUST_BE_EQUALS_TO_UNIVERSITY_ADDRESS")


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
    WHERE t_user_id = %s AND t_address_departure_id = %s AND t_address_arrival_id = %s AND t_timestamp_proposed = %s AND t_total_passenger_count = %s
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
            t.t_id,
            t.t_total_passenger_count,
            t.t_timestamp_proposed,
            t.t_status,
            t.t_price,
            t.t_user_id,       
            departure.a_id AS departure_a_id,
            departure.a_street_number AS departure_a_street_number,
            departure.a_street_name AS departure_a_street_name,
            departure.a_city AS departure_a_city,
            departure.a_postal_code AS departure_a_postal_code,
            departure.a_latitude AS departure_a_latitude,
            departure.a_longitude AS departure_a_longitude,
            arrival.a_id AS arrival_a_id,
            arrival.a_street_number AS arrival_a_street_number,
            arrival.a_street_name AS arrival_a_street_name,
            arrival.a_city AS arrival_a_city,
            arrival.a_postal_code AS arrival_a_postal_code,
            arrival.a_latitude AS arrival_a_latitude,
            arrival.a_longitude AS arrival_a_longitude
        FROM 
            uniride.ur_trip t
        JOIN 
            uniride.ur_address departure ON t.t_address_departure_id = departure.a_id
        JOIN 
            uniride.ur_address arrival ON t.t_address_arrival_id = arrival.a_id
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
        True,
    )
    connect_pg.disconnect(conn)

    return trips


def get_trips_for_university_address(trip_bo: TripBO, departure_address_bo, address_arrival_bo, university_address_bo):
    """Get the trips for the university address"""
    intermediate_point_departure = (departure_address_bo.latitude, departure_address_bo.longitude)
    intermediate_point_arrival = (address_arrival_bo.latitude, address_arrival_bo.longitude)
    university_point = (university_address_bo.latitude, university_address_bo.longitude)

    if intermediate_point_departure == university_point:
        condition_where = "(departure.a_latitude = %s AND departure.a_longitude = %s)"
    elif intermediate_point_arrival == university_point:
        condition_where = "(arrival.a_latitude = %s AND arrival.a_longitude = %s)"
    else:
        # If an intermediate address is not the university, raise an exception
        raise InvalidIntermediateAddressException
    # Get the trips
    trips = get_trips(trip_bo, university_address_bo.latitude, university_address_bo.longitude, condition_where)

    available_trips: List[TripDTO] = []

    for trip in trips:
        trip_bo = format_trip(trip)
        trip_bo.price = trip_bo.price * trip_bo.total_passenger_count

        if intermediate_point_departure == university_point:
            distance = haversine(
                address_arrival_bo.latitude,
                address_arrival_bo.longitude,
                trip_bo.arrival_address.latitude,
                trip_bo.arrival_address.longitude,
            )
        else:
            distance = haversine(
                departure_address_bo.latitude,
                departure_address_bo.longitude,
                trip_bo.departure_address.latitude,
                trip_bo.departure_address.longitude,
            )

        address_dtos = {
            "departure": AddressDTO(
                id=trip_bo.departure_address.id,
                latitude=trip_bo.departure_address.latitude,
                longitude=trip_bo.departure_address.longitude,
                address_name=trip_bo.departure_address.get_full_address(),
            ),
            "arrival": AddressDTO(
                id=trip_bo.arrival_address.id,
                latitude=trip_bo.arrival_address.latitude,
                longitude=trip_bo.arrival_address.longitude,
                address_name=trip_bo.arrival_address.get_full_address(),
            ),
            "distance": distance,
        }

        trip_dto = TripDTO(
            trip_id=trip_bo.id,
            address=address_dtos,
            driver_id=trip_bo.user_id,
            price=trip_bo.price,
            proposed_date=str(trip_bo.timestamp_proposed),
            total_passenger_count=trip_bo.total_passenger_count,
        )
        available_trips.append(trip_dto)

    return available_trips


def get_driver_trips(user_id):
    """Get the current trips for the driver"""

    query = """
        SELECT 
            t_id, 
            t_price, 
            t_timestamp_proposed,
            t.t_user_id, 
            t.t_id,
            departure.a_id AS departure_a_id,
            departure.a_street_number AS departure_a_street_number,
            departure.a_street_name AS departure_a_street_name,
            departure.a_city AS departure_a_city,
            departure.a_postal_code AS departure_a_postal_code,
            departure.a_latitude AS departure_a_latitude,
            departure.a_longitude AS departure_a_longitude,
            arrival.a_id AS arrival_a_id,
            arrival.a_street_number AS arrival_a_street_number,
            arrival.a_street_name AS arrival_a_street_name,
            arrival.a_city AS arrival_a_city,
            arrival.a_postal_code AS arrival_a_postal_code,
            arrival.a_latitude AS arrival_a_latitude,
            arrival.a_longitude AS arrival_a_longitude
        FROM 
            uniride.ur_trip t
        JOIN 
            uniride.ur_address departure ON t.t_address_departure_id = departure.a_id
        JOIN 
            uniride.ur_address arrival ON t.t_address_arrival_id = arrival.a_id
        WHERE t_user_id = %s
        AND t_status = %s
    """
    values = (user_id, TripStatus.PENDING.value)
    conn = connect_pg.connect()
    driver_current_trips = connect_pg.get_query(conn, query, values, True)

    connect_pg.disconnect(conn)
    available_trips = format_get_current_driver_trips(driver_current_trips)
    return available_trips


def format_get_current_driver_trips(driver_current_trips):
    """Format the current trips for the driver"""

    available_trips = []

    for current_trip in driver_current_trips:
        trip_bo = format_trip(current_trip)

        address_dtos = {
            "departure": AddressSimpleDTO(
                id=trip_bo.departure_address.id,
                name=trip_bo.departure_address.get_full_address(),
            ),
            "arrival": AddressSimpleDTO(
                id=trip_bo.arrival_address.id,
                name=trip_bo.arrival_address.get_full_address(),
            ),
        }
        trip_dto = TripDTO(
            trip_id=trip_bo.id,
            address=address_dtos,
            driver_id=trip_bo.user_id,
            proposed_date=str(trip_bo.timestamp_proposed),
            price=trip_bo.price,
        )
        available_trips.append(trip_dto)

    return available_trips


def format_trip(raw_trip: dict) -> TripBO:
    """Format the trip"""
    departure_address = AddressBO(
        id=raw_trip["departure_a_id"],
        street_number=raw_trip["departure_a_street_number"],
        street_name=raw_trip["departure_a_street_name"],
        city=raw_trip["departure_a_city"],
        postal_code=raw_trip["departure_a_postal_code"],
        latitude=raw_trip["departure_a_latitude"],
        longitude=raw_trip["departure_a_longitude"],
    )
    arrival_address = AddressBO(
        id=raw_trip["arrival_a_id"],
        street_number=raw_trip["arrival_a_street_number"],
        street_name=raw_trip["arrival_a_street_name"],
        city=raw_trip["arrival_a_city"],
        postal_code=raw_trip["arrival_a_postal_code"],
        latitude=raw_trip["arrival_a_latitude"],
        longitude=raw_trip["arrival_a_longitude"],
    )
    trip = TripBO(
        trip_id=raw_trip["t_id"],
        price=raw_trip["t_price"],
        timestamp_proposed=raw_trip["t_timestamp_proposed"],
        departure_address_bo=departure_address,
        arrival_address_bo=arrival_address,
        user_id=raw_trip["t_user_id"],
        passenger_count=raw_trip.get("passenger_count", None),
        total_passenger_count=raw_trip.get("t_total_passenger_count", None),
        status=raw_trip.get("t_status", None),
    )
    return trip


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

    validate_timestamp_proposed(trip.timestamp_proposed)

    available_trips = get_trips_for_university_address(
        trip, trip.departure_address, trip.arrival_address, university_address_bo
    )

    return available_trips


def get_trip_by_id(trip_id):
    """Get the formatted trip by id"""
    if not trip_id:
        raise MissingInputException("TRIP_ID_MISSING")

    query = """
        SELECT
            t.t_id, 
            t.t_price, 
            t.t_timestamp_proposed,
            t.t_user_id, 
            t.t_status,
            t.t_total_passenger_count,
            departure.a_id AS departure_a_id,
            departure.a_street_number AS departure_a_street_number,
            departure.a_street_name AS departure_a_street_name,
            departure.a_city AS departure_a_city,
            departure.a_postal_code AS departure_a_postal_code,
            departure.a_latitude AS departure_a_latitude,
            departure.a_longitude AS departure_a_longitude,
            arrival.a_id AS arrival_a_id,
            arrival.a_street_number AS arrival_a_street_number,
            arrival.a_street_name AS arrival_a_street_name,
            arrival.a_city AS arrival_a_city,
            arrival.a_postal_code AS arrival_a_postal_code,
            arrival.a_latitude AS arrival_a_latitude,
            arrival.a_longitude AS arrival_a_longitude
        FROM 
            uniride.ur_trip t
        JOIN 
            uniride.ur_address departure ON t.t_address_departure_id = departure.a_id
        JOIN 
            uniride.ur_address arrival ON t.t_address_arrival_id = arrival.a_id
        WHERE
            t.t_id = %s
        GROUP BY
            t.t_id, 
            t.t_price, 
            t.t_timestamp_proposed,
            t.t_user_id, 
            t.t_status,
            t.t_total_passenger_count,
            departure.a_id,
            departure.a_street_number,
            departure.a_street_name,
            departure.a_city,
            departure.a_postal_code,
            departure.a_latitude,
            departure.a_longitude,
            arrival.a_id,
            arrival.a_street_number,
            arrival.a_street_name,
            arrival.a_city,
            arrival.a_postal_code,
            arrival.a_latitude,
            arrival.a_longitude
    """

    conn = connect_pg.connect()
    trip = connect_pg.get_query(conn, query, (trip_id,), True)
    if not trip:
        raise TripNotFoundException()
    trip = trip[0]

    query = "SELECT SUM(j_passenger_count) FROM uniride.ur_join WHERE t_id = %s and j_accepted = 1"
    passenger_count = connect_pg.get_query(conn, query, (trip_id,))[0][0]
    connect_pg.disconnect(conn)
    trip["passenger_count"] = passenger_count if passenger_count else 0
    trip_bo = format_trip(trip)
    origin = (trip_bo.departure_address.latitude, trip_bo.departure_address.longitude)
    destination = (trip_bo.arrival_address.latitude, trip_bo.arrival_address.longitude)
    duration = trip_bo.route_checker.get_duration(origin, destination, trip_bo.timestamp_proposed)
    arrival_date = trip_bo.timestamp_proposed + timedelta(seconds=duration)
    address_dtos = {
        "departure": AddressDTO(
            id=trip_bo.departure_address.id,
            latitude=trip_bo.departure_address.latitude,
            longitude=trip_bo.departure_address.longitude,
            address_name=trip_bo.departure_address.get_full_address(),
        ),
        "arrival": AddressDTO(
            id=trip_bo.arrival_address.id,
            latitude=trip_bo.arrival_address.latitude,
            longitude=trip_bo.arrival_address.longitude,
            address_name=trip_bo.arrival_address.get_full_address(),
        ),
    }

    trip_dto = TripDetailedDTO(
        trip_id=trip_bo.id,
        address=address_dtos,
        driver_id=trip_bo.user_id,
        price=trip_bo.price,
        departure_date=str(trip_bo.timestamp_proposed),
        arrival_date=str(arrival_date),
        passenger_count=trip_bo.passenger_count,
        total_passenger_count=trip_bo.total_passenger_count,
        status=trip_bo.status,
    )
    return trip_dto


def count_trip():
    """Get number of trip"""
    conn = connect_pg.connect()
    query = "SELECT COUNT(*) FROM uniride.ur_trip"
    result = connect_pg.get_query(conn, query)
    connect_pg.disconnect(conn)
    return result[0][0]


def _validate_trip_id(trip_id):
    """Validate the trip id"""
    conn = connect_pg.connect()

    query = """
    SELECT 
        t_user_id
    FROM 
        uniride.ur_trip 
    WHERE 
        t_id = %s
    """
    driver_id = connect_pg.get_query(conn, query, (trip_id,))
    connect_pg.disconnect(conn)

    if not driver_id:
        raise TripNotFoundException()

    return driver_id[0][0]


def _verify_user_id(user_id, driver_id, passengers):
    """Verify the user id"""
    user_ids = [passenger["u_id"] for passenger in passengers]
    user_ids.append(driver_id)
    if user_id not in user_ids:
        raise ForbiddenException("ONLY_DRIVER_AND_PASSENGERS_ALLOWED")


def get_passengers(trip_id, user_id):
    """Get passengers"""
    driver_id = _validate_trip_id(trip_id)

    conn = connect_pg.connect()
    query = """
    SELECT 
        u_id, 
        u_firstname, 
        u_lastname, 
        u_profile_picture 
    FROM 
        uniride.ur_user 
    WHERE 
        u_id IN (SELECT u_id FROM uniride.ur_join WHERE t_id = %s AND j_accepted = 1)
    """
    passengers = connect_pg.get_query(conn, query, (trip_id,), True)
    connect_pg.disconnect(conn)
    _verify_user_id(user_id, driver_id, passengers)
    passenger_dtos = []
    for passenger in passengers:
        passenger_dtos.append(
            PassengerInfosDTO(
                id=passenger["u_id"],
                firstname=passenger["u_firstname"],
                lastname=passenger["u_lastname"],
                profile_picture=get_encoded_file(passenger["u_profile_picture"], app.config["PFP_UPLOAD_FOLDER"]),
            )
        )
    return passenger_dtos


def trips_status(status):
    """Get number status of trip"""
    conn = connect_pg.connect()
    query = "SELECT COUNT(*) FROM uniride.ur_trip WHERE t_status = %s"
    result = connect_pg.get_query(conn, query, (status,))
    connect_pg.disconnect(conn)
    return result[0][0]

def passenger_current_trips(user_id):
    """Get passager current"""
    if user_id is None:
        raise MissingInputException("USER_ID_CANNOT_BE_NULL")

    conn = connect_pg.connect()
    query = """
        Select  
                u_id, 
                t_id, 
                j_accepted,
                t.t_timestamp_proposed,
                t.t_status,
                departure.a_id AS departure_a_id,
                departure.a_street_number AS departure_a_street_number,
                departure.a_street_name AS departure_a_street_name,
                departure.a_city AS departure_a_city,
                arrival.a_id AS arrival_a_id,
                arrival.a_street_number AS arrival_a_street_number,
                arrival.a_street_name AS arrival_a_street_name,
                arrival.a_city AS arrival_a_city,
                arrival.a_postal_code AS arrival_a_postal_code,
                departure.a_postal_code AS departure_a_postal_code
        FROM 
            uniride.ur_join 
        INNER JOIN
            uniride.ur_trip as t using (t_id)
        INNER JOIN
            uniride.ur_address departure ON t.t_address_departure_id = departure.a_id
        INNER JOIN
            uniride.ur_address arrival ON t.t_address_arrival_id = arrival.a_id
        WHERE 
            u_id=%s;
        """
    conn = connect_pg.connect()
    passenger_trips = connect_pg.get_query(conn, query, (user_id,), True)
    if not passenger_trips:
        raise TripNotFoundException()
    connect_pg.disconnect(conn)
    result_list = []

    for trip_data in passenger_trips:
        trip_dto = PassengerTripDTO(
            trip_id=trip_data['t_id'],
            departure_address=f"{trip_data['departure_a_street_number']} {trip_data['departure_a_street_name']}, {trip_data['departure_a_city']}",
            arrival_address=f"{trip_data['arrival_a_street_number']} {trip_data['arrival_a_street_name']}, {trip_data['arrival_a_city']}",
            proposed_date=str(trip_data['t_timestamp_proposed']),
            status=trip_data['t_status'],
            book_status=trip_data['j_accepted']
        )
        result_list.append(trip_dto)

    return result_list