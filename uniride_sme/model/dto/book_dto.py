"""DTO for Book BO"""

from typing import TypedDict
from uniride_sme.model.dto.trip_dto import TripShortDTO
from uniride_sme.model.dto.user_dto import UserShortDTO


class BookDTO(TypedDict):
    """Address DTO (Data Transfer Object)"""

    user: TripShortDTO
    trip: UserShortDTO
    accepted: int
    passenger_count: int
    date_requested: str
