"""User business owner"""
import re
import os
import bcrypt

from uniride_sme import app
from uniride_sme import connect_pg
from uniride_sme.utils.file import save_file, delete_file
from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,
    MissingInputException,
    InternalServerErrorException,
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

        if self.u_id:
            self.get_from_db()

    def get_from_db(self):
        """Get user infos from db"""
        if not self.u_id and not self.u_login:
            raise MissingInputException("IDENTIFIER_MISSING")

        if self.u_id:
            query = "select * from uniride.ur_user where u_id = %s"
            params = (self.u_id,)
        else:
            query = "select * from uniride.ur_user where u_login = %s"
            params = (self.u_login,)

        conn = connect_pg.connect()
        infos = connect_pg.get_query(conn, query, params, True)
        if not infos:
            raise UserNotFoundException()
        for key in infos[0]:
            setattr(self, key, infos[0][key])

        # get documents
        query = "select * from uniride.ur_documents where u_id = %s"
        params = (self.u_id,)

        conn = connect_pg.connect()
        infos = connect_pg.get_query(conn, query, params, True)
        for key in infos[0]:
            setattr(self, key, infos[0][key])

        # get document verification
        query = "select * from uniride.ur_document_verification where u_id = %s"
        params = (self.u_id,)

        conn = connect_pg.connect()
        infos = connect_pg.get_query(conn, query, params, True)
        for key in infos[0]:
            setattr(self, key, infos[0][key])

    def add_in_db(self, password_confirmation, files):
        """Insert the user in the database"""
        # _validate values
        self._validate_login()
        self._validate_student_email()
        self._validate_firstname()
        self._validate_lastname()
        self._validate_gender()
        self._validate_phone_number()
        self._validate_description()
        self._validate_password(password_confirmation)

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

        query = "INSERT INTO uniride.ur_documents (u_id) VALUES (%s)"
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, (self.u_id,))

        query = "INSERT INTO uniride.ur_document_verification (u_id) VALUES (%s)"
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, (self.u_id,))

        self.get_from_db()

        try:
            self.save_pfp(files)
            self.save_license(files)
            self.save_id_card(files)
            self.save_school_certificate(files)
        except MissingInputException:
            pass

    def save_pfp(self, files):
        """Save profil picture"""
        if "pfp" not in files:
            raise MissingInputException("MISSING_PFP_FILE")
        file = files["pfp"]
        if file.filename == "":
            raise MissingInputException("MISSING_PFP_FILE")

        allowed_extensions = ["png", "jpg", "jpeg"]
        file_name = save_file(
            file, app.config["PFP_UPLOAD_FOLDER"], allowed_extensions, self.u_id
        )
        if file_name != self.u_profile_picture:
            try:
                if self.u_profile_picture:
                    delete_file(self.u_profile_picture, app.config["PFP_UPLOAD_FOLDER"])
            except FileNotFoundError:
                pass
            query = "UPDATE uniride.ur_user SET u_profile_picture=%s WHERE u_id=%s"
            values = (file_name, self.u_id)
            conn = connect_pg.connect()
            connect_pg.execute_command(conn, query, values)

    def save_license(self, files):
        """Save license"""
        self.d_license = self._save_document(files, self.d_license, "license")

    def save_id_card(self, files):
        """Save id card"""
        self.d_id_card = self._save_document(files, self.d_id_card, "id_card")

    def save_school_certificate(self, files):
        """Save school certificate"""
        self.d_school_certificate = self._save_document(
            files, self.d_school_certificate, "school_certificate"
        )

    def _save_document(self, files, old_file_name, document_type):
        """Save document"""
        if document_type not in files:
            raise MissingInputException(f"MISSING_{document_type.upper()}_FILE")
        file = files[document_type]
        if file.filename == "":
            raise MissingInputException(f"MISSING_{document_type.upper()}_FILE")

        allowed_extensions = ["pdf", "png", "jpg", "jpeg"]
        directory = app.config[f"{document_type.upper()}_UPLOAD_FOLDER"]
        file_name = save_file(file, directory, allowed_extensions, self.u_id)
        if file_name != old_file_name:
            try:
                if old_file_name:
                    delete_file(old_file_name, directory)
            except FileNotFoundError:
                pass
            query = (
                f"UPDATE uniride.ur_documents SET d_{document_type}=%s WHERE u_id=%s"
            )
            values = (file_name, self.u_id)
            conn = connect_pg.connect()
            connect_pg.execute_command(conn, query, values)
        return file_name

    def _validate_login(self):
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

    def _validate_student_email(self):
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

    def _validate_firstname(self):
        """Check if the firstname is valid"""

        self._validate_name(self.u_firstname, "FIRSTNAME")

    def _validate_lastname(self):
        """Check if the lastname is valid"""

        self._validate_name(self.u_lastname, "LASTNAME")

    def _validate_gender(self):
        """Check if the gender is valid"""

        # check if exist
        if not self.u_gender:
            raise MissingInputException("GENDER_MISSING")

        # check if the format is valid
        if self.u_gender not in ("N", "H", "F"):
            raise InvalidInputException("GENDER_INVALID")

    def _validate_phone_number(self):
        """Check if the phone number is valid"""
        # check if the format is valid
        if self.u_phone_number and not (
            self.u_phone_number.isdigit() and len(self.u_phone_number) == 9
        ):
            raise InvalidInputException("PHONE_NUMBER_INVALID")

    def _validate_description(self):
        """Check if the description is valid"""
        # check if description not too long
        if self.u_description and len(self.u_description) > 500:
            raise InvalidInputException("DESCRIPTION_TOO_LONG")

    def _validate_password(self, password_confirmation):
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
