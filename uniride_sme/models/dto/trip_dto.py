"""DTO for Trip BO"""
from typing import TypedDict


class TripDTO(TypedDict):
    """Trip DTO (Data Transfer Object)"""

    id_trajet: int
    adresse: dict
    driver_id: int
    price: float
    proposed_date: str
    total_passenger_count: int
