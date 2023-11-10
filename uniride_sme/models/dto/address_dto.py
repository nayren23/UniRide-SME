"""DTO for Address BO"""

from typing import TypedDict


class AddressDTO(TypedDict):
    """Address DTO (Data Transfer Object)"""

    address_id: int
    latitude: float
    longitude: float
    nom_complet: str
