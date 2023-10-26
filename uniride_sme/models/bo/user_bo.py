"""User business owner"""
import connect_pg
from models.exception.user_exceptions import (
    InvalidInputException,
    MissingInputException,
)
import re
import os


class UserBO:
    """User business owner class"""

    def __init__(
        self,
        id: int = None,
        login: str = None,
        firstname: str = None,
        lastname: str = None,
        student_email: str = None,
        password: str = None,
        gender: str = None,
        phone_number: str = None,
        description: str = None,
    ):
        self.id = id
        self.login = login
        self.firstname = firstname
        self.lastname = lastname
        self.student_email = student_email
        self.password = password
        self.gender = gender
        self.phone_number = phone_number
        self.description = description

    def add_in_db(self):
        """Insert the user in the database"""
        self.validate_login()
        self.validate_email()
        self.validate_firstname()
        self.validate_lastname()
        self.validate_gender()
        self.validate_phone_number()

        attr_dict = {}
        for attr, value in self.__dict__.items():
            if value:
                attr_dict["u_" + attr] = value

        fields = ", ".join(attr_dict.keys())
        placeholders = ", ".join(["%s"] * len(attr_dict))
        values = tuple(attr_dict.values())

        query = f"INSERT INTO uniride.ur_user ({fields}) VALUES ({placeholders}) RETURNING u_id"

        conn = connect_pg.connect()
        id = connect_pg.execute_command(conn, query, values)
        self.id = id

    def validate_login(self):
        # check if exist
        if not self.login:
            raise MissingInputException("Login missing")

        # check if the format is valid
        if len(self.login) > 50:
            raise InvalidInputException("Login invalid format : too long")
        regex = r"[A-Za-z0-9._-]+"
        if not re.fullmatch(regex, self.login):
            raise InvalidInputException(
                "Login invalid format : not allowed special characters"
            )

        # check if the login is already taken
        query = "select count(*) from uniride.ur_user where u_login = %s"

        conn = connect_pg.connect()
        count = connect_pg.get_query(conn, query, (self.login,))[0][0]
        if count:
            raise InvalidInputException("Login already taken")

    def validate_email(self):
        # check if exist
        if not self.student_email:
            raise MissingInputException("Email missing")

        # check if the format is valid
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.fullmatch(regex, self.student_email):
            raise InvalidInputException("Email invalid format")

        # check if the domain is valid
        email_domain = self.student_email.split("@")[1]
        valid_domain = os.getenv("EMAIL_VALID_DOMAIN")
        if email_domain != valid_domain:
            raise InvalidInputException("Email invalid : not a student email")

        # check if the email is already taken
        query = "select count(*) from uniride.ur_user where u_student_email = %s"
        conn = connect_pg.connect()
        count = connect_pg.get_query(conn, query, (self.student_email,))[0][0]
        if count:
            raise InvalidInputException("Email adresse already taken")

    def validate_name(self, name, name_type):
        # check if exist
        if not name:
            raise MissingInputException(f"{name_type} missing")

        # check if the format is valid
        regex = r"[A-Za-z-\s]+"
        if not re.fullmatch(regex, name):
            raise InvalidInputException(
                f"{name_type} format: not allowed special characters"
            )

    def validate_firstname(self):
        self.validate_name(self.firstname, "Firstname")

    def validate_lastname(self):
        self.validate_name(self.lastname, "Lastname")

    def validate_gender(self):
        # check if exist
        if not self.gender:
            raise MissingInputException(f"Gender is missing")

        # check if the format is valid
        if self.gender not in ("N", "H", "F"):
            raise InvalidInputException(f"Gender incorrect")

    def validate_phone_number(self):
        # check if exist
        if not self.phone_number:
            raise MissingInputException(f"Phone number is missing")

        # check if the format is valid
        if not (self.phone_number.isdigit() and len(self.phone_number) == 9):
            raise InvalidInputException(f"Phone number incorrect")
