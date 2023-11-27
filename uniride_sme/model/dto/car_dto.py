"""DTO for Car BO"""

from typing import TypedDict


class CarDTO(TypedDict):
    """Car DTO (Data Transfer Object)"""

    id_car: int
    moderl: str
    licence_plate: str
    country_licence_plate: str
    color: str
    brand: str
    id_user: int

