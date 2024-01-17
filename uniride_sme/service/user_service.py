"""User service module"""
import re
import bcrypt
from uniride_sme.utils.file import get_encoded_file
from uniride_sme import app
from uniride_sme import connect_pg
from uniride_sme.model.bo.user_bo import UserBO
from uniride_sme.service.documents_service import update_role
from uniride_sme.service.trip_service import get_trip_by_id
from uniride_sme.utils.file import save_file, delete_file
from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,
    MissingInputException,
)
from uniride_sme.utils.exception.user_exceptions import (
    UserNotFoundException,
    PasswordIncorrectException,
    AttributeUnchangedException,
    RatingNotFoundException,
)
from uniride_sme.utils.exception.criteria_exceptions import TooManyCriteriaException


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
        verify_user(user_id)

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
        status=infos["u_status"],
        home_address_id=infos["u_home_address_id"],
        work_address_id=infos["u_work_address_id"],
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
):
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


def save_pfp(user_id, pfp_file, profile_picture=None):
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


def verify_student_email(student_email):
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


def _validate_firstname(firstname):
    """Check if the firstname is valid"""
    _validate_name(firstname, "FIRSTNAME")


def _validate_lastname(lastname):
    """Check if the lastname is valid"""
    _validate_name(lastname, "LASTNAME")


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


def _validate_gender(gender):
    """Check if the gender is valid"""

    # check if exist
    if not gender:
        raise MissingInputException("GENDER_MISSING")

    # check if the format is valid
    if gender not in ("N", "H", "F"):
        raise InvalidInputException("GENDER_INVALID")


def _validate_phone_number(phone_number):
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


def _validate_description(description):
    """Check if the description is valid"""
    # check if description not too long
    if description and len(description) > 500:
        raise InvalidInputException("DESCRIPTION_TOO_LONG")


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


def change_password(user_id, old_password, new_password, new_password_confirmation):
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


def change_student_email(user_id, student_email):
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


def update_user_attribute(user_id, attribute_name, new_value, validation_func):
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


def change_login(user_id, login):
    """Change login"""
    update_user_attribute(user_id, "login", login, _validate_login)


def change_firstname(user_id, firstname):
    """Change firstname"""
    update_user_attribute(user_id, "firstname", firstname, lambda name: _validate_name(name, "FIRSTNAME"))


def change_lastname(user_id, lastname):
    """Change lastname"""
    update_user_attribute(user_id, "lastname", lastname, lambda name: _validate_name(name, "LASTNAME"))


def change_phone_number(user_id, phone_number):
    """Change phone number"""
    update_user_attribute(user_id, "phone_number", phone_number, _validate_phone_number)


def change_gender(user_id, gender):
    """Change gender"""
    update_user_attribute(user_id, "gender", gender, _validate_gender)


def change_description(user_id, description):
    """Change description"""
    update_user_attribute(user_id, "description", description, _validate_description)


def count_users():
    """Get number of users"""
    conn = connect_pg.connect()
    query = "SELECT COUNT(*) FROM uniride.ur_user"
    result = connect_pg.get_query(conn, query)
    connect_pg.disconnect(conn)
    return result[0][0]


def count_role_user(role):
    """Get number of user by role"""
    conn = connect_pg.connect()
    query = "SELECT COUNT(*) FROM uniride.ur_user WHERE r_id = %s"
    result = connect_pg.get_query(conn, query, (role,))
    connect_pg.disconnect(conn)
    return result[0][0]


def users_information():
    """Get users information"""
    conn = connect_pg.connect()
    result = []

    try:
        query = """
            SELECT u_id, r_id, u_lastname, u_firstname, u_profile_picture, u_timestamp_creation, u_timestamp_modification
            FROM uniride.ur_user
        """
        document = connect_pg.get_query(conn, query)

        for documents in document:
            request_data = {
                "id_user": documents[0],
                "lastname": documents[2],
                "firstname": documents[3],
                "timestamp_creation": documents[5],
                "last_modified_date": documents[6],
                "profile_picture": get_encoded_file(documents[4], "PFP_UPLOAD_FOLDER"),
                "role": documents[1],
            }

            result.append(request_data)
    finally:
        connect_pg.disconnect(conn)

    return result


def verify_user(id_user):
    """Verify user"""
    conn = connect_pg.connect()
    check_query = "SELECT * FROM uniride.ur_user WHERE u_id = %s"
    check_values = (id_user,)
    result = connect_pg.get_query(conn, check_query, check_values)

    if not result:
        connect_pg.disconnect(conn)
        raise UserNotFoundException()
    connect_pg.disconnect(conn)


def verify_admin(id_user):
    """Verify user"""
    conn = connect_pg.connect()
    check_query = "SELECT r_id FROM uniride.ur_user WHERE u_id = %s"
    check_values = (id_user,)
    result = connect_pg.get_query(conn, check_query, check_values)

    if not result:
        connect_pg.disconnect(conn)
        raise UserNotFoundException()
    connect_pg.disconnect(conn)


def delete_user(id_user):
    """Delete user"""
    conn = connect_pg.connect()
    verify_user(id_user)
    delete_query = "DELETE FROM uniride.ur_user WHERE u_id = %s"
    delete_values = (id_user,)
    connect_pg.execute_command(conn, delete_query, delete_values)
    connect_pg.disconnect(conn)

    return id_user


def user_information_id(id_user):
    """Get user information"""
    conn = connect_pg.connect()
    verify_user(id_user)

    query = """
    SELECT r_id, u_login, u_student_email, u_lastname, u_firstname, u_phone_number, u_gender, u_description, u_profile_picture
    FROM uniride.ur_user WHERE u_id = %s
    """

    # Pass the id_user parameter in the execute query
    document = connect_pg.get_query(conn, query, (id_user,))
    connect_pg.disconnect(conn)

    if not document:
        # Handle the case where no user information is found for the given ID
        return None

    user_data = document[0]

    result = {
        "login": user_data[1],
        "student_email": user_data[2],
        "firstname": user_data[4],
        "lastname": user_data[3],
        "gender": user_data[6],
        "phone_number": user_data[5],
        "description": user_data[7],
        "role": user_data[0],
        "profile_picture": get_encoded_file(user_data[8], "PFP_UPLOAD_FOLDER"),
    }

    return result


def user_stat_passenger(id_user):
    """Get user information"""
    with connect_pg.connect() as conn:
        verify_user(id_user)

        query = """
        SELECT j_accepted
        FROM uniride.ur_join
        WHERE u_id = %s
        """
        document = connect_pg.get_query(conn, query, (id_user,))

    if not document:
        # If the query result is None, return counts initialized to 0
        return {"completed_count": 0, "pending_count": 0}

    user_data = document[0]
    count_completed = user_data.count(1)
    count_pending = user_data.count(0)

    result = {
        "completed_count": count_completed,
        "pending_count": count_pending,
    }

    return result


def user_stat_driver(id_user):
    """Get user information"""
    with connect_pg.connect() as conn:
        verify_user(id_user)

        query = """
        SELECT t_status
        FROM uniride.ur_trip
        WHERE t_user_id = %s
        """
        document = connect_pg.get_query(conn, query, (id_user,))

    if not document:
        # If the query result is None, return counts initialized to 0
        return {"pending_count": 0, "canceled_count": 0, "completed_count": 0, "oncourse_count": 0}

    user_data = document[0]

    countpending = user_data.count(1)
    countcanceled = user_data.count(2)
    countcompleted = user_data.count(3)
    countoncourse = user_data.count(4)

    result = {
        "pending_count": countpending,
        "canceled_count": countcanceled,
        "completed_count": countcompleted,
        "oncourse_count": countoncourse,
    }

    return result


def verify_rating_criteria(id_criteria):
    """Verify criteria"""
    conn = connect_pg.connect()
    check_query = "SELECT r_id FROM uniride.ur_rating_criteria WHERE rc_id = %s"
    check_values = (id_criteria,)
    result = connect_pg.get_query(conn, check_query, check_values)

    if not result:
        connect_pg.disconnect(conn)
        raise RatingNotFoundException()
    connect_pg.disconnect(conn)
    return result


def get_rating_criteria():
    """Get rating criteria from the database"""
    conn = connect_pg.connect()

    try:
        query = """
            SELECT rc_id, rc_name, rc_description,r_id
            FROM uniride.ur_rating_criteria
        """
        documents = connect_pg.get_query(conn, query)

        labels = []

        for document in documents:
            label_data = {
                "label": {
                    "id_criteria": document[0],
                    "name": document[1],
                    "description": document[2],
                    "role": document[3],
                }
            }
            labels.append(label_data)

    finally:
        connect_pg.disconnect(conn)

    return labels


def insert_rating_criteria(data):
    """Insert new rating criteria"""
    conn = connect_pg.connect()
    if count_role(data["role"]) >= 5:
        raise TooManyCriteriaException
    try:
        query = """
           INSERT INTO uniride.ur_rating_criteria (rc_name, rc_description,r_id)
           VALUES (%s, %s,%s)
           RETURNING rc_id
        """
        result = connect_pg.execute_command(conn, query, (data["name"], data["description"], data["role"]))
    finally:
        connect_pg.disconnect(conn)
    return result


def delete_rating_criteria(id_criteria):
    """Delete rating criteria"""
    conn = connect_pg.connect()
    verify_rating_criteria(id_criteria)
    try:
        query = """
           DELETE FROM uniride.ur_rating_criteria WHERE rc_id = %s
        """
        connect_pg.execute_command(conn, query, (id_criteria,))
    finally:
        connect_pg.disconnect(conn)
    return id_criteria


def update_rating_criteria(data):
    """Update rating criteria"""
    conn = connect_pg.connect()
    id_role_ongoing = verify_rating_criteria(data["id_criteria"])

    if count_role(data["role"]) > 4 and id_role_ongoing[0][0] != data["role"]:
        raise InvalidInputException("TOO_MANY_CRITERIA_FOR_THIS_ROLE")
    try:
        query = """
           UPDATE uniride.ur_rating_criteria
           SET rc_name = %s, rc_description = %s, r_id = %s
           WHERE rc_id = %s
        """
        verify_rating_criteria(data["id_criteria"])
        connect_pg.execute_command(conn, query, (data["name"], data["description"], data["role"], data["id_criteria"]))

    finally:
        connect_pg.disconnect(conn)

    return {"message": "Rating criteria updated successfully"}


def users_ranking(role):
    """Get ranking information"""
    conn = connect_pg.connect()
    result = []

    try:
        query = """
            SELECT DISTINCT ON (ur_user.u_id) ur_user.u_id, ur_user.r_id, ur_user.u_lastname, ur_user.u_firstname,ur_user.u_profile_picture,
                   ur_rating.rc_id, AVG(ur_rating.n_value) AS n_value
            FROM uniride.ur_user
            NATURAL JOIN uniride.ur_rating
            WHERE ur_user.r_id = %s  
            GROUP BY ur_user.u_id, ur_user.r_id, ur_user.u_lastname, ur_user.u_firstname, ur_rating.rc_id
        """
        ranks = connect_pg.get_query(conn, query, (role,))

        for rank in ranks:
            user_data = {
                "id": rank[0],
                "profile_picture": get_encoded_file(rank[4], "PFP_UPLOAD_FOLDER"),
                "firstname": rank[3],
                "lastname": rank[2],
                "role": rank[1],
            }

            score_criteria = criteria_by_id(rank[0], rank[1])
            average = calculate_avg_note_by_user(rank[0])
            result.append({"user": user_data, "average": average, "scoreCriteria": score_criteria})
    finally:
        connect_pg.disconnect(conn)

    return result


def calculate_avg_note_by_user(user_id):
    """Calculate the average note value for a given user."""
    conn = connect_pg.connect()

    try:
        query = """
            SELECT AVG(n_value) AS avg_note
            FROM uniride.ur_rating
            WHERE u_id = %s
        """
        avg_result = connect_pg.get_query(conn, query, (user_id,))

        if avg_result and avg_result[0][0] is not None:
            return round(avg_result[0][0], 2)
        else:
            return None  # Return None if there are no notes for the user

    finally:
        connect_pg.disconnect(conn)


def criteria_by_id(user_id, role):
    """Get criteria by id"""
    conn = connect_pg.connect()
    result = []

    try:
        query = """
            SELECT rc_id, ROUND(avg(n_value),2) as avg_value, rc_name
            FROM uniride.ur_rating
            NATURAL JOIN uniride.ur_rating_criteria
            WHERE ur_rating.u_id = %s and ur_rating_criteria.r_id = %s
            GROUP BY rc_id, rc_name
        """
        criterian_result = connect_pg.get_query(
            conn,
            query,
            (
                user_id,
                role,
            ),
        )

        actif_criterion = actif_criteria(role)

        print(actif_criterion, "ACTIF CRITERION")

        for actif in actif_criterion:
            criteria_found = False
            for criteria in criterian_result:
                if actif["id"] == criteria[0]:
                    user_data = {
                        "id": criteria[0],
                        "name": criteria[2],
                        "value": criteria[1],
                    }
                    result.append(user_data)
                    criteria_found = True
                    break

            if not criteria_found:
                # If no matching criteria found, add null values
                user_data = {
                    "id": actif["id"],
                    "name": actif["name"],
                    "value": None,
                }
                result.append(user_data)

        return result
    finally:
        connect_pg.disconnect(conn)


def actif_criteria(role):
    """Get active criteria"""
    conn = connect_pg.connect()
    result = []

    try:
        query = """
            SELECT rc_id,rc_name,r_id
            FROM uniride.ur_rating_criteria
            WHERE r_id = %s
        """
        criterian_result = connect_pg.get_query(conn, query, (role,))

        for criteria in criterian_result:
            user_data = {
                "id": criteria[0],
                "name": criteria[1],
                "role": criteria[2],
            }
            result.append(user_data)

        return result
    finally:
        connect_pg.disconnect(conn)


def count_role(role):
    """Get number of user by role"""
    conn = connect_pg.connect()
    query = "SELECT COUNT(*) FROM uniride.ur_rating_criteria WHERE r_id = %s"
    result = connect_pg.get_query(conn, query, (role,))
    connect_pg.disconnect(conn)
    return result[0][0]


def average_rating_user_id(id_user):
    """Get average rating"""
    conn = connect_pg.connect()
    query = "SELECT ROUND(avg(n_value),2) FROM uniride.ur_rating WHERE u_id = %s"
    result = connect_pg.get_query(conn, query, (id_user,))
    connect_pg.disconnect(conn)
    return result[0][0]

def get_label(trip_id,user_id):
    """Get passenger label"""
    conn = connect_pg.connect()
    current_trip = get_trip_by_id(trip_id)
    if user_id == current_trip.get('driver_id'):
        query = "SELECT rc_id, rc_name, rc_description FROM uniride.ur_rating_criteria WHERE r_id = 2"
    else:
        query = "SELECT rc_id, rc_name, rc_description FROM uniride.ur_rating_criteria WHERE r_id = 1"
    result = connect_pg.get_query(conn, query)
    connect_pg.disconnect(conn)
    return result

