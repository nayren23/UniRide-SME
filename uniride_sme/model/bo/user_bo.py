"""User business object module"""
import dataclasses
from datetime import datetime


@dataclasses.dataclass
class UserBO:  # pylint: disable=too-many-instance-attributes
    """User business object class"""

    def __init__(  # pylint: disable=too-many-arguments, too-many-locals
        self,
        u_id: int = None,
        u_login: str = None,
        u_firstname: str = None,
        u_lastname: str = None,
        u_student_email: str = None,
        u_password: str = None,
        u_gender: str = None,
        u_phone_number: str = None,
        u_description: str = None,
        u_profile_picture: str = None,
        u_timestamp_creation: datetime = None,
        u_timestamp_modification: datetime = None,
        u_email_verified: str = None,
        u_status: str = None,
        u_home_address_id: str = None,
        u_work_address_id: str = None,
    ):
        self.u_id = u_id
        self.u_login = u_login
        self.u_firstname = u_firstname
        self.u_lastname = u_lastname
        self.u_student_email = u_student_email
        self.u_password = u_password
        self.u_gender = u_gender
        self.u_phone_number = u_phone_number
        self.u_description = u_description
        self.u_profile_picture = u_profile_picture
        self.u_timestamp_creation = u_timestamp_creation
        self.u_timestamp_modification = u_timestamp_modification
        self.u_email_verified = u_email_verified
        self.u_status = u_status
        self.u_home_address_id = u_home_address_id
        self.u_work_address_id = u_work_address_id
