"""Contains the business object of the trip"""

from datetime import datetime
from math import ceil
from typing import List

from uniride_sme import connect_pg

from uniride_sme.utils.exception.trip_exceptions import InvalidInputException, MissingInputException, TripAlreadyExistsException, TripNotFoundException

from uniride_sme.utils.exception.address_exceptions import InvalidIntermediateAddressException

from uniride_sme.utils.cartography.route_checker_factory import RouteCheckerFactory

from uniride_sme.models.dto.trip_dto import TripDTO
from uniride_sme.models.dto.address_dto import AddressDTO
from uniride_sme.utils.trip_status import TripStatus
from uniride_sme import app
from uniride_sme.models.bo.address_bo import AddressBO
from uniride_sme.models.dto.address_dto import AddressSimpleDTO


class TripBO:
    """Business object of the trip"""

    def __init__(
        self,
        trip_id: int = None,
        total_passenger_count: int = None,
        timestamp_creation=None,
        timestamp_proposed=None,
        status: int = None,  # En cours, en attente, annulé, terminé
        price: float = None,
        user_id: int = None,
        depart_address_bo: AddressBO = None,
        arrival_address_bo: AddressBO = None,
    ):
        self.id = trip_id
        self.total_passenger_count = total_passenger_count
        self.timestamp_creation = timestamp_creation
        self.timestamp_proposed = timestamp_proposed
        self.status = status
        self.price = price
        self.user_id = user_id
        self.choice_route_checker = app.config["ROUTE_CHECKER"]
        self.route_checker = RouteCheckerFactory.create_route_checker(self.choice_route_checker)

        self.departure_address = depart_address_bo
        self.arrival_address = arrival_address_bo

    def add_in_db(self):
        """Insert the trip in the database"""

        # Check if the address already exists
        self.trip_exists()
        self.departure_address.check_address_existence()
        self.arrival_address.check_address_existence()
        self.calculate_price()

        # validate values
        self.validate_total_passenger_count()
        self.validate_timestamp_proposed()
        self.validate_status()
        self.validate_price()
        self.validate_user_id()
        self.validate_address_depart_id_equals_address_arrival_id()  # i need this function to check if the trip is viable

        query = (
            f"INSERT INTO {app.config['DB_NAME']}.ur_trip (t_total_passenger_count,"
            "t_timestamp_proposed, t_status, t_price, t_user_id, t_address_depart_id, t_address_arrival_id) "
            " VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING t_id"
        )

        values = (self.total_passenger_count, self.timestamp_proposed, self.status, self.price, self.user_id, self.departure_address.id, self.arrival_address.id)

        conn = connect_pg.connect()
        trip_id = connect_pg.execute_command(conn, query, values)

        self.id = trip_id

    def validate_total_passenger_count(self):
        """Check if the total passenger count is valid"""
        if self.total_passenger_count is None:
            raise MissingInputException("TOTAL_PASSENGER_COUNT_CANNOT_BE_NULL")
        if self.total_passenger_count < 0:
            raise InvalidInputException("TOTAL_PASSENGER_COUNT_CANNOT_BE_NEGATIVE")
        if self.total_passenger_count > 10:  # TODO: change the number of seats in the car DB
            raise InvalidInputException("TOTAL_PASSENGER_COUNT_TOO_HIGH")

    def validate_timestamp_proposed(self):
        """Check if the timestamp proposed is valid"""
        if self.timestamp_proposed is None:
            raise MissingInputException("TIMESTAMP_PROPOSED_CANNOT_BE_NULL")
        try:
            datetime.strptime(self.timestamp_proposed, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise InvalidInputException("INVALID_TIMESTAMP_FORMAT") from e

    def validate_status(self):
        """Check if the status is valid"""
        if self.status is None:
            raise MissingInputException("STATUS_CANNOT_BE_NULL")
        if self.status < 0:
            raise InvalidInputException("STATUS_CANNOT_BE_NEGATIVE")

    def validate_price(self):
        """Check if the price is valid"""
        if self.price is None:
            raise MissingInputException("PRICE_CANNOT_BE_NULL")
        if self.price < 0:
            raise InvalidInputException("PRICE_CANNOT_BE_NEGATIVE")

    def validate_user_id(self):
        """Check if the user id is valid"""
        if self.user_id is None:
            raise MissingInputException("USER_ID_CANNOT_BE_NULL")
        if self.user_id < 0:
            raise InvalidInputException("USER_ID_CANNOT_BE_NEGATIVE")

    def validate_address_depart_id_equals_address_arrival_id(self):
        """Check if the address depart id is not equal to the address arrival id"""
        if self.departure_address.id == self.arrival_address.id:
            raise InvalidInputException("ADDRESS_DEPART_ID_CANNOT_BE_EQUALS_TO_ADDRESS_ARRIVAL_ID")

    def calculate_price(self):
        """Calculate the price of the trip"""

        origin = (self.departure_address.latitude, self.departure_address.longitude)
        destination = (self.arrival_address.latitude, self.arrival_address.longitude)
        distance = self.route_checker.get_distance(origin, destination)

        rate_per_km = app.config["RATE_PER_KM"]
        cost_per_km = app.config["COST_PER_KM"]
        base_rate = app.config["BASE_RATE"]

        # Calculating the total cost of the trip
        total_cost = (distance * cost_per_km) + (distance * rate_per_km)

        # The recommended fare is capped at 1.5 times the base fare
        recommended_price = min(total_cost, base_rate * 1.5)

        # Reduce the price by 20%
        final_price = ceil(recommended_price * 0.8)

        self.price = final_price

    def trip_exists(self):
        """Check if the trip with address already exists in the database"""

        query = f"""
        SELECT t_id
        FROM {app.config['DB_NAME']}.ur_trip
        WHERE t_user_id = %s AND t_address_depart_id = %s AND t_address_arrival_id = %s AND t_timestamp_proposed = %s AND t_total_passenger_count = %s
        """

        conn = connect_pg.connect()
        trip_id = connect_pg.get_query(conn, query, (self.user_id, self.departure_address.id, self.arrival_address.id, self.timestamp_proposed, self.total_passenger_count))
        connect_pg.disconnect(conn)

        if trip_id:
            raise TripAlreadyExistsException()

    def get_trips(self, departure_or_arrived_latitude, departure__or_arrived_longitude, condition_where):
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
                {app.config['DB_NAME']}.ur_trip t
            JOIN
                {app.config['DB_NAME']}.ur_address departure_address ON t.t_address_depart_id = departure_address.a_id
            JOIN
                {app.config['DB_NAME']}.ur_address arrival_address ON t.t_address_arrival_id = arrival_address.a_id
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
            conn, query, (departure_or_arrived_latitude, departure__or_arrived_longitude, self.timestamp_proposed, self.timestamp_proposed, self.total_passenger_count, TripStatus.PENDING.value)
        )
        connect_pg.disconnect(conn)

        return trips

    def get_trips_for_university_address(self, depart_address_bo, address_arrival_bo, university_address_bo):
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
        trips = self.get_trips(university_address_bo.latitude, university_address_bo.longitude, condition_where)

        available_trips: List[TripDTO] = []

        for trip in trips:
            (
                trip_id,
                total_passenger_count,
                proposed_date,
                trip_status,
                trip_price,
                user_id,
                departure_address_id,
                arrival_address_id,
                departure_latitude,
                departure_longitude,
                arrival_latitude,
                arrival_longitude,
            ) = trip

            point_depart = (departure_latitude, departure_longitude)
            point_arrivee = (arrival_latitude, arrival_longitude)

            is_viable = self.route_checker.check_if_route_is_viable(point_depart, point_arrivee, point_intermediaire_departure)

            if is_viable:
                price = trip_price * self.total_passenger_count

                address_dtos = {
                    "departure": AddressDTO(id=departure_address_id, latitude=departure_latitude, longitude=departure_longitude, nom_complet=depart_address_bo.concatene_address()),
                    "arrival": AddressDTO(id=arrival_address_id, latitude=arrival_latitude, longitude=arrival_longitude, nom_complet=address_arrival_bo.concatene_address()),
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

    def get_current_driver_trips(self):
        """Get the current trips for the driver"""

        query = f"""
            SELECT t_id, t_address_depart_id, t_address_arrival_id,t_price
            FROM {app.config['DB_NAME']}.ur_trip
            WHERE t_user_id = %s
            AND t_status = %s
        """
        values = (self.user_id, TripStatus.PENDING.value)
        conn = connect_pg.connect()
        driver_current_trips = connect_pg.get_query(conn, query, values)

        connect_pg.disconnect(conn)

        return driver_current_trips

    def format_get_current_driver_trips(self, driver_current_trips, user_id):
        available_trips = []

        for current_trip in driver_current_trips:
            t_id, t_address_depart_id, t_address_arrival_id, price = current_trip

            self.departure_address = AddressBO(address_id=t_address_depart_id)
            self.arrival_address = AddressBO(address_id=t_address_arrival_id)

            self.departure_address.check_address_existence()
            self.arrival_address.check_address_existence()

            address_dtos = {
                "departure": AddressSimpleDTO(id=self.departure_address.id, name=self.departure_address.concatene_address()),
                "arrival": AddressSimpleDTO(id=self.arrival_address.id, name=self.arrival_address.concatene_address()),
            }
            trip_dto = TripDTO(
                trip_id=t_id,
                address=address_dtos,
                driver_id=user_id,
                price=price,
            )
            available_trips.append(trip_dto)

        return available_trips

    def check_if_trip_exists(self):
        """Check if the trip exists in the database"""

        query = f"""
        SELECT *
        FROM {app.config['DB_NAME']}.ur_trip
        WHERE t_id = %s
        """

        conn = connect_pg.connect()
        trip = connect_pg.get_query(conn, query, (self.id,))
        connect_pg.disconnect(conn)

        if trip:
            self.id = (trip[0][0],)
            self.total_passenger_count = (trip[0][1],)
            self.timestamp_creation = (trip[0][2],)
            self.timestamp_proposed = (trip[0][3],)
            self.status = (trip[0][4],)
            self.price = (trip[0][5],)
            self.user_id = (trip[0][6],)
            self.departure_address.id = (trip[0][7],)
            self.arrival_address.id = trip[0][8]
            return True
        raise TripNotFoundException()

    def get_available_trips(self):
        # We check if the address is valid
        self.departure_address.check_address_exigeance()
        self.arrival_address.check_address_exigeance()

        self.departure_address.get_latitude_longitude_from_address()
        self.arrival_address.get_latitude_longitude_from_address()

        # We use the environment variables to get the university address
        university_street_number = app.config["UNIVERSITY_STREET_NUMBER"]
        university_street_name = app.config["UNIVERSITY_STREET_NAME"]
        university_city = app.config["UNIVERSITY_CITY"]
        university_postal_code = app.config["UNIVERSITY_POSTAL_CODE"]

        university_address_bo = AddressBO(
            street_number=university_street_number,
            street_name=university_street_name,
            city=university_city,
            postal_code=university_postal_code,
        )

        # We check if the address is valid
        university_address_bo.check_address_exigeance()

        university_address_bo.get_latitude_longitude_from_address()

        self.validate_total_passenger_count()
        self.validate_timestamp_proposed()

        available_trips = self.get_trips_for_university_address(self.departure_address, self.arrival_address, university_address_bo)

        return available_trips
