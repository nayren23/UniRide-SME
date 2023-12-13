"""Documents service module"""
from flask import send_file
from datetime import datetime
from uniride_sme import app
from uniride_sme import connect_pg
from uniride_sme.model.bo.documents_bo import DocumentsBO
from uniride_sme.utils.file import save_file, delete_file
from uniride_sme.utils.exception.exceptions import MissingInputException
from uniride_sme.utils.exception.documents_exceptions import DocumentsNotFoundException
from uniride_sme.utils.file import get_encoded_file


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
        SET v_{document_type}_verified=0, v_timestamp_modification=CURRENT_TIMESTAMP
        WHERE u_id=%s;
        """
        values = (file_name, user_id, user_id)
        connect_pg.execute_command(conn, query, values)
        connect_pg.disconnect(conn)

    return file_name


def document_to_verify():
    """Get documents to verify"""
    conn = connect_pg.connect()
    query = """
        SELECT u_id, v_id, u_lastname, u_firstname, u_profile_picture, d_timestamp_modification,v_license_verified, v_id_card_verified,v_school_certificate_verified
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
        formatted_last_modified_date = datetime.strftime(document[5], "%Y-%m-%d %H:%M:%S")
        profile_picture_url = get_encoded_file(document[4])
        license_verified_str = str(document[6])
        id_card_verified_str = str(document[7])
        school_certificate_verified_str = str(document[8])
        license_zeros = license_verified_str.count("0")
        id_card_zeros = id_card_verified_str.count("0")
        school_certificate_zeros = school_certificate_verified_str.count("0")

        total_zeros = license_zeros + id_card_zeros + school_certificate_zeros

        request_data = {
            "request_number": document[1],
            "documents_to_verify": total_zeros,
            "person": {
                "id_user": document[0],
                "full_name": document[2] + " " + document[3],
                "last_modified_date": formatted_last_modified_date,
                "profile_picture": profile_picture_url,
            },
        }

        result.append(request_data)

    return result


def document_check(data):
    """Update document status"""
    user_id = data["user_id"]
    document_data = data["document"]

    conn = connect_pg.connect()
    connect_pg.disconnect(conn)

    document_type = document_data.get("type")
    status = document_data.get("status")
    column_mapping = {
        "license": "v_license_verified",
        "card": "v_id_card_verified",
        "school_certificate": "v_school_certificate_verified",
    }
    if document_type not in column_mapping:
        return {
            "user_id": user_id,
            "document": document_data,
            "success": False,
            "message": f"Type de document non pris en charge : {document_type}",
        }
    document_column = column_mapping[document_type]
    conn = connect_pg.connect()
    query = f"""
        UPDATE uniride.ur_document_verification
        SET {document_column} = %s
        WHERE u_id = %s
    """
    connect_pg.execute_command(conn, query, (status, user_id))
    connect_pg.disconnect(conn)
    result = {
        "user_id": user_id,
        "document": document_data,
        "success": True,
        "message": f"The document for {user_id} has been updated to {document_type}.",
    }

    return result


def document_user(user_id):
    """Get documents by user id"""
    conn = connect_pg.connect()
    query = """
        SELECT u_id, d_license, d_id_card, d_school_certificate, v_license_verified, v_id_card_verified, v_school_certificate_verified
        FROM uniride.ur_document_verification
        NATURAL JOIN uniride.ur_documents
        WHERE u_id = %s
    """
    document_data = connect_pg.get_query(conn, query, (user_id,), return_dict=True)
    connect_pg.disconnect(conn)

    if not document_data:
        return {
            "user_id": user_id,
            "documents": [],
            "success": False,
            "message": "Aucun document trouvé pour l'utilisateur.",
        }

    documents = []
    column_mapping = {
        "d_license": "license",
        "d_id_card": "card",
        "d_school_certificate": "school_certificate",
    }

    for document_row in document_data:
        document = []
        for column_name in document_row.keys():
            if column_name.startswith("d_"):
                document_type = column_mapping.get(column_name, None)
                if document_type:
                    document_url = document_row[column_name]
                    status_column = f"v_{column_name[2:]}_verified"
                    document_status = document_row.get(status_column, None)

                    document.append(
                        {
                            "url": document_url,
                            "status": str(document_status),
                            "type": document_type,
                        }
                    )

        documents.append({"document": document})

    return {
        "user_id": user_id,
        "documents": documents,
    }


def count_users():
    """Get number of users"""
    conn = connect_pg.connect()
    query = "SELECT COUNT(*) FROM uniride.ur_user"
    result = connect_pg.get_query(conn, query)
    connect_pg.disconnect(conn)
    return result[0][0]


