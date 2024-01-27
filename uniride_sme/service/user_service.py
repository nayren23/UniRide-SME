"""User service module"""
import re
import bcrypt
from uniride_sme import app, connect_pg
from uniride_sme.model.bo.user_bo import UserBO
from uniride_sme.service.documents_service import update_role
from uniride_sme.service.trip_service import get_trip_by_id
from uniride_sme.service import admin_service
from uniride_sme.utils.file import save_file, delete_file
from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,
    MissingInputException,
)
from uniride_sme.utils.exception.user_exceptions import (
    UserNotFoundException,
    PasswordIncorrectException,
    AttributeUnchangedException,
)


def authenticate(login, password) -> UserBO:
    """authenticate the user"""
    # check if exist
    if not login:
        raise MissingInputException("LOGIN_MISSING")
    if not password:
        raise MissingInputException("PASSWORD_MISSING")

    try:
        user_bo = get_user_by_login(login)
    except UserNotFoundException:
        user_bo = get_user_by_email(login)
    _verify_password(password, user_bo.password)
    return user_bo


def get_user_role(user_id):
    """Get user role"""
    with connect_pg.connect() as conn:
        admin_service.verify_user(user_id)

        query = """
        SELECT r_id, u_id
        FROM uniride.ur_user
        WHERE u_id = %s
        """

        r_id = connect_pg.get_query(conn, query, (user_id,))

    if not r_id:
        raise UserNotFoundException

    document = r_id[0]

    return {"role": document[0], "id": user_id}


def get_user_by_id(user_id) -> UserBO:
    """Get user infos from db using the id"""
    return _get_user_by_identifier(user_id, "u_id")


def get_user_by_login(login) -> UserBO:
    """Get user infos from db using the login"""
    return _get_user_by_identifier(login, "u_login")


def get_user_by_email(student_email) -> UserBO:
    """Get user infos from db using the student_email"""
    return _get_user_by_identifier(student_email, "u_student_email")


def _get_user_by_identifier(identifier, identifier_type) -> UserBO:
    """Get user infos from db"""
    if not identifier and not identifier_type:
        raise MissingInputException("IDENTIFIER_MISSING")

    query = f"select * from uniride.ur_user where {identifier_type} = %s"
    params = (identifier,)

    conn = connect_pg.connect()
    infos = connect_pg.get_query(conn, query, params, True)
    connect_pg.disconnect(conn)

    if not infos:
        raise UserNotFoundException()
    infos = infos[0]

    user_bo = UserBO(
        id=infos["u_id"],
        login=infos["u_login"],
        firstname=infos["u_firstname"],
        lastname=infos["u_lastname"],
        student_email=infos["u_student_email"],
        password=infos["u_password"],
        gender=infos["u_gender"],
        phone_number=infos["u_phone_number"],
        description=infos["u_description"],
        profile_picture=infos["u_profile_picture"],
        timestamp_creation=infos["u_timestamp_creation"],
        timestamp_modification=infos["u_timestamp_modification"],
        email_verified=infos["u_email_verified"],
        r_id=infos["r_id"],
    )
    return user_bo


def add_user(  # pylint: disable=too-many-arguments, too-many-locals
    login,
    lastname,
    firstname,
    student_email,
    password,
    password_confirmation,
    gender,
    phone_number,
    description,
    pfp_file,
) -> UserBO:
    """Insert the user in the database"""

    _validate_login(login)
    _validate_student_email(student_email)
    _validate_firstname(firstname)
    _validate_lastname(lastname)
    _validate_gender(gender)
    _validate_phone_number(phone_number)
    _validate_description(description)
    _validate_password(password, password_confirmation)

    password = _hash_password(password)

    user_attributes = {
        "u_login": login,
        "u_firstname": firstname,
        "u_lastname": lastname,
        "u_student_email": student_email,
        "u_password": password,
        "u_gender": gender,
        "u_phone_number": phone_number,
        "u_description": description,
    }

    fields = ", ".join(user_attributes.keys())
    placeholders = ", ".join(["%s"] * len(user_attributes))
    values = tuple(user_attributes.values())

    query = f"INSERT INTO uniride.ur_user ({fields}) VALUES ({placeholders}) RETURNING u_id"

    conn = connect_pg.connect()
    user_id = connect_pg.execute_command(conn, query, values)

    try:
        save_pfp(user_id, pfp_file)
    except MissingInputException:
        pass

    return get_user_by_id(user_id)


def _validate_login(login) -> None:
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


def _validate_student_email(studen_email) -> None:
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


def _hash_password(password) -> str:
    """Hash the password"""
    salt = app.config["JWT_SALT"]
    password = password.encode("utf8")
    password = bcrypt.hashpw(password, salt)
    # convert back to string
    return str(password, "utf8")


def _verify_password(password, hashed_password) -> bool:
    """Verify the password is correct"""
    if not bcrypt.checkpw(password.encode("utf8"), hashed_password.encode("utf8")):
        raise PasswordIncorrectException()


def save_pfp(user_id, pfp_file, profile_picture=None) -> None:
    """Save profil picture"""
    if not pfp_file:
        raise MissingInputException("MISSING_PFP_FILE")

    if pfp_file.filename == "":
        raise MissingInputException("MISSING_PFP_FILE")

    allowed_extensions = ["png", "jpg", "jpeg"]
    file_name = save_file(pfp_file, app.config["PFP_UPLOAD_FOLDER"], allowed_extensions, user_id)
    try:
        if profile_picture and file_name != profile_picture:
            delete_file(profile_picture, app.config["PFP_UPLOAD_FOLDER"])
    except FileNotFoundError:
        pass
    query = "UPDATE uniride.ur_user SET u_profile_picture=%s, u_timestamp_modification=CURRENT_TIMESTAMP WHERE u_id=%s"
    values = (file_name, user_id)
    conn = connect_pg.connect()
    connect_pg.execute_command(conn, query, values)


def verify_student_email(student_email) -> None:
    """Verify the student email"""
    # check if exist
    if not student_email:
        raise MissingInputException("EMAIL_MISSING")

    conn = connect_pg.connect()

    query = "select u_email_verified, u_id from uniride.ur_user where u_student_email = %s"
    email_verified = connect_pg.get_query(conn, query, (student_email,))
    # check if the email belongs to a user
    if not email_verified:
        raise InvalidInputException("EMAIL_NOT_OWNED")
    # check if the email is already verified
    if email_verified[0][0]:
        raise InvalidInputException("EMAIL_ALREADY_VERIFIED")

    query = "update uniride.ur_user set u_email_verified=True where u_student_email = %s"

    connect_pg.execute_command(conn, query, (student_email,))
    connect_pg.disconnect(conn)

    update_role(email_verified[0][1])


def _validate_firstname(firstname) -> None:
    """Check if the firstname is valid"""
    _validate_name(firstname, "FIRSTNAME")


def _validate_lastname(lastname) -> None:
    """Check if the lastname is valid"""
    _validate_name(lastname, "LASTNAME")


def _validate_name(name, name_type) -> None:
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


def _validate_gender(gender) -> None:
    """Check if the gender is valid"""

    # check if exist
    if not gender:
        raise MissingInputException("GENDER_MISSING")

    # check if the format is valid
    if gender not in ("N", "H", "F"):
        raise InvalidInputException("GENDER_INVALID")


def _validate_phone_number(phone_number) -> None:
    """Check if the phone number is valid"""
    if not phone_number:
        raise MissingInputException("PHONE_NUMBER_MISSING")

    # check if the format is valid
    if not phone_number.isdigit() or len(phone_number) != 10:
        raise InvalidInputException("PHONE_NUMBER_INVALID")

    query = "select count(*) from uniride.ur_user where u_phone_number = %s"
    conn = connect_pg.connect()
    count = connect_pg.get_query(conn, query, (phone_number,))[0][0]
    if count:
        raise InvalidInputException("PHONE_NUMBER_TAKEN")


def _validate_description(description) -> None:
    """Check if the description is valid"""
    # check if description not too long
    if description and len(description) > 500:
        raise InvalidInputException("DESCRIPTION_TOO_LONG")


def _validate_password(password, password_confirmation) -> None:
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


def change_password(user_id, old_password, new_password, new_password_confirmation) -> None:
    """Change password"""
    user_bo = get_user_by_id(user_id)
    if not old_password:
        raise MissingInputException("PASSWORD_MISSING")

    _verify_password(old_password, user_bo.password)

    if old_password == new_password:
        raise AttributeUnchangedException("PASSWORD")

    _validate_password(new_password, new_password_confirmation)

    hashed_password = _hash_password(new_password)

    query = "UPDATE uniride.ur_user SET u_password=%s WHERE u_id=%s"
    values = (hashed_password, user_id)
    conn = connect_pg.connect()
    connect_pg.execute_command(conn, query, values)
    connect_pg.disconnect(conn)


def change_forgotten_password(studen_email, new_password, new_password_confirmation) -> None:
    """Change forgotten password"""
    _validate_password(new_password, new_password_confirmation)

    hashed_password = _hash_password(new_password)

    query = "UPDATE uniride.ur_user SET u_password=%s WHERE u_student_email=%s"
    values = (hashed_password, studen_email)
    conn = connect_pg.connect()
    connect_pg.execute_command(conn, query, values)


def change_student_email(user_id, student_email) -> None:
    """Change student email"""
    user_bo = get_user_by_id(user_id)
    if user_bo.student_email == student_email:
        raise AttributeUnchangedException("STUDENT_EMAIL")

    _validate_student_email(student_email)

    query = "UPDATE uniride.ur_user SET u_student_email=%s, u_email_verified=false WHERE u_id=%s"
    values = (student_email, user_id)
    conn = connect_pg.connect()
    connect_pg.execute_command(conn, query, values)
    connect_pg.disconnect(conn)


def update_user_attribute(user_id, attribute_name, new_value, validation_func) -> None:
    """General function to update a user attribute"""
    user_bo = get_user_by_id(user_id)

    # Check if the new value is the same as the old value
    if getattr(user_bo, attribute_name) == new_value:
        raise AttributeUnchangedException(attribute_name.upper())

    # Validate the new value
    validation_func(new_value)

    # Construct the query dynamically
    query = f"UPDATE uniride.ur_user SET u_{attribute_name}=%s WHERE u_id=%s"
    values = (new_value, user_id)
    conn = connect_pg.connect()
    connect_pg.execute_command(conn, query, values)
    connect_pg.disconnect(conn)


def change_login(user_id, login) -> None:
    """Change login"""
    update_user_attribute(user_id, "login", login, _validate_login)


def change_firstname(user_id, firstname) -> None:
    """Change firstname"""
    update_user_attribute(user_id, "firstname", firstname, lambda name: _validate_name(name, "FIRSTNAME"))


def change_lastname(user_id, lastname) -> None:
    """Change lastname"""
    update_user_attribute(user_id, "lastname", lastname, lambda name: _validate_name(name, "LASTNAME"))


def change_phone_number(user_id, phone_number) -> None:
    """Change phone number"""
    update_user_attribute(user_id, "phone_number", phone_number, _validate_phone_number)


def change_gender(user_id, gender) -> None:
    """Change gender"""
    update_user_attribute(user_id, "gender", gender, _validate_gender)


def change_description(user_id, description) -> None:
    """Change description"""
    update_user_attribute(user_id, "description", description, _validate_description)


def get_label(trip_id, user_id):
    """Get passenger label"""
    result = []
    conn = connect_pg.connect()
    current_trip = get_trip_by_id(trip_id)
    if user_id == current_trip.get("driver_id"):
        query = "SELECT rc_id, rc_name FROM uniride.ur_rating_criteria WHERE r_id = 2"
    else:
        query = "SELECT rc_id, rc_name FROM uniride.ur_rating_criteria WHERE r_id = 1"
    result_label = connect_pg.get_query(conn, query)
    for label in result_label:
        user_data = {
            "id": label[0],
            "name": label[1],
        }
        result.append(user_data)
    connect_pg.disconnect(conn)
    return result
