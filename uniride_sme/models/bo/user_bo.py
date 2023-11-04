"""User business owner"""
import re
import os
import bcrypt

from uniride_sme import app
from uniride_sme import connect_pg
from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,
    MissingInputException,
)

from uniride_sme.utils.exception.user_exceptions import (
    UserNotFoundException,
    PasswordIncorrectException,
)


class UserBO:
    """User business owner class"""

    def __init__(
        self,
        user_id: int = None,
        login: str = None,
        firstname: str = None,
        lastname: str = None,
        student_email: str = None,
        password: str = None,
        gender: str = None,
        phone_number: str = None,
        description: str = None,
    ):
        self.u_id = user_id
        self.u_login = login
        self.u_firstname = firstname
        self.u_lastname = lastname
        self.u_student_email = student_email
        self.u_password = password
        self.u_gender = gender
        self.u_phone_number = phone_number
        self.u_description = description

    def get_from_db(self):
        """Get user infos from db"""
        if not self.u_id:
            raise MissingInputException("USER_ID_MISSING")

        query = "select * from uniride.ur_user where u_id = %s"
        conn = connect_pg.connect()
        infos = connect_pg.get_query(conn, query, (self.u_id,), True)
        if not infos:
            raise UserNotFoundException()
        for key in infos[0]:
            setattr(self, key, infos[0][key])

    def add_in_db(self, password_confirmation):
        """Insert the user in the database"""
        # validate values
        self.validate_login()
        self.validate_student_email()
        self.validate_firstname()
        self.validate_lastname()
        self.validate_gender()
        self.validate_phone_number()
        self.validate_description()
        self.validate_password(password_confirmation)

        self._hash_password()

        # retrieve not None values
        self.u_id = None
        attr_dict = {}
        for attr, value in self.__dict__.items():
            if value:
                attr_dict[attr] = value

        # format for sql query
        fields = ", ".join(attr_dict.keys())
        placeholders = ", ".join(["%s"] * len(attr_dict))
        values = tuple(attr_dict.values())

        query = f"INSERT INTO uniride.ur_user ({fields}) VALUES ({placeholders}) RETURNING u_id"

        conn = connect_pg.connect()
        user_id = connect_pg.execute_command(conn, query, values)
        self.u_id = user_id

    def validate_login(self):
        """Check if the login is valid"""

        # check if exist
        if not self.u_login:
            raise MissingInputException("LOGIN_MISSING")

        # check if the format is valid
        if len(self.u_login) > 50:
            raise InvalidInputException("LOGIN_TOO_LONG")

        regex = r"[A-Za-z0-9._-]+"
        if not re.fullmatch(regex, self.u_login):
            raise InvalidInputException("LOGIN_INVALID_CHARACTERS")

        # check if the login is already taken
        query = "select count(*) from uniride.ur_user where u_login = %s"
        conn = connect_pg.connect()
        count = connect_pg.get_query(conn, query, (self.u_login,))[0][0]
        if count:
            raise InvalidInputException("LOGIN_TAKEN")

    def validate_student_email(self):
        """Check if the email is valid"""

        # check if exist
        if not self.u_student_email:
            raise MissingInputException("EMAIL_MISSING")

        # check if the format is valid
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.fullmatch(regex, self.u_student_email):
            raise InvalidInputException("EMAIL_INVALID_FORMAT")

        if len(self.u_student_email) > 254:
            raise InvalidInputException("EMAIL_TOO_LONG")

        # check if the domain is valid
        email_domain = self.u_student_email.split("@")[1]
        valid_domain = os.getenv("UNIVERSITY_EMAIL_DOMAIN")
        if email_domain != valid_domain:
            raise InvalidInputException("EMAIL_INVALID_DOMAIN")

        # check if the email is already taken
        query = "select count(*) from uniride.ur_user where u_student_email = %s"
        conn = connect_pg.connect()
        count = connect_pg.get_query(conn, query, (self.u_student_email,))[0][0]
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
        """Check if the firstname is valid"""

        self._validate_name(self.u_firstname, "FIRSTNAME")

    def validate_lastname(self):
        """Check if the lastname is valid"""

        self._validate_name(self.u_lastname, "LASTNAME")

    def validate_gender(self):
        """Check if the gender is valid"""

        # check if exist
        if not self.u_gender:
            raise MissingInputException("GENDER_MISSING")

        # check if the format is valid
        if self.u_gender not in ("N", "H", "F"):
            raise InvalidInputException("GENDER_INVALID")

    def validate_phone_number(self):
        """Check if the phone number is valid"""
        # check if the format is valid
        if self.u_phone_number and not (
            self.u_phone_number.isdigit() and len(self.u_phone_number) == 9
        ):
            raise InvalidInputException("PHONE_NUMBER_INVALID")

    def validate_description(self):
        """Check if the description is valid"""
        # check if description not too long
        if self.u_description and len(self.u_description) > 500:
            raise InvalidInputException("DESCRIPTION_TOO_LONG")

    def validate_password(self, password_confirmation):
        """Check if the password is valid"""

        # check if exist
        if not self.u_password:
            raise MissingInputException("PASSWORD_MISSING")
        if not password_confirmation:
            raise MissingInputException("PASSWORD_CONFIRMATION_MISSING")

        # check if the format is valid
        contains_lower_case_letter = re.search(r"[a-z]", self.u_password)
        contains_upper_case_letter = re.search(r"[A-Z]", self.u_password)
        contains_digit = re.search(r"\d", self.u_password)
        contains_special = re.search(r"[!@#$%^&*(),.?\":{}|<>]", self.u_password)
        correct_size = 8 <= len(self.u_password) <= 50

        if not (
            contains_lower_case_letter
            and contains_upper_case_letter
            and contains_digit
            and contains_special
            and correct_size
        ):
            raise InvalidInputException("PASSWORD_INVALID")

        # check if password and password confirmation are equals
        if self.u_password != password_confirmation:
            raise InvalidInputException("PASSWORD_NOT_MATCHING")

    def _hash_password(self):
        """Hash the password"""
        salt = app.config["SECURITY_PASSWORD_SALT"]
        # convert to bytes
        salt = salt.encode("utf8")
        self.u_password = self.u_password.encode("utf8")
        self.u_password = bcrypt.hashpw(self.u_password, salt)
        # convert back to string
        self.u_password = str(self.u_password, "utf8")

    def _verify_password(self, hashed_password):
        """Verify the password is correct"""
        return bcrypt.checkpw(
            self.u_password.encode("utf8"),
            hashed_password.encode("utf8"),
        )

    def verify_student_email(
        self,
    ):
        """Verify the student email"""
        # check if exist
        if not self.u_student_email:
            raise MissingInputException("EMAIL_MISSING")

        query = (
            "select u_email_verified from uniride.ur_user where u_student_email = %s"
        )
        conn = connect_pg.connect()
        email_verified = connect_pg.get_query(conn, query, (self.u_student_email,))
        # check if the email belongs to a user
        if not email_verified:
            raise InvalidInputException("EMAIL_NOT_OWNED")
        # check if the email is already verified
        if email_verified[0][0]:
            raise InvalidInputException("EMAIL_ALREADY_VERIFIED")

        query = "update uniride.ur_user set u_email_verified=True where u_student_email = %s"
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, (self.u_student_email,))

    def authentificate(self):
        """Verify the login and password"""
        # check if exist
        if not self.u_login:
            raise MissingInputException("LOGIN_MISSING")
        if not self.u_password:
            raise MissingInputException("PASSWORD_MISSING")

        query = "select u_password from uniride.ur_user where u_login = %s"
        conn = connect_pg.connect()
        password = connect_pg.get_query(conn, query, (self.u_login,))

        if not password:
            raise UserNotFoundException()

        if not self._verify_password(password[0][0]):
            raise PasswordIncorrectException()
