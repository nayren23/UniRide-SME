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
