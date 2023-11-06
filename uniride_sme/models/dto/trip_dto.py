from typing import TypedDict

class TripDto(TypedDict):
    id_trajet: int
    adresse: dict
    driver_id : int
    price: float