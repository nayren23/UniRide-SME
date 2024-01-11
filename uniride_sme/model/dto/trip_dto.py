"""DTO for Trip BO"""
from typing import TypedDict


class TripDTO(TypedDict):
    """Trip DTO (Data Transfer Object)"""

    trip_id: int
    address: dict
    driver_id: int
    price: float
    proposed_date: str
    total_passenger_count: int


class TripDetailedDTO(TypedDict):
    """Trip Detailed DTO (Data Transfer Object)"""

    trip_id: int
    address: dict
    driver_id: int
    price: float
    departure_date: str
    arrival_date: str
    passenger_count: int
    total_passenger_count: int
    status: int


class TripShortDTO(TypedDict):
    """Trip DTO (Data Transfer Object)"""

    trip_id: int
    departure_address: str
    arrival_address: str
    departure_date: str


class TripStatusDTO(TypedDict):
    """Trip Status DTO (Data Transfer Object)"""

    trip_pending: int
    trip_canceled: int
    trip_completed: int
    trip_oncourse: int


class PassengerTripDTO(TypedDict):
    """Passenger Trip DTO (Data Transfer Object)"""

    trip_id: int
    departure_address: str
    arrival_address: str
    proposed_date: str
    status: int
    book_status: int
