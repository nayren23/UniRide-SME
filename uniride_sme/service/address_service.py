"""Address service module"""

from datetime import datetime
import requests

from uniride_sme import connect_pg
from uniride_sme.model.bo.address_bo import AddressBO
from uniride_sme.utils.exception.address_exceptions import (
    AddressNotFoundException,
    InvalidAddressException,
)
from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,
    MissingInputException,
)


def add_address(address: AddressBO) -> AddressBO:
    """Insert the address in the database"""
    existing_address_id = address_exists(address.street_number, address.street_name, address.city)

    # Check if the address already exists
    if existing_address_id:
        address.id = existing_address_id
    else:
        # Validate values
        valid_street_number(address.street_number)
        valid_street_name(address.street_name)
        valid_city(address.city)
        valid_postal_code(address.postal_code)
        set_latitude_longitude_from_address(address)
        valid_latitude(address.latitude)
        valid_longitude(address.longitude)
        # Add more validation methods if needed

        # retrieve not None values
        attr_dict = {}
        for attr, value in address.__dict__.items():
            if value:
                attr_dict["a_" + attr] = value

        # format for sql query
        fields = ", ".join(attr_dict.keys())
        placeholders = ", ".join(["%s"] * len(attr_dict))
        values = tuple(attr_dict.values())

        query = f"INSERT INTO uniride.ur_address ({fields}) VALUES ({placeholders}) RETURNING a_id"

        conn = connect_pg.connect()
        address_id = connect_pg.execute_command(conn, query, values)
        address.id = address_id
    return address


def valid_street_number(street_number) -> None:
    """Check if the street number is valid"""
    if not street_number:
        raise InvalidInputException("STREET_NUMBER_CANNOT_BE_NULL")


def valid_street_name(street_name) -> None:
    """Check if the street name is valid"""
    if not street_name:
        raise InvalidInputException("STREET_NAME_CANNOT_BE_NULL")
    if len(street_name) > 255:
        raise InvalidInputException("STREET_NAME_CANNOT_BE_GREATER_THAN_255")


def valid_city(city) -> None:
    """Check if the city is valid"""
    if not city:
        raise InvalidInputException("CITY_CANNOT_BE_NULL")
    if len(city) > 255:
        raise InvalidInputException("CITY_CANNOT_BE_GREATER_THAN_255")


def valid_postal_code(postal_code) -> None:
    """Check if the postal code is valid"""
    if not postal_code:
        raise InvalidInputException("POSTAL_CODE_CANNOT_BE_NULL")


def valid_latitude(latitude) -> None:
    """Check if the latitude is valid"""
    if not latitude:
        raise InvalidInputException("LATITUDE_CANNOT_BE_NULL")
    if latitude > 90 or latitude < -90:
        raise InvalidInputException("LATITUDE_CANNOT_BE_GREATER_THAN_90_OR_LESS_THAN_-90")


def valid_longitude(longitude) -> None:
    """Check if the longitude is valid"""
    if not longitude:
        raise InvalidInputException("LONGITUDE_CANNOT_BE_NULL")
    if longitude > 180 or longitude < -180:
        raise InvalidInputException("LONGITUDE_CANNOT_BE_GREATER_THAN_180_OR_LESS_THAN_-180")


def valid_timestamp_modification(timestamp_modification) -> None:
    """Check if the timestamp modification is valid"""
    if timestamp_modification is None:
        raise MissingInputException("TTIMESTAMP_MODIFICATION_CANNOT_BE_NULL")
    try:
        datetime.strptime(timestamp_modification, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        raise InvalidInputException("INVALID_TIMESTAMP_FORMAT") from e


def address_exists(street_number, street_name, city) -> int:
    """Check if the address already exists in the database"""

    query = """SELECT a_id
    FROM uniride.ur_address
    WHERE a_street_number = %s AND a_street_name = %s AND a_city = %s"""

    conn = connect_pg.connect()
    address_id = connect_pg.get_query(conn, query, (street_number, street_name, city))
    connect_pg.disconnect(conn)
    if address_id:
        return address_id[0][0]
    return None


def set_latitude_longitude_from_address(address_bo: AddressBO) -> None:
    """Get the latitude and longitude of the address, use the API Adresse GOUV"""

    # URL API Adresse GOUV  /search/
    url_search = "https://api-adresse.data.gouv.fr/search/"

    address = address_bo.get_full_address()

    # Parameter for research
    params = {"q": address, "limit": 1, "autocomplete": 0}

    # We launch the request  l'API /search/
    response = requests.get(url_search, params=params, timeout=5)

    # We get the data in JSON from the response
    data = response.json()

    if data["features"] != []:
        # Get the coordonate from first adress
        address_bo.latitude = data["features"][0]["geometry"]["coordinates"][1]
        address_bo.longitude = data["features"][0]["geometry"]["coordinates"][0]
    else:
        raise InvalidAddressException()


def check_address_existence(address_bo: AddressBO) -> None:
    """Get the address from the id"""

    validate_address_departure_id(address_bo.id)

    query = """
    SELECT a_street_number, a_street_name, a_city, a_postal_code, a_latitude, a_longitude
    FROM uniride.ur_address
    WHERE a_id = %s
    """

    conn = connect_pg.connect()
    address = connect_pg.get_query(conn, query, (address_bo.id,))
    connect_pg.disconnect(conn)

    if address:
        address_bo.street_number = address[0][0]
        address_bo.street_name = address[0][1]
        address_bo.city = address[0][2]
        address_bo.postal_code = address[0][3]
        address_bo.latitude = address[0][4]
        address_bo.longitude = address[0][5]
    else:
        raise AddressNotFoundException()


def check_address_exigeance(address: AddressBO) -> None:
    """Check if the address is valid"""
    valid_street_number(address.street_number)
    valid_street_name(address.street_name)
    valid_city(address.city)
    valid_postal_code(address.postal_code)


def validate_address_departure_id(id_address) -> None:
    """Check if the address departure id is valid"""
    if id_address is None:
        raise MissingInputException("ADDRESS_ID_CANNOT_BE_NULL")
    if id_address < 0:
        raise InvalidInputException("ADDRESS_ID_CANNOT_BE_NEGATIVE")
