"""Test for book service"""
import pytest
import datetime
import psycopg2
from unittest.mock import MagicMock, Mock

from uniride_sme.service.book_service import (
    _validate_passenger_count,
    _validate_user_id,
    book_trip,
    get_booking_by_id,
    _validate_driver_id,
    _validate_response,
    _validate_booking_status,
    respond_booking,
    get_bookings,
    get_books_dtos,
)
from uniride_sme.model.dto.trip_dto import TripDetailedDTO
from uniride_sme.model.bo.book_bo import BookBO
from uniride_sme.model.dto.book_dto import BookDTO
from uniride_sme.utils.exception.exceptions import (
    MissingInputException,
    InvalidInputException,
    ForbiddenException,
)
from uniride_sme.utils.exception.book_exceptions import (
    TripAlreadyBookedException,
    BookingNotFoundException,
    BookingAlreadyRespondedException,
)


@pytest.fixture
def mock_get_trip_by_id(monkeypatch):
    """Mock get_trip_by_id"""
    mock = MagicMock()
    monkeypatch.setattr("uniride_sme.service.trip_service.get_trip_by_id", mock)
    return mock


@pytest.fixture
def mock_get_booking_by_id(monkeypatch):
    """Mock get_trip_by_id"""
    mock = MagicMock()
    monkeypatch.setattr("uniride_sme.service.book_service.get_booking_by_id", mock)
    return mock


@pytest.fixture
def mock_get_bookings(monkeypatch):
    """Mock get_trip_by_id"""
    mock = MagicMock()
    monkeypatch.setattr("uniride_sme.service.book_service.get_bookings", mock)
    return mock


def test_validate_passenger_count_missing():
    """Test _validate_passenger_count when passenger_count is missing"""
    trip = TripDetailedDTO(
        passenger_count=3,
        total_passenger_count=4,
    )
    with pytest.raises(MissingInputException) as e:
        _validate_passenger_count(trip, None)
    assert "PASSENGER_COUNT_MISSING" in str(e.value)


def test_validate_passenger_count_too_low():
    """Test _validate_passenger_count when passenger_count is too low"""
    trip = TripDetailedDTO(
        passenger_count=3,
        total_passenger_count=4,
    )
    with pytest.raises(InvalidInputException) as e:
        _validate_passenger_count(trip, 0)
    assert "PASSENGER_COUNT_TOO_LOW" in str(e.value)


def test_validate_passenger_count_too_high():
    """Test _validate_passenger_count when passenger_count is too high"""
    trip = TripDetailedDTO(
        passenger_count=3,
        total_passenger_count=4,
    )
    with pytest.raises(InvalidInputException) as e:
        _validate_passenger_count(trip, 2)
    assert "PASSENGER_COUNT_TOO_HIGH" in str(e.value)


def test_validate_passenger_count_success():
    """Test _validate_passenger_count success"""
    trip = TripDetailedDTO(
        passenger_count=3,
        total_passenger_count=4,
    )
    _validate_passenger_count(trip, 1)


def test_validate_user_id_missing():
    """Test _validate_user_id missing user id"""
    trip = TripDetailedDTO(driver_id=2)
    with pytest.raises(MissingInputException) as e:
        _validate_user_id(trip, None)
    assert "USER_ID_MISSING" in str(e.value)


def test_validate_user_id_is_driver_id():
    """Test _validate_user_id user id is the driver's id"""
    trip = TripDetailedDTO(driver_id=2)
    with pytest.raises(ForbiddenException) as e:
        _validate_user_id(trip, 2)
    assert "DRIVER_CANNOT_BOOK_HIS_OWN_TRIP" in str(e.value)


def test_validate_user_id_success():
    """Test _validate_user_id success"""
    trip = TripDetailedDTO(driver_id=2)
    _validate_user_id(trip, 1)


def test_book_trip_already_booked(mock_get_trip_by_id, mock_execute_command):
    """Test book_trip trip already booked"""
    mock_get_trip_by_id.return_value = TripDetailedDTO(
        passenger_count=3,
        total_passenger_count=4,
        driver_id=2,
    )
    mock_execute_command.side_effect = psycopg2.errors.UniqueViolation()
    with pytest.raises(TripAlreadyBookedException):
        book_trip(1, 1, 1)


def test_book_trip_success(mock_get_trip_by_id, mock_execute_command):
    """Test book_trip success"""
    mock_get_trip_by_id.return_value = TripDetailedDTO(
        passenger_count=3,
        total_passenger_count=4,
        driver_id=2,
    )
    mock_execute_command.return_value = None
    book_trip(1, 1, 1)


def test_get_booking_by_id_trip_id_missing():
    """Test get_booking_by_id success"""
    with pytest.raises(MissingInputException) as e:
        get_booking_by_id(None, 60)
    assert "TRIP_ID_MISSING" in str(e.value)


def test_get_booking_by_id_user_id_missing():
    """Test get_booking_by_id success"""
    with pytest.raises(MissingInputException) as e:
        get_booking_by_id(143, None)
    assert "USER_ID_MISSING" in str(e.value)


def test_get_booking_by_id_booking_not_found(mock_get_query):
    """Test get_booking_by_id booking not found"""
    mock_get_query.return_value = []
    with pytest.raises(BookingNotFoundException):
        get_booking_by_id(143, 60)


def test_get_booking_by_id_success(mock_get_query):
    """Test get_booking_by_id success"""
    mock_get_query.return_value = [
        psycopg2.extras.RealDictRow(
            [
                ("u_id", 143),
                ("t_id", 60),
                ("r_accepted", 1),
                ("r_passenger_count", 1),
                ("r_date_requested", datetime.datetime(2023, 12, 9, 14, 6, 37, 904962)),
            ]
        )
    ]
    expected_result = mock_get_query.return_value[0]
    result = get_booking_by_id(143, 60)
    assert result == expected_result


def test_validate_driver_id_missing():
    """Test _validate_driver_id driver_id is missing"""
    trip = TripDetailedDTO(driver_id=2)
    with pytest.raises(MissingInputException) as e:
        _validate_driver_id(trip, None)
    assert "DRIVER_ID_MISSING" in str(e.value)


def test_validate_driver_id_is_not_driver_id():
    """Test _validate_driver_id driver_id is not the driver's id"""
    trip = TripDetailedDTO(driver_id=2)
    with pytest.raises(ForbiddenException) as e:
        _validate_driver_id(trip, 1)
    assert "ONLY_DRIVER_CAN_RESPOND" in str(e.value)


def test_validate_driver_id_success():
    """Test _validate_driver_id success"""
    trip = TripDetailedDTO(driver_id=2)
    _validate_driver_id(trip, 2)


def test_validate_response_missing():
    """Test _validate_response response missing"""
    with pytest.raises(MissingInputException) as e:
        _validate_response(None)
    assert "RESPONSE_MISSING" in str(e.value)


def test_validate_response_invalid():
    """Test _validate_response response invalid"""
    with pytest.raises(InvalidInputException) as e:
        _validate_response(2)
    assert "RESPONSE_INVALID" in str(e.value)


def test_validate_response_success():
    """Test _validate_response success"""
    _validate_response(-1)


def test_validate_booking_status_already_responded():
    """Test _validate_booking_status booking already responded"""
    with pytest.raises(BookingAlreadyRespondedException):
        _validate_booking_status(1)


def test_validate_booking_status_success():
    """Test _validate_booking_status success"""
    _validate_booking_status(0)


def test_respond_booking_success(mock_get_trip_by_id, mock_get_booking_by_id, mock_execute_command):
    """Test book_trip success"""
    mock_get_trip_by_id.return_value = TripDetailedDTO(
        passenger_count=3,
        total_passenger_count=4,
        driver_id=2,
    )
    mock_get_booking_by_id.return_value = psycopg2.extras.RealDictRow(
        [
            ("u_id", 143),
            ("t_id", 60),
            ("r_accepted", 0),
            ("r_passenger_count", 1),
            ("r_date_requested", datetime.datetime(2023, 12, 9, 14, 6, 37, 904962)),
        ]
    )
    mock_execute_command.return_value = None
    respond_booking(60, 2, 143, 1)


def test_get_bookings_user_id_missing():
    """Test book_trip user_id missing"""
    with pytest.raises(MissingInputException) as e:
        get_bookings(None)
    assert "USER_ID_MISSING" in str(e.value)


def test_get_bookings_success(mock_get_query):
    """Test book_trip success"""
    mock_get_query.return_value = [
        psycopg2.extras.RealDictRow(
            [
                ("u_id", 143),
                ("t_id", 60),
                ("r_accepted", 0),
                ("r_passenger_count", 3),
                ("r_date_requested", datetime.datetime(2023, 11, 9, 14, 6, 37, 904962)),
            ]
        ),
        psycopg2.extras.RealDictRow(
            [
                ("u_id", 42),
                ("t_id", 17),
                ("r_accepted", -1),
                ("r_passenger_count", 1),
                ("r_date_requested", datetime.datetime(2023, 12, 9, 14, 4, 37, 904962)),
            ]
        ),
    ]
    expected_result = [
        BookBO(
            user_id=143,
            trip_id=60,
            accepted=0,
            passenger_count=3,
            date_requested=datetime.datetime(2023, 11, 9, 14, 6, 37, 904962),
        ),
        BookBO(
            user_id=42,
            trip_id=17,
            accepted=-1,
            passenger_count=1,
            date_requested=datetime.datetime(2023, 12, 9, 14, 4, 37, 904962),
        ),
    ]
    result = get_bookings(2)
    assert result == expected_result


def test_get_books_dtos_success(mock_get_bookings):
    """Test book_trip success"""
    mock_get_bookings.return_value = [
        BookBO(
            user_id=143,
            trip_id=60,
            accepted=0,
            passenger_count=3,
            date_requested=datetime.datetime(2023, 11, 9, 14, 6, 37, 904962),
        ),
        BookBO(
            user_id=42,
            trip_id=17,
            accepted=-1,
            passenger_count=1,
            date_requested=datetime.datetime(2023, 12, 9, 14, 4, 37, 904962),
        ),
    ]
    expected_result = [
        BookDTO(
            user_id=143,
            trip_id=60,
            accepted=0,
            passenger_count=3,
            date_requested=datetime.datetime(2023, 11, 9, 14, 6, 37, 904962),
        ),
        BookDTO(
            user_id=42,
            trip_id=17,
            accepted=-1,
            passenger_count=1,
            date_requested=datetime.datetime(2023, 12, 9, 14, 4, 37, 904962),
        ),
    ]
    result = get_books_dtos(2)
    assert result == expected_result
