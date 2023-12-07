"""DTO for Car BO"""

from typing import TypedDict


class DocumentVerificationDTO(TypedDict):
    """Car DTO (Data Transfer Object)"""

    id_user: int
    model: str
    licence_plate: str
    country_licence_plate: str
    color: str
    brand: str
    id_user: int
    total_places: int
