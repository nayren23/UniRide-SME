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
