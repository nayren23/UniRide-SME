"""DTO for Address BO"""
from typing import TypedDict


class AddressSimpleDTO(TypedDict):
    """Address simple DTO."""

    id: int
    name: str
