"""DTO for UserBO"""
from typing import TypedDict


class UserInfosDTO(TypedDict):
    """DTO for user's informations"""

    login: str
    student_email: str
    firstname: str
    lastname: str
    gender: str
    phone_number: str
    description: str


class InformationsVerifiedDTO(TypedDict):
    """DTO to check if user's informations are verified"""

    email_verified: bool
    license_verified: bool
    id_card_verified: bool
    school_certificate_verified: bool
