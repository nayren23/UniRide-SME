"""User business owner"""
import connect_pg
from models.exception.user_exceptions import InvalidInputException
import re


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
        try:
            self._validate_email()
        except InvalidInputException as e:
            return {"message": str(e), "status_code": 422}

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
        return {"message": "User created successfuly", "status_code": 422}

    def _validate_email(self):
        # check if exist
        if not self.student_email:
            raise InvalidInputException("Email missing")

        # check if the format is valid
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.fullmatch(regex, self.student_email):
            raise InvalidInputException("Email invalid")

        # check if the email is already taken
        query = "select count(*) from uniride.ur_user where u_student_email = %s"

        conn = connect_pg.connect()
        email_count = connect_pg.get_query(conn, query, (self.student_email,))[0][0]
        if email_count:
            raise InvalidInputException("Email adresse already taken")
