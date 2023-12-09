"""DTO for Book BO"""

from typing import TypedDict


class BookDTO(TypedDict):
    """Address DTO (Data Transfer Object)"""

    user_id: int
    trip_id: int
    accepted: int
    passenger_count: int
    date_requested: str
