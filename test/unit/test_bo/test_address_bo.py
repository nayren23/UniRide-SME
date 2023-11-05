# test_address_bo.py

import pytest
from datetime import datetime
from uniride_sme.models.bo.address_bo import AddressBO


@pytest.fixture
def default_address() -> AddressBO:
    """Returns a standard AddressBO Object"""
    return AddressBO(
        address_id=50,
        street_number= "140",
        street_name="Rue de la Nouvelle France",
        city="Montreuil",
        postal_code="93100",
        latitude=45.1234,
        longitude=-67.5678,
        timestamp_modification=datetime.now()
    )

def test_valid_street_number(default_address: AddressBO):
    default_address.valid_street_number()

    default_address.street_number = None
    with pytest.raises(ValueError, match="street_number cannot be null"):
        default_address.valid_street_number()
    
    default_address.street_number = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaa" # Street number longer than 10 characters
    with pytest.raises(ValueError, match="street_number cannot be greater than 10"):
        default_address.valid_street_number()

def test_valid_street_name(default_address: AddressBO):
    assert default_address.valid_street_name() is True  # Valid street name

    default_address.street_name = None
    assert default_address.valid_street_name() is False  # Invalid: street_name is None

    default_address.street_name = "a" * 256  # Street name longer than 255 characters
    assert default_address.valid_street_name() is False  # Invalid: street_name too long

def test_valid_city(default_address: AddressBO):
    assert default_address.valid_city() is True  # Valid city name

    default_address.city = None
    assert default_address.valid_city() is False  # Invalid: city is None

    default_address.city = "a" * 256  # City name longer than 255 characters
    assert default_address.valid_city() is False  # Invalid: city name too long

def test_valid_postal_code(default_address: AddressBO):
    assert default_address.valid_postal_code() is True  # Valid postal code

    default_address.postal_code = None
    assert default_address.valid_postal_code() is False  # Invalid: postal_code is None

    default_address.postal_code = "123456"  # Postal code longer than 5 characters
    assert default_address.valid_postal_code() is False  # Invalid: postal_code too long

    default_address.postal_code = "1234"  # Postal code shorter than 5 characters
    assert default_address.valid_postal_code() is False  # Invalid: postal_code too short

def test_valid_latitude(default_address: AddressBO):
    assert default_address.valid_latitude() is True  # Valid latitude

    default_address.latitude = None
    assert default_address.valid_latitude() is False  # Invalid: latitude is None

    default_address.latitude = "45.1234"  # Latitude as a string
    assert default_address.valid_latitude() is False  # Invalid: latitude is not a float

def test_valid_longitude(default_address: AddressBO):
    assert default_address.valid_longitude() is True  # Valid longitude

    default_address.longitude = None
    assert default_address.valid_longitude() is False  # Invalid: longitude is None

    default_address.longitude = "-67.5678"  # Longitude as a string
    assert default_address.valid_longitude() is False  # Invalid: longitude is not a float

def test_valid_description(default_address: AddressBO):
    assert default_address.valid_description() is True  # Valid description

    default_address.description = None
    assert default_address.valid_description() is False  # Invalid: description is None

    default_address.description = "a" * 51  # Description longer than 50 characters
    assert default_address.valid_description() is False  # Invalid: description too long

def test_valid_timestamp_modification(default_address: AddressBO):
    assert default_address.valid_timestamp_modification() is True  # Valid timestamp_modification

    default_address.timestamp_modification = None
    assert default_address.valid_timestamp_modification() is False  # Invalid: timestamp_modification is None

    default_address.timestamp_modification = "2023-11-05 12:00:00"  # Not a datetime instance
    assert default_address.valid_timestamp_modification() is False  # Invalid: timestamp_modification is not a datetime instance

def test_get_latitude_longitude_from_address(default_address: AddressBO):
    default_address.get_latitude_longitude_from_address()

    assert default_address.latitude == 48.86257 # IUT de Montreuil's latitude
    assert default_address.longitude == 2.464205 # IUT de Montreuil's longitude

def test_address_exists(default_address: AddressBO):
    assert default_address.address_exists() == [] # The address shouldn't exist before we add it (because the database is empty)
    default_address.add_in_db()
    assert default_address.address_exists()[0][0] == 50 # The address should now exist