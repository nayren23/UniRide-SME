""" This module contains the AddressBO class. """

from datetime import datetime
import requests

from uniride_sme import connect_pg

from uniride_sme.utils.exception.address_exceptions import AddressNotFoundException, InvalidAddressException, MissingInputException, InvalidInputException

from uniride_sme import app


class AddressBO:
    """Address business object"""

    def __init__(
        self,
        address_id: str = None,
        street_number: str = None,
        street_name: str = None,
        city: str = None,
        postal_code: str = None,
        latitude: float = None,
        longitude: float = None,
        description: str = "",
        timestamp_modification=None,
    ):
        self.id = address_id
        self.street_number = street_number
        self.street_name = street_name
        self.city = city
        self.postal_code = postal_code
        self.latitude = latitude
        self.longitude = longitude
        self.description = description
        self.timestamp_modification = timestamp_modification

    def add_in_db(self):
        """Insert the address in the database"""
        existing_address_id = self.address_exists()

        # Check if the address already exists
        if existing_address_id:
            self.id = existing_address_id[0][0]
        else:
            # validate values
            self.valid_street_number()
            self.valid_street_name()
            self.valid_city()
            self.valid_postal_code()
            self.get_latitude_longitude_from_address()
            self.valid_latitude()
            self.valid_longitude()
            self.valid_description()
            # Add more validation methods as needed

            # retrieve not None values
            attr_dict = {}
            for attr, value in self.__dict__.items():
                if value:
                    attr_dict["a_" + attr] = value

            # format for sql query
            fields = ", ".join(attr_dict.keys())
            placeholders = ", ".join(["%s"] * len(attr_dict))
            values = tuple(attr_dict.values())

            query = f"INSERT INTO {app.config['DB_NAME']}.ur_address ({fields}) VALUES ({placeholders}) RETURNING a_id"

            conn = connect_pg.connect()
            address_id = connect_pg.execute_command(conn, query, values)
            self.id = address_id

    def valid_street_number(self):
        """Check if the street number is valid"""
        if self.street_number is None:
            raise InvalidInputException("STREET_NUMBER_CANNOT_BE_NULL")

    def valid_street_name(self):
        """Check if the street name is valid"""
        if self.street_name is None:
            raise InvalidInputException("STREET_NAME_CANNOT_BE_NULL")
        if len(self.street_name) > 255:
            raise InvalidInputException("STREET_NAME_CANNOT_BE_GREATER_THAN_255")

    def valid_city(self):
        """Check if the city is valid"""
        if self.city is None:
            raise InvalidInputException("CITY_CANNOT_BE_NULL")
        if len(self.city) > 255:
            raise InvalidInputException("CITY_CANNOT_BE_GREATER_THAN_255")

    def valid_postal_code(self):
        """Check if the postal code is valid"""
        if self.postal_code is None:
            raise InvalidInputException("POSTAL_CODE_CANNOT_BE_NULL")

    def valid_latitude(self):
        """Check if the latitude is valid"""
        if self.latitude is None:
            raise InvalidInputException("LATITUDE_CANNOT_BE_NULL")
        if self.latitude > 90 or self.latitude < -90:
            raise InvalidInputException("LATITUDE_CANNOT_BE_GREATER_THAN_90_OR_LESS_THAN_-90")

    def valid_longitude(self):
        """Check if the longitude is valid"""
        if self.longitude is None:
            raise InvalidInputException("LONGITUDE_CANNOT_BE_NULL")
        if self.longitude > 180 or self.longitude < -180:
            raise InvalidInputException("LONGITUDE_CANNOT_BE_GREATER_THAN_180_OR_LESS_THAN_-180")

    def valid_description(self):
        """Check if the description is valid"""
        if self.description is None:
            raise InvalidInputException("DESCRIPTION_CANNOT_BE_NULL")
        if len(self.description) > 50:
            raise InvalidInputException("DESCRIPTION_CANNOT_BE_GREATER_THAN_50")

    def valid_timestamp_modification(self):
        """Check if the timestamp modification is valid"""
        if self.timestamp_modification is None:
            raise MissingInputException("TTIMESTAMP_MODIFICATION_CANNOT_BE_NULL")
        try:
            datetime.strptime(self.timestamp_modification, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise InvalidInputException("INVALID_TIMESTAMP_FORMAT") from e

    def address_exists(self):
        """Check if the address already exists in the database"""

        query = f"""SELECT a_id
        FROM {app.config['DB_NAME']}.ur_address
        WHERE a_street_number = %s AND a_street_name = %s AND a_city = %s"""

        conn = connect_pg.connect()
        address_id = connect_pg.get_query(conn, query, (self.street_number, self.street_name, self.city))
        connect_pg.disconnect(conn)

        return address_id

    def get_latitude_longitude_from_address(self):
        """Get the latitude and longitude of the address, use the API Adresse GOUV"""

        # URL API Adresse GOUV  /search/
        url_search = "https://api-adresse.data.gouv.fr/search/"

        address = self.concatene_address()

        # Parameter for research
        params = {"q": address, "limit": 1, "autocomplete": 0}

        # We launch the request  l'API /search/
        response = requests.get(url_search, params=params, timeout=5)

        # We get the data in JSON from the response
        data = response.json()

        if data["features"] != []:
            # Get the coordonate from first adress
            self.latitude = data["features"][0]["geometry"]["coordinates"][1]
            self.longitude = data["features"][0]["geometry"]["coordinates"][0]
        else:
            raise InvalidAddressException()

    def concatene_address(self):
        """Concatene the address"""
        return str(self.street_number) + " " + self.street_name + " " + self.city + " " + str(self.postal_code)

    def check_address_existence(self):
        """Get the address from the id"""
        query = f"""
        SELECT a_street_number, a_street_name, a_city, a_postal_code, a_latitude, a_longitude
        FROM {app.config['DB_NAME']}.ur_address
        WHERE a_id = %s
        """

        conn = connect_pg.connect()
        address = connect_pg.get_query(conn, query, (self.id,))
        connect_pg.disconnect(conn)

        if address:
            self.street_number = address[0][0]
            self.street_name = address[0][1]
            self.city = address[0][2]
            self.postal_code = address[0][3]
            self.latitude = address[0][4]
            self.longitude = address[0][5]
        else:
            raise AddressNotFoundException()

    def check_address_exigeance(self):
        """Check if the address is valid"""
        self.valid_street_number()
        self.valid_street_name()
        self.valid_city()
        self.valid_postal_code()
