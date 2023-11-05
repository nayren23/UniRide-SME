from typing import TypedDict

class TripDto(TypedDict):
    id_trajet: int
    prix_par_passager: float
    adresse: dict
    driver_id : int