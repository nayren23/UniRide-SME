"""DTO for Address BO"""

from typing import TypedDict


class AddressDTO(TypedDict):
    """Address DTO (Data Transfer Object)"""

    id: int
    latitude: float
    longitude: float
    address_name: str


class AddressSimpleDTO(TypedDict):
    """Address simple DTO."""

    id: int
    name: str
