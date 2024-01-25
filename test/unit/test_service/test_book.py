"""Test for book service"""
import datetime
from unittest.mock import MagicMock
import pytest
import psycopg2

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
    _validate_trip_availability,
    _validate_trip_started,
    _validate_booking,
    join,
    get_verification_code,
    _check_trip_already_booked,
)
from uniride_sme.model.dto.trip_dto import TripDetailedDTO, TripShortDTO
from uniride_sme.model.dto.user_dto import UserShortDTO
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


def test_trip_availability_with_wrong_status():
    """Test _validate_trip_availability with a trip having wrong status"""
    future_trip = {
        "status": 0,
        "departure_date": (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
    }

    with pytest.raises(ForbiddenException) as e:
        _validate_trip_availability(future_trip)
    assert "TRIP_NOT_AVAILABLE" in str(e.value)


def test_trip_availability_with_past_trip():
    """Test _validate_trip_availability with a past trip"""
    past_trip = {
        "status": 1,
        "departure_date": (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
    }

    with pytest.raises(ForbiddenException) as e:
        _validate_trip_availability(past_trip)
    assert "TRIP_NOT_AVAILABLE" in str(e.value)


def test_trip_availability_success():
    """Test _validate_trip_availability success"""
    future_trip = {
        "status": 1,
        "departure_date": (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
    }
    _validate_trip_availability(future_trip)


def test_check_trip_already_booked_uncanceled_booking(mock_get_query):
    """Test _check_trip_already_booked with an uncanceled booking"""
    mock_get_query.return_value = [{"j_accepted": 1}]

    with pytest.raises(TripAlreadyBookedException):
        _check_trip_already_booked(1, 1)


def test_check_trip_already_booked_more_than_three_canceled_booking(mock_get_query):
    """Test _check_trip_already_booked with more than three canceled bookings"""
    mock_get_query.return_value = [{"j_accepted": -2}, {"j_accepted": -2}, {"j_accepted": -2}, {"j_accepted": -2}]

    with pytest.raises(ForbiddenException, match="BOOKED_TOO_MANY_TIMES"):
        _check_trip_already_booked(1, 1)


def test_check_trip_already_booked_less_than_four_canceled_booking(mock_get_query):
    """Test _check_trip_already_booked with more than three canceled bookings"""
    mock_get_query.return_value = [{"j_accepted": -2}, {"j_accepted": -2}, {"j_accepted": -2}]
    _check_trip_already_booked(1, 1)


def test_check_trip_already_booked_not_booked(mock_get_query):
    """Test _check_trip_already_booked with no booking"""
    mock_get_query.return_value = []
    _check_trip_already_booked(1, 1)


def test_book_trip_already_booked(mock_get_trip_by_id, mock_get_query):
    """Test book_trip trip already booked"""
    mock_get_query.return_value = [{"j_accepted": 1}]

    mock_get_trip_by_id.return_value = TripDetailedDTO(
        status=1,
        passenger_count=3,
        total_passenger_count=4,
        driver_id=2,
        departure_date=str(datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(days=1)),
    )
    with pytest.raises(TripAlreadyBookedException):
        book_trip(1, 1, 1)


def test_book_trip_trip_started(mock_get_trip_by_id):
    """Test book_trip trip already booked"""
    # status error
    mock_get_trip_by_id.return_value = TripDetailedDTO(
        status=1,
        passenger_count=3,
        total_passenger_count=4,
        driver_id=2,
        departure_date="2024-01-09 09:00:00",
    )

    with pytest.raises(ForbiddenException):
        book_trip(1, 1, 1)

    # departure date error
    mock_get_trip_by_id.return_value = TripDetailedDTO(
        status=4,
        passenger_count=3,
        total_passenger_count=4,
        driver_id=2,
        departure_date="2024-01-09 09:00:00",
    )

    with pytest.raises(ForbiddenException):
        book_trip(1, 1, 1)


def test_book_trip_success(mock_get_trip_by_id, mock_execute_command):
    """Test book_trip success"""
    mock_get_trip_by_id.return_value = TripDetailedDTO(
        status=1,
        passenger_count=3,
        total_passenger_count=4,
        driver_id=2,
        departure_date=str(datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(days=1)),
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
                ("j_accepted", 1),
                ("j_passenger_count", 1),
                ("j_joined", False),
                ("j_date_requested", datetime.datetime(2023, 12, 9, 14, 6, 37, 904962)),
                ("j_verification_code", 12345),
            ]
        )
    ]
    expected_result = BookBO(
        user_id=143,
        trip_id=60,
        accepted=1,
        passenger_count=1,
        joined=False,
        date_requested=datetime.datetime(2023, 12, 9, 14, 6, 37, 904962),
        verification_code=12345,
    )
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
        status=1,
        departure_date=str(datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(days=1)),
    )
    mock_get_booking_by_id.return_value = BookBO(
        user_id=143,
        trip_id=60,
        accepted=0,
        passenger_count=1,
        date_requested=datetime.datetime(2023, 12, 9, 14, 6, 37, 904962),
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
                ("j_accepted", 1),
                ("j_passenger_count", 3),
                ("j_date_requested", datetime.datetime(2023, 12, 8, 11, 11, 13, 479329)),
                ("t_id", 15),
                ("t_timestamp_proposed", datetime.datetime(2023, 12, 6, 16, 22)),
                ("departure_a_id", 1),
                ("departure_a_street_number", "8"),
                ("departure_a_street_name", "Rue d'Amsterdam"),
                ("departure_a_city", "Paris"),
                ("departure_a_postal_code", "75008"),
                ("arrival_a_id", 2),
                ("arrival_a_street_number", "140"),
                ("arrival_a_street_name", "Rue de la Nouvelle France"),
                ("arrival_a_city", "Montreuil"),
                ("arrival_a_postal_code", "93100"),
                ("u_id", 92),
                ("u_firstname", "test"),
                ("u_lastname", "test"),
                ("u_profile_picture", None),
            ]
        )
    ]
    expected_result = [
        BookDTO(
            user=UserShortDTO(
                id=92,
                firstname="test",
                lastname="test",
                profile_picture="",
            ),
            trip=TripShortDTO(
                trip_id=15,
                departure_date=datetime.datetime(2023, 12, 6, 16, 22),
                departure_address="8 Rue d'Amsterdam, Paris, 75008",
                arrival_address="140 Rue de la Nouvelle France, Montreuil, 93100",
            ),
            accepted=1,
            passenger_count=3,
            date_requested=datetime.datetime(2023, 12, 8, 11, 11, 13, 479329),
        ),
    ]
    result = get_bookings(2)
    assert result == expected_result


def test_validate_trip_started_with_started_trip():
    """Test _validate_trip_started with a trip that has started"""
    started_trip = {"status": 4}
    _validate_trip_started(started_trip)


def test_validate_trip_started_with_invalid_status():
    """Test _validate_trip_started with invalid status"""
    invalid_trip = {"status": 1}

    with pytest.raises(ForbiddenException) as e:
        _validate_trip_started(invalid_trip)
    assert "TRIP_NOT_STARTED" in str(e.value)


def test_validate_booking_unaccepted():
    """Test _validate_booking with an unaccepted booking"""
    unaccepted_booking = BookBO(accepted=0, joined=False, verification_code=12345)
    verification_code = 12345

    with pytest.raises(ForbiddenException) as e:
        _validate_booking(unaccepted_booking, verification_code)
    assert "BOOKING_NOT_ACCEPTED" in str(e.value)


def test_validate_booking_invalid_verification_code():
    """Test _validate_booking with an invalid verification code"""
    booking = BookBO(accepted=1, joined=False, verification_code=12345)
    invalid_verification_code = 54321

    with pytest.raises(ForbiddenException) as e:
        _validate_booking(booking, invalid_verification_code)
    assert "INVALID_VERIFICATION_CODE" in str(e.value)


def test_validate_booking_passenger_already_joined():
    """Test _validate_booking with the passenger already joined"""
    booking = BookBO(accepted=1, joined=True, verification_code=12345)
    with pytest.raises(ForbiddenException) as e:
        _validate_booking(booking, 12345)
    assert "PASSENGER_AlREADY_JOINED" in str(e.value)


def test_validate_booking_success():
    """Test _validate_booking success"""
    valid_booking = BookBO(accepted=1, joined=False, verification_code=12345)
    verification_code = 12345
    _validate_booking(valid_booking, verification_code)


def test_join_success(mock_get_booking_by_id, mock_get_trip_by_id):
    """Test join success"""
    mock_get_booking_by_id.return_value = BookBO(accepted=1, joined=False, verification_code=12345)
    mock_get_trip_by_id.return_value = {"status": 4, "driver_id": 1}
    join(1, 1, 2, 12345)


def test_get_verification_code_missing_trip_id():
    """Test get_verification_code with missing trip_id"""
    with pytest.raises(MissingInputException) as e:
        get_verification_code(None, 1)
    assert "TRIP_ID_MISSING" in str(e.value)


def test_get_verification_code_status_invalid(mock_get_trip_by_id):
    """Test get_verification_code with invalid status"""
    mock_get_trip_by_id.return_value = {"status": 1}
    with pytest.raises(ForbiddenException) as e:
        get_verification_code(1, 1)
    assert "TRIP_NOT_STARTED" in str(e.value)


def test_get_verification_code_missing_user_id(mock_get_trip_by_id):
    """Test get_verification_code with missing user_id"""
    mock_get_trip_by_id.return_value = {"status": 4}
    with pytest.raises(MissingInputException) as e:
        get_verification_code(1, None)
    assert "USER_ID_MISSING" in str(e.value)


def test_get_verification_code_booking_not_found(mock_get_trip_by_id, mock_get_query):
    """Test get_verification_code with booking not found"""
    mock_get_trip_by_id.return_value = {"status": 4}
    mock_get_query.return_value = None
    with pytest.raises(BookingNotFoundException):
        get_verification_code(1, 1)


def test_get_verification_code_unaccepted_booking(mock_get_trip_by_id, mock_get_query):
    """Test get_verification_code with booking not accepted"""
    mock_get_trip_by_id.return_value = {"status": 4}
    mock_get_query.return_value = [{"j_accepted": 0, "j_verification_code": 12345}]
    with pytest.raises(ForbiddenException):
        get_verification_code(1, 1)


def test_get_verification_code_success(mock_get_trip_by_id, mock_get_query):
    """Test get_verification_code successfully retrieves the verification code"""
    mock_get_trip_by_id.return_value = {"status": 4}
    expected_verification_code = 12345
    mock_get_query.return_value = [{"j_accepted": 1, "j_verification_code": expected_verification_code}]
    actual_verification_code = get_verification_code(1, 1)
    assert actual_verification_code == expected_verification_code
