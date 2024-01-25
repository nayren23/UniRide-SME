"""Documents service module"""
import os
from datetime import datetime
from uniride_sme import app, connect_pg
from uniride_sme.model.bo.documents_bo import DocumentsBO
from uniride_sme.utils.file import save_file, delete_file, get_encoded_file
from uniride_sme.service import user_service, admin_service
from uniride_sme.utils.exception.exceptions import MissingInputException
from uniride_sme.utils.exception.documents_exceptions import DocumentsNotFoundException, DocumentsTypeException


def get_documents_by_user_id(user_id) -> DocumentsBO:
    """Get user infos from db"""
    if not user_id:
        raise MissingInputException("USER_ID_MISSING")

    conn = connect_pg.connect()
    admin_service.verify_user(user_id)

    query = "SELECT * FROM uniride.ur_documents natural join uniride.ur_document_verification where u_id = %s"
    params = (user_id,)
    documents = connect_pg.get_query(conn, query, params, True)
    connect_pg.disconnect(conn)

    if not documents:
        raise DocumentsNotFoundException()
    documents = documents[0]
    document_bo = DocumentsBO(**documents)
    return document_bo


def add_documents(user_id, files) -> None:
    """Insert documents in the database"""
    if not user_id:
        raise MissingInputException("USER_ID_MISSING")

    conn = connect_pg.connect()
    admin_service.verify_user(user_id)

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
    except MissingInputException:
        pass
    try:
        save_id_card(user_id, files.get("id_card", None))
    except MissingInputException:
        pass

    try:
        save_school_certificate(user_id, files.get("school_certificate", None))
    except MissingInputException:
        pass

    try:
        save_insurance(user_id, files.get("insurance", None))
    except MissingInputException:
        pass

    try:
        save_license(user_id, files.get("license", None))
        save_id_card(user_id, files.get("id_card", None))
        save_school_certificate(user_id, files.get("school_certificate", None))
        save_insurance(user_id, files.get("insurance", None))
    except MissingInputException:
        pass


def save_license(user_id, file, old_file_name=None) -> None:
    """Save license"""
    _save_document(user_id, file, old_file_name, "license")


def save_id_card(user_id, file, old_file_name=None) -> None:
    """Save id card"""
    _save_document(user_id, file, old_file_name, "id_card")


def save_school_certificate(user_id, file, old_file_name=None) -> None:
    """Save school certificate"""
    _save_document(user_id, file, old_file_name, "school_certificate")


def save_insurance(user_id, file, old_file_name=None) -> None:
    """Save insurance"""
    _save_document(user_id, file, old_file_name, "insurance")


def _save_document(user_id, file, old_file_name, document_type) -> None:
    """Save document"""
    if not file:
        raise MissingInputException(f"MISSING_{document_type.upper()}_FILE")
    if file.filename == "":
        raise MissingInputException(f"MISSING_{document_type.upper()}_FILE")

    allowed_extensions = ["pdf", "png", "jpg", "jpeg"]
    directory = app.config[f"{document_type.upper()}_UPLOAD_FOLDER"]
    file_name = save_file(file, directory, allowed_extensions, user_id)

    if old_file_name and file_name != old_file_name:
        try:
            delete_file(old_file_name, directory)
        except FileNotFoundError:
            pass

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
        SELECT u_id, v_id, u_lastname, u_firstname, u_profile_picture, d_timestamp_modification,v_license_verified, v_id_card_verified,v_school_certificate_verified, v_insurance_verified
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
        if count_zero_and_minus_one(document) > 0:
            formatted_last_modified_date = datetime.strftime(document[5], "%Y-%m-%d %H:%M:%S")
            profile_picture_url = get_encoded_file(document[4], "PFP_UPLOAD_FOLDER")
            request_data = {
                "request_number": document[1],
                "documents_to_verify": count_zero_and_minus_one(document),
                "person": {
                    "id_user": document[0],
                    "first_name": document[2],
                    "last_name": document[3],
                    "last_modified_date": formatted_last_modified_date,
                    "profile_picture": profile_picture_url,
                },
            }

            result.append(request_data)

    return result


def count_zero_and_minus_one(document):
    """Count the number of zero and minus one in a document"""
    fields_to_check = [str(document[i]) for i in range(6, 10)]

    total_zeros = sum(field.count("0") for field in fields_to_check)
    total_minus_ones = sum(field.count("-1") for field in fields_to_check)

    return total_zeros + total_minus_ones


def document_number_status():
    """Get documents to verify"""
    conn = connect_pg.connect()
    query = """
        SELECT v_license_verified, v_id_card_verified, v_school_certificate_verified, v_insurance_verified
        FROM uniride.ur_document_verification
        """
    documents = connect_pg.get_query(conn, query)
    connect_pg.disconnect(conn)

    # Initialize counts for total across all attributes
    total_document_pending = 0
    total_document_ok = 0
    total_document_refused = 0

    if not documents:
        # If the query result is None, return counts initialized to 0
        return {
            "document_validated": 0,
            "document_pending": 0,
            "document_refused": 0,
        }

    attributes = ["v_license_verified", "v_id_card_verified", "v_school_certificate_verified", "v_insurance_verified"]

    for document in documents:
        for attribute in attributes:
            attribute_value = document[attributes.index(attribute)]

            # Update counts for each attribute
            total_document_pending += 1 if attribute_value == 0 else 0
            total_document_ok += 1 if attribute_value == 1 else 0
            total_document_refused += 1 if attribute_value == -1 else 0

    # Create a dictionary to store total counts
    result = {
        "document_validated": total_document_ok,
        "document_pending": total_document_pending,
        "document_refused": total_document_refused,
    }

    return result


def count_documents_status(document):
    """Count documents by status"""
    fields_to_check = [str(document[i]) for i in range(0, 4)]

    counts = {
        "document_pending": sum(field.count("0") for field in fields_to_check),
        "document_validated": sum(field.count("1") for field in fields_to_check),
        "document_refused": sum(field.count("-1") for field in fields_to_check),
    }

    return counts


def document_check(data):
    """Update document status"""
    user_id = data["user_id"]
    document_data = data["document"]

    conn = connect_pg.connect()
    connect_pg.disconnect(conn)
    admin_service.verify_user(user_id)

    document_type = document_data.get("type")
    status = document_data.get("status")
    description = document_data.get("description", "")

    column_mapping = {
        "license": {"status_column": "v_license_verified", "description_column": "v_license_description"},
        "card": {
            "status_column": "v_id_card_verified",
            "description_column": "v_card_description",
        },  # No description column for "card"
        "school_certificate": {
            "status_column": "v_school_certificate_verified",
            "description_column": "v_school_certificate_description",
        },
        "insurance": {"status_column": "v_insurance_verified", "description_column": "v_insurance_description"},
    }

    if document_type not in column_mapping:
        raise DocumentsTypeException()

    document_columns = column_mapping[document_type]
    status_column = document_columns["status_column"]
    description_column = document_columns.get("description_column")

    conn = connect_pg.connect()
    query = f"""
        UPDATE uniride.ur_document_verification
        SET {status_column} = %s
    """

    if description_column:
        query += f", {description_column} = %s"

    query += " WHERE u_id = %s"

    if description_column:
        connect_pg.execute_command(conn, query, (status, description, user_id))
    else:
        connect_pg.execute_command(conn, query, (status, user_id))

    connect_pg.disconnect(conn)

    update_role(user_id, status_column)

    return {"message": "DOCUMENT_STATUS_UPDATED"}


def update_role(user_id, column=None) -> None:
    """Update r_id to 1 if both v_license_verified and v_id_card_verified are 1"""

    user_bo = user_service.get_user_by_id(user_id)

    conn = connect_pg.connect()
    query = """
    SELECT v_license_verified, v_id_card_verified, v_school_certificate_verified, v_insurance_verified, d_license, d_id_card, d_school_certificate, d_insurance
    FROM uniride.ur_document_verification
    NATURAL JOIN uniride.ur_documents
    Where u_id = %s
    """
    documents = connect_pg.get_query(conn, query, (user_id,), True)
    if column and documents[0].get(column) == 1:
        match column:
            case "v_license_verified":
                delete_documents(documents,"LICENSE_UPLOAD_FOLDER","d_license")
            case "v_id_card_verified":
                delete_documents(documents,"ID_CARD_UPLOAD_FOLDER","d_id_card")
            case "v_school_certificate_verified":
                delete_documents(documents,"SCHOOL_CERTIFICATE_UPLOAD_FOLDER","d_school_certificate")
            case "v_insurance_verified":
                delete_documents(documents,"INSURANCE_UPLOAD_FOLDER","d_insurance")
            case _:
                pass

    if (
        user_bo.email_verified
        and documents[0].get("v_id_card_verified") == 1
        and documents[0].get("v_school_certificate_verified") == 1
    ):
        if documents[0].get("v_license_verified") == 1 and documents[0].get("v_insurance_verified") == 1:
            r_id = 1
        else:
            r_id = 2
    else:
        r_id = 3
    r_id_query = f"""
    UPDATE uniride.ur_user
    SET r_id = {r_id}
    WHERE u_id = %s
    """

    connect_pg.execute_command(conn, r_id_query, (user_id,))

    connect_pg.disconnect(conn)


def delete_documents(documents, folder_documents, id_doc) -> None:
    """Delete documents if they are verified"""
    if os.path.exists(os.path.join(app.config[folder_documents], documents[0].get(id_doc))):
        os.remove(os.path.join(app.config[folder_documents], documents[0].get(id_doc)))
    else:
        raise MissingInputException("MISSING_DOCUMENTS_FOLDER")


def document_user(user_id):
    """Get documents by user id"""
    conn = connect_pg.connect()
    admin_service.verify_user(user_id)

    query = """
        SELECT u_id, d_license, d_id_card, d_school_certificate, d_insurance, v_license_verified, v_id_card_verified, v_school_certificate_verified, v_insurance_verified, v_license_description, v_card_description, v_school_certificate_description, v_insurance_description 
        FROM uniride.ur_document_verification
        NATURAL JOIN uniride.ur_documents
        WHERE u_id = %s
    """
    document_data = connect_pg.get_query(conn, query, (user_id,), return_dict=True)
    connect_pg.disconnect(conn)

    if not document_data:
        raise DocumentsTypeException()

    documents = []
    column_mapping = {
        "d_license": {"type": "license", "folder": "LICENSE_UPLOAD_FOLDER", "description": "v_license_description"},
        "d_id_card": {"type": "card", "folder": "ID_CARD_UPLOAD_FOLDER", "description": "v_card_description"},
        "d_school_certificate": {
            "type": "school_certificate",
            "folder": "SCHOOL_CERTIFICATE_UPLOAD_FOLDER",
            "description": "v_school_certificate_description",
        },
        "d_insurance": {
            "type": "insurance",
            "folder": "INSURANCE_UPLOAD_FOLDER",
            "description": "v_insurance_description",
        },
    }

    for document_row in document_data:
        document = []
        for column_name in document_row.keys():
            if column_name.startswith("d_"):
                document_info = column_mapping.get(column_name, None)
                if document_info:
                    document_type = document_info["type"]
                    document_description = document_row.get(document_info["description"], None)
                    document_url = document_row[column_name]
                    status_column = f"v_{column_name[2:]}_verified"
                    document_status = document_row.get(status_column, None)
                    document.append(
                        {
                            "url": get_encoded_file(document_url, document_info["folder"]),
                            "status": str(document_status),
                            "type": document_type,
                            "description": document_description,
                        }
                    )

        documents.append({"document": document})

    return {
        "user_id": user_id,
        "documents": documents,
    }
