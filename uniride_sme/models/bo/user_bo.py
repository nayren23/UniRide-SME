"""User business owner"""
import re
import bcrypt

from uniride_sme import app
from uniride_sme import connect_pg
from uniride_sme.models.bo.documents_bo import DocumentsBO
from uniride_sme.utils.file import save_file, delete_file
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

        self.documents_bo = DocumentsBO(self.u_id)
        self.documents_bo.get_from_db()

    def add_in_db(self, password_confirmation, files):
        """Insert the user in the database"""
        # _validate values
        self._validate_login(self.u_login)
        self._validate_student_email(self.u_student_email)
        self._validate_firstname(self.u_firstname)
        self._validate_lastname(self.u_lastname)
        self._validate_gender(self.u_gender)
        self._validate_phone_number(self.u_phone_number)
        self._validate_description(self.u_description)
        self._validate_password(self.u_password, password_confirmation)

        self._hash_password(self.u_password)

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

        self.documents_bo = DocumentsBO(self.u_id)
        self.documents_bo.add_in_db(files)
        try:
            self.u_profile_picture = None
            self.save_pfp(files)
        except MissingInputException:
            pass

    def change_password(self, old_password, new_password, new_password_confirmation):
        """Change password"""
        if not old_password:
            raise MissingInputException("PASSWORD_MISSING")

        if not self._verify_password(old_password, self.u_password):
            raise PasswordIncorrectException()

        if old_password == new_password:
            raise InvalidInputException("PASSWORD_OLD_AND_NEW_SAME")

        self._validate_password(new_password, new_password_confirmation)
        hashed_password = self._hash_password(new_password)

        query = "UPDATE uniride.ur_user SET u_password=%s WHERE u_id=%s"
        values = (hashed_password, self.u_id)
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, values)
        self.u_password = hashed_password

    def change_login(self, login):
        """Change login"""
        if not login:
            raise MissingInputException("LOGIN_MISSING")

        if self.u_login == login:
            raise InvalidInputException("LOGIN_OLD_AND_NEW_SAME")

        self._validate_login(login)
        query = "UPDATE uniride.ur_user SET u_login=%s WHERE u_id=%s"
        values = (login, self.u_id)
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, values)
        self.u_login = login

    def change_firstname(self, firstname):
        """Change firstname"""
        self._change_name(firstname, "FIRSTNAME")

    def change_lastname(self, lastname):
        """Change lastname"""
        self._change_name(lastname, "LASTNAME")

    def _change_name(self, name, name_type):
        """Change name"""
        if not name:
            raise MissingInputException(f"{name_type}_MISSING")

        if getattr(self, f"u_{name_type.lower()}") == name:
            raise InvalidInputException(f"{name_type}_OLD_AND_NEW_SAME")

        self._validate_name(name, name_type)
        query = f"UPDATE uniride.ur_user SET u_{name_type.lower()}=%s WHERE u_id=%s"
        values = (name, self.u_id)
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, values)
        setattr(self, f"u_{name_type.lower()}", name)

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
        try:
            if self.u_profile_picture and file_name != self.u_profile_picture:
                delete_file(self.u_profile_picture, app.config["PFP_UPLOAD_FOLDER"])
        except FileNotFoundError:
            pass
        query = "UPDATE uniride.ur_user SET u_profile_picture=%s, u_timestamp_modification=CURRENT_TIMESTAMP WHERE u_id=%s"
        values = (file_name, self.u_id)
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, values)

    def save_license(self, files):
        """Save license"""
        self.documents_bo.save_license(files)

    def save_id_card(self, files):
        """Save id card"""
        self.documents_bo.save_id_card(files)

    def save_school_certificate(self, files):
        """Save school certificate"""
        self.documents_bo.save_school_certificate(files)

    @staticmethod
    def _validate_login(login):
        """Check if the login is valid"""

        # check if exist
        if not login:
            raise MissingInputException("LOGIN_MISSING")

        # check if the format is valid
        if len(login) > 50:
            raise InvalidInputException("LOGIN_TOO_LONG")

        regex = r"[A-Za-z0-9._-]+"
        if not re.fullmatch(regex, login):
            raise InvalidInputException("LOGIN_INVALID_CHARACTERS")

        # check if the login is already taken
        query = "select count(*) from uniride.ur_user where u_login = %s"
        conn = connect_pg.connect()
        count = connect_pg.get_query(conn, query, (login,))[0][0]
        if count:
            raise InvalidInputException("LOGIN_TAKEN")

    @staticmethod
    def _validate_student_email(studen_email):
        """Check if the email is valid"""

        # check if exist
        if not studen_email:
            raise MissingInputException("EMAIL_MISSING")

        # check if the format is valid
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.fullmatch(regex, studen_email):
            raise InvalidInputException("EMAIL_INVALID_FORMAT")

        if len(studen_email) > 254:
            raise InvalidInputException("EMAIL_TOO_LONG")

        # check if the domain is valid
        email_domain = studen_email.split("@")[1]
        valid_domain = app.config["UNIVERSITY_EMAIL_DOMAIN"]
        if email_domain != valid_domain:
            raise InvalidInputException("EMAIL_INVALID_DOMAIN")

        # check if the email is already taken
        query = "select count(*) from uniride.ur_user where u_student_email = %s"
        conn = connect_pg.connect()
        count = connect_pg.get_query(conn, query, (studen_email,))[0][0]
        if count:
            raise InvalidInputException("EMAIL_TAKEN")

    @staticmethod
    def _validate_name(name, name_type):
        """Check if the name is valid"""
        # check if exist
        if not name:
            raise MissingInputException(f"{name_type}_MISSING")

        # check if the format is valid
        if len(name) > 50:
            raise InvalidInputException(f"{name_type}_TOO_LONG")

        regex = r"[A-Za-z-\s]+"
        if not re.fullmatch(regex, name):
            raise InvalidInputException(f"{name_type}_INVALID_CHARACTERS")

    @staticmethod
    def _validate_firstname(firstname):
        """Check if the firstname is valid"""

        UserBO._validate_name(firstname, "FIRSTNAME")

    @staticmethod
    def _validate_lastname(lastname):
        """Check if the lastname is valid"""
        UserBO._validate_name(lastname, "LASTNAME")

    @staticmethod
    def _validate_gender(gender):
        """Check if the gender is valid"""

        # check if exist
        if not gender:
            raise MissingInputException("GENDER_MISSING")

        # check if the format is valid
        if gender not in ("N", "H", "F"):
            raise InvalidInputException("GENDER_INVALID")

    @staticmethod
    def _validate_phone_number(phone_number):
        """Check if the phone number is valid"""
        # check if the format is valid
        if phone_number and not (phone_number.isdigit() and len(phone_number) == 9):
            raise InvalidInputException("PHONE_NUMBER_INVALID")

    @staticmethod
    def _validate_description(description):
        """Check if the description is valid"""
        # check if description not too long
        if description and len(description) > 500:
            raise InvalidInputException("DESCRIPTION_TOO_LONG")

    @staticmethod
    def _validate_password(password, password_confirmation):
        """Check if the password is valid"""

        # check if exist
        if not password:
            raise MissingInputException("PASSWORD_MISSING")
        if not password_confirmation:
            raise MissingInputException("PASSWORD_CONFIRMATION_MISSING")

        # check if the format is valid
        contains_lower_case_letter = re.search(r"[a-z]", password)
        contains_upper_case_letter = re.search(r"[A-Z]", password)
        contains_digit = re.search(r"\d", password)
        contains_special = re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
        correct_size = 8 <= len(password) <= 50

        if not (
            contains_lower_case_letter
            and contains_upper_case_letter
            and contains_digit
            and contains_special
            and correct_size
        ):
            raise InvalidInputException("PASSWORD_INVALID")

        # check if password and password confirmation are equals
        if password != password_confirmation:
            raise InvalidInputException("PASSWORD_NOT_MATCHING")

    @staticmethod
    def _hash_password(password) -> str:
        """Hash the password"""
        salt = app.config["SECURITY_PASSWORD_SALT"]
        # convert to bytes
        salt = salt.encode("utf8")
        password = password.encode("utf8")
        password = bcrypt.hashpw(password, salt)
        # convert back to string
        return str(password, "utf8")

    @staticmethod
    def _verify_password(password, hashed_password) -> bool:
        """Verify the password is correct"""
        return bcrypt.checkpw(
            password.encode("utf8"),
            hashed_password.encode("utf8"),
        )

    @staticmethod
    def verify_student_email(student_email):
        """Verify the student email"""
        # check if exist
        if not student_email:
            raise MissingInputException("EMAIL_MISSING")

        query = (
            "select u_email_verified from uniride.ur_user where u_student_email = %s"
        )
        conn = connect_pg.connect()
        email_verified = connect_pg.get_query(conn, query, (student_email,))
        # check if the email belongs to a user
        if not email_verified:
            raise InvalidInputException("EMAIL_NOT_OWNED")
        # check if the email is already verified
        if email_verified[0][0]:
            raise InvalidInputException("EMAIL_ALREADY_VERIFIED")

        query = "update uniride.ur_user set u_email_verified=True where u_student_email = %s"
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, (student_email,))

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

        if not self._verify_password(self.u_password, password[0][0]):
            raise PasswordIncorrectException()
