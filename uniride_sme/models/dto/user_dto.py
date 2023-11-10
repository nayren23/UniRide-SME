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
