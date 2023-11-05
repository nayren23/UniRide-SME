from typing import TypedDict

from uniride_sme.models.dto.trip_dto import TripDto

class TripsGetDto(TypedDict):
    trajet: TripDto