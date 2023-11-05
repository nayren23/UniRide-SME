from typing import TypedDict


class AddressDto(TypedDict):
    address_id: int
    latitude: float
    longitude: float
    nom_complet: str