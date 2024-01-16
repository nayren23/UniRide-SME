"""Admin service module"""
from uniride_sme.utils.file import get_encoded_file
from uniride_sme import app
from uniride_sme import connect_pg
from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,
)
from uniride_sme.utils.exception.user_exceptions import (
    UserNotFoundException,
    RatingNotFoundException,
)
from uniride_sme.utils.exception.criteria_exceptions import TooManyCriteriaException



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
    print(result, "RESULT")
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
