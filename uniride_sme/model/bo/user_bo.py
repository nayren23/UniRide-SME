import dataclasses
from datetime import datetime

@dataclasses.dataclass
class UserBO:
    """User business object class"""

    u_id: int = None
    u_login: str = None
    u_firstname: str = None
    u_lastname: str = None
    u_student_email: str = None
    u_password: str = None
    u_gender: str = None
    u_phone_number: str = None
    u_description: str = None
    u_profile_picture: str = None
    u_timestamp_creation: datetime = None
    u_timestamp_modification: datetime = None
    u_email_verified: str = None
    u_status: str = None
    u_home_address_id: str = None
    u_work_address_id: str = None

    def __init__(self, **kwargs):
        for field in dataclasses.fields(self):
            setattr(self, field.name, kwargs.get(field.name, field.default))
