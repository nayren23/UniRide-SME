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
        password_confirmation: str = None,
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

    def add_in_db(self, password_confirmation):
        """Insert the user in the database"""
        # validate values
        self.validate_login()
        self.validate_email()
        self.validate_firstname()
        self.validate_lastname()
        self.validate_gender()
        self.validate_phone_number()
        self.validate_password(password_confirmation)
        try:
            self.validate_description()
        except MissingInputException:
            pass

        # retrieve not None values
        attr_dict = {}
        for attr, value in self.__dict__.items():
            if value:
                attr_dict["u_" + attr] = value

        # format for sql query
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
            raise MissingInputException("LOGIN_MISSING")

        # check if the format is valid
        if len(self.login) > 50:
            raise InvalidInputException("LOGIN_TOO_LONG")

        regex = r"[A-Za-z0-9._-]+"
        if not re.fullmatch(regex, self.login):
            raise InvalidInputException("LOGIN_INVALID_CHARACTERS")

        # check if the login is already taken
        query = "select count(*) from uniride.ur_user where u_login = %s"
        conn = connect_pg.connect()
        count = connect_pg.get_query(conn, query, (self.login,))[0][0]
        if count:
            raise InvalidInputException("LOGIN_TAKEN")

    def validate_email(self):
        # check if exist
        if not self.student_email:
            raise MissingInputException("EMAIL_MISSING")

        # check if the format is valid
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.fullmatch(regex, self.student_email):
            raise InvalidInputException("EMAIL_INVALID_FORMAT")

        if len(self.student_email) > 254:
            raise InvalidInputException("EMAIL_TOO_LONG")

        # check if the domain is valid
        email_domain = self.student_email.split("@")[1]
        valid_domain = os.getenv("EMAIL_VALID_DOMAIN")
        if email_domain != valid_domain:
            raise InvalidInputException("EMAIL_INVALID_DOMAIN")

        # check if the email is already taken
        query = "select count(*) from uniride.ur_user where u_student_email = %s"
        conn = connect_pg.connect()
        count = connect_pg.get_query(conn, query, (self.student_email,))[0][0]
        if count:
            raise InvalidInputException("EMAIL_TAKEN")

    def _validate_name(self, name, name_type):
        # check if exist
        if not name:
            raise MissingInputException(f"{name_type}_MISSING")

        # check if the format is valid
        if len(name) > 50:
            raise InvalidInputException(f"{name_type}_TOO_LONG")

        regex = r"[A-Za-z-\s]+"
        if not re.fullmatch(regex, name):
            raise InvalidInputException(f"{name_type}_INVALID_CHARACTERS")

    def validate_firstname(self):
        self._validate_name(self.firstname, "FIRSTNAME")

    def validate_lastname(self):
        self._validate_name(self.lastname, "LASTNAME")

    def validate_gender(self):
        # check if exist
        if not self.gender:
            raise MissingInputException(f"GENDER_MISSING")

        # check if the format is valid
        if self.gender not in ("N", "H", "F"):
            raise InvalidInputException(f"GENDER_INVALID")

    def validate_phone_number(self):
        # check if exist
        if not self.phone_number:
            raise MissingInputException(f"PHONE_NUMBER_MISSING")

        # check if the format is valid
        if not (self.phone_number.isdigit() and len(self.phone_number) == 9):
            raise InvalidInputException(f"PHONE_NUMBER_INVALID")

    def validate_password(self, password_confirmation):
        # check if exist
        if not self.password:
            raise MissingInputException(f"PASSWORD_MISSING")
        if not password_confirmation:
            raise MissingInputException(f"PASSWORD_CONFIRMATION_MISSING")

        # check if password and password confirmation are equals
        if self.password != password_confirmation:
            raise InvalidInputException(f"PASSWORD_NOT_MATCHING")

        # check if the format is valid
        contains_lower_case_letter = re.search(r"[a-z]", self.password)
        contains_upper_case_letter = re.search(r"[A-Z]", self.password)
        contains_digit = re.search(r"\d", self.password)
        contains_special = re.search(r"[!@#$%^&*(),.?\":{}|<>]", self.password)
        correct_size = 8 <= len(self.password) <= 50

        if not (
            contains_lower_case_letter
            and contains_upper_case_letter
            and contains_digit
            and contains_special
            and correct_size
        ):
            raise InvalidInputException(f"PASSWORD_INVALID")

    def validate_description(self):
        # check if exist
        if not self.description:
            raise MissingInputException(f"DESCRIPTION_MISSING")

        # check if description not too long
        if len(self.description) > 500:
            raise InvalidInputException("DESCRIPTION_TOO_LONG")
