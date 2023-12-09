"""Documents service module"""
from uniride_sme import app
from uniride_sme import connect_pg
from uniride_sme.model.bo.documents_bo import DocumentsBO
from uniride_sme.utils.file import save_file, delete_file
from uniride_sme.utils.exception.exceptions import MissingInputException
from uniride_sme.utils.exception.documents_exceptions import DocumentsNotFoundException


def get_documents_by_user_id(user_id):
    """Get user infos from db"""
    if not user_id:
        raise MissingInputException("USER_ID_MISSING")

    conn = connect_pg.connect()
    query = "SELECT * FROM uniride.ur_documents natural join uniride.ur_document_verification where u_id = %s"
    params = (user_id,)
    documents = connect_pg.get_query(conn, query, params, True)
    connect_pg.disconnect(conn)

    if not documents:
        raise DocumentsNotFoundException()
    documents = documents[0]
    document_bo = DocumentsBO(**documents)
    return document_bo


def add_documents(user_id, files):
    """Insert documents in the database"""
    if not user_id:
        raise MissingInputException("USER_ID_MISSING")

    conn = connect_pg.connect()
    query = """
    WITH first_insert AS (
        INSERT INTO uniride.ur_documents (u_id) VALUES (%s)
    )
    INSERT INTO uniride.ur_document_verification (u_id) VALUES (%s);
    """
    connect_pg.execute_command(conn, query, (user_id, user_id))
    connect_pg.disconnect(conn)
    try:
        save_license(user_id, files.get("license", None))
        save_id_card(user_id, files.get("id_card", None))
        save_school_certificate(user_id, files.get("school_certificate", None))
    except MissingInputException:
        pass


def save_license(user_id, file, old_file_name=None):
    """Save license"""
    _save_document(user_id, file, old_file_name, "license")


def save_id_card(user_id, file, old_file_name=None):
    """Save id card"""
    _save_document(user_id, file, old_file_name, "id_card")


def save_school_certificate(user_id, file, old_file_name=None):
    """Save school certificate"""
    _save_document(user_id, file, old_file_name, "school_certificate")


def _save_document(user_id, file, old_file_name, document_type):
    """Save document"""
    if not file:
        raise MissingInputException(f"MISSING_{document_type.upper()}_FILE")
    if file.filename == "":
        raise MissingInputException(f"MISSING_{document_type.upper()}_FILE")

    allowed_extensions = ["pdf", "png", "jpg", "jpeg"]
    directory = app.config[f"{document_type.upper()}_UPLOAD_FOLDER"]
    file_name = save_file(file, directory, allowed_extensions, user_id)

    if old_file_name and file_name != old_file_name:
        delete_file(old_file_name, directory)

    if not old_file_name or file_name != old_file_name:
        conn = connect_pg.connect()
        query = f"""
        WITH first_update AS (
            UPDATE uniride.ur_documents
            SET d_{document_type}=%s, d_timestamp_modification=CURRENT_TIMESTAMP
            WHERE u_id=%s
        )
        UPDATE uniride.ur_document_verification
        SET v_{document_type}_verified=false, v_timestamp_modification=CURRENT_TIMESTAMP
        WHERE u_id=%s;
        """
        values = (file_name, user_id, user_id)
        connect_pg.execute_command(conn, query, values)
        connect_pg.disconnect(conn)

    return file_name


from datetime import datetime

def document_to_verify():
    conn = connect_pg.connect()
    query = """
        SELECT u_id, v_id, u_lastname, u_firstname, u_profile_picture, d_timestamp_modification,
               v_license_verified::int + v_id_card_verified::int + v_school_certificate_verified::int
        FROM uniride.ur_document_verification
        NATURAL JOIN uniride.ur_user
        NATURAL JOIN uniride.ur_documents
        WHERE u_id = u_id
    """
    documents = connect_pg.get_query(conn, query)
    connect_pg.disconnect(conn)

    # Create a list to store documents with attributes
    result = []

    for document in documents:
        last_modified_datetime = document[5]
        formatted_last_modified_date = datetime.strftime(last_modified_datetime, "%Y-%m-%d %H:%M:%S")
        #profile_picture_url = f'https://example.com/images/{document[4]}'
        #Vrai url du serveur d'image
        profile_picture_url = f'/Users/chefy/Desktop/SAE_BACK/UniRide-SME/documents/pft/{document[4]}'
        
        request_data = {
            'id_user':document[0],
            'request_number': document[1],
            'documents_to_verify': document[6],
            'person': {
                'full_name': document[2] + " " + document[3],
                'last_modified_date': formatted_last_modified_date,
                'profile_picture': profile_picture_url,
            }
        }

        result.append(request_data)

    return result




