"""User business owner"""
import connect_pg


class UserBO:
    """User business owner class"""

    def __init__(
        self,
        id: int = None,
        lastname: str = None,
        student_email: str = None,
        password: str = None,
        gender: str = None,
        firstname: str = None,
        phone_number: str = None,
        description: str = None,
    ):
        self.id = id
        self.lastname = lastname
        self.student_email = student_email
        self.password = password
        self.gender = gender
        self.firstname = firstname
        self.phone_number = phone_number
        self.description = description

    def add_in_db(self):
        """Insert the user in the database"""
        attr_dict = {}
        for attr, value in self.__dict__.items():
            if value:
                attr_dict["u_" + attr] = f"'{value}'"

        fields = ", ".join(attr_dict)
        values = ", ".join(attr_dict.values())
        query = (
            f"INSERT INTO uniride.ur_user ({fields}) VALUES ({values}) RETURNING u_id"
        )

        conn = connect_pg.connect()
        id = connect_pg.execute_commands(conn, (query,))
        self.id = id
