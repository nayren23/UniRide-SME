import dataclasses
from datetime import datetime


@dataclasses.dataclass
class UserBO:
    """User business object class"""

    id: int = None
    login: str = None
    firstname: str = None
    lastname: str = None
    student_email: str = None
    password: str = None
    gender: str = None
    phone_number: str = None
    description: str = None
    profile_picture: str = None
    timestamp_creation: datetime = None
    timestamp_modification: datetime = None
    email_verified: str = None
    status: str = None
    home_address_id: str = None
    work_address_id: str = None
    r_id: int= None
    