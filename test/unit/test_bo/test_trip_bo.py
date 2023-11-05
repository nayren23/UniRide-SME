# test_trip_bo.py

import pytest

from datetime import datetime, timedelta
from uniride_sme.models.bo.trip_bo import TripBO
from uniride_sme.models.bo.address_bo import AddressBO

from uniride_sme.models.exception.trip_exceptions import (
    InvalidInputException,
    MissingInputException,
)

@pytest.fixture
def default_trip():
    """Returns a standard TripBO Object"""
    return TripBO(
        25,
        3,
        datetime.now(),
        datetime.now() + timedelta(days=2),
        status=0,
        price=5,
        user_id=1,
        address_depart_id=10,
        address_arrival_id=11
    )

@pytest.fixture(scope="module", autouse=True)
def add_addresses():
    ad_dprt = AddressBO(
        address_id=10,
        street_number= "80",
        street_name="Bd Jean Jaurès",
        city="Clichy",
        postal_code="92110"
    )

    ad_arr = AddressBO(
        address_id=11,
        street_number= "13",
        street_name="Rue d'Amsterdam",
        city="Paris",
        postal_code="75008"
    )

    ad_dprt.add_in_db()
    ad_arr.add_in_db()

def test_validate_total_passenger_count(default_trip):
    default_trip.validate_total_passenger_count()
    default_trip.total_passenger_count = None
    with pytest.raises(MissingInputException):
        default_trip.validate_total_passenger_count()

    default_trip.total_passenger_count = -1 # negative total_passenger_count
    with pytest.raises(InvalidInputException):
        default_trip.validate_total_passenger_count()
    
    default_trip.total_passenger_count = 15 # total_passenger_count over the limit
    with pytest.raises(InvalidInputException):
        default_trip.validate_total_passenger_count()

def test_validate_timestamp_proposed(default_trip):
    assert default_trip.validate_timestamp_proposed() is True
    default_trip.timestamp_proposed = "2023-11-04"
    assert default_trip.validate_timestamp_proposed() is False

def test_validate_status(default_trip):
    default_trip.validate_status()

    default_trip.status = None
    with pytest.raises(MissingInputException):
        default_trip.validate_status()
    
    default_trip.status = -1 # negative status
    with pytest.raises(InvalidInputException):
        default_trip.validate_status()

def test_validate_price(default_trip):
    default_trip.validate_price()

    default_trip.price = None
    with pytest.raises(MissingInputException):
        default_trip.validate_price()
    
    default_trip.price = -50 # negative price
    with pytest.raises(InvalidInputException):
        default_trip.validate_price()

def test_validate_user_id(default_trip):
    default_trip.validate_user_id()

    default_trip.user_id = None
    with pytest.raises(MissingInputException):
        default_trip.validate_user_id()
    
    default_trip.user_id = -5  # negative user_id
    with pytest.raises(InvalidInputException):
        default_trip.validate_user_id()

def test_validate_address_depart_id(default_trip):
    default_trip.validate_address_depart_id()

    default_trip.address_depart_id = None
    with pytest.raises(MissingInputException):
        default_trip.validate_address_depart_id()
    
    default_trip.address_depart_id = -5  # negative address_depart_id
    with pytest.raises(InvalidInputException):
        default_trip.validate_address_depart_id()

def test_validate_address_arrival_id(default_trip):
    default_trip.validate_address_arrival_id()

    default_trip.address_arrival_id = None
    with pytest.raises(MissingInputException):
        default_trip.validate_address_arrival_id()
    
    default_trip.address_arrival_id = -5  # negative address_arrival_id
    with pytest.raises(InvalidInputException):
        default_trip.validate_address_arrival_id()

def test_validate_address_depart_id_equals_address_arrival_id(default_trip):
    default_trip.validate_address_depart_id_equals_address_arrival_id()

    default_trip.address_depart_id = default_trip.address_arrival_id
    with pytest.raises(InvalidInputException):
        default_trip.validate_address_depart_id_equals_address_arrival_id()

def test_trip_exists(default_trip):
    default_trip.add_in_db()

    assert default_trip.trip_exists()[0][0] == default_trip.id
