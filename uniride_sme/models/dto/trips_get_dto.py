"""DTO for Trip BO"""

from typing import TypedDict

from uniride_sme.models.dto.trip_dto import TripDTO


class TripsGetDto(TypedDict):
    """TripsGetDto"""

    trip: TripDTO
