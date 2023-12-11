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
        SET v_{document_type}_verified=0, v_timestamp_modification=CURRENT_TIMESTAMP
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
        last_modified_datetime = document[5]
        formatted_last_modified_date = datetime.strftime(last_modified_datetime, "%Y-%m-%d %H:%M:%S")
        #profile_picture_url = f'https://example.com/images/{document[4]}'
        #Vrai url du serveur d'image
        profile_picture_url = f'/Users/chefy/Desktop/SAE_BACK/UniRide-SME/documents/pft/{document[4]}'
        
        license_verified_str = str(document[6])
        id_card_verified_str = str(document[7])
        school_certificate_verified_str = str(document[8])
         # Count the number of zeros for each verification field
        count_license_verified_zeros = license_verified_str.count('0')
        count_id_card_verified_zeros = id_card_verified_str.count('0')
        count_school_certificate_verified_zeros = school_certificate_verified_str.count('0')

        # Total count of zeros
        total_zeros = count_license_verified_zeros + count_id_card_verified_zeros + count_school_certificate_verified_zeros


        request_data = {
            'request_number': total_zeros,
            'documents_to_verify': document[6],
            'person': {
                'id_user':document[0],
                'full_name': document[2] + " " + document[3],
                'last_modified_date': formatted_last_modified_date,
                'profile_picture': profile_picture_url,
            }
        }

        result.append(request_data)

    return result







def document_check(data):
    # Assurez-vous que toutes les données nécessaires sont présentes
    if 'user_id' not in data or 'document' not in data:
        return {
            'success': False,
            'message': "Les données fournies sont incomplètes. Assurez-vous d'inclure 'user_id' et 'document'.",
        }

    user_id = data['user_id']
    document_data = data['document']

    # Vérifiez si l'utilisateur existe avant de procéder à la mise à jour
    conn = connect_pg.connect()
    user_exists_query = "SELECT COUNT(*) FROM uniride.ur_user WHERE u_id = %s"
    user_exists = connect_pg.get_query(conn, user_exists_query, (user_id,))[0][0]
    connect_pg.disconnect(conn)

    if user_exists == 0:
        return {
            'user_id': user_id,
            'document': document_data,
            'success': False,
            'message': f"L'utilisateur avec l'ID {user_id} n'existe pas.",
        }

    document_type = document_data.get('type')
    status = document_data.get('status')

    if not document_type or status is None:
        return {
            'user_id': user_id,
            'document': document_data,
            'success': False,
            'message': "Les informations du document sont incomplètes. Assurez-vous d'inclure 'type' et 'status' dans 'document'.",
        }

    column_mapping = {
        'license': 'v_license_verified',
        'card': 'v_id_card_verified',
        'school_certificate': 'v_school_certificate_verified'
        # Ajoutez d'autres types de document au besoin
    }

    # Assurez-vous que le type de document est pris en charge
    if document_type not in column_mapping:
        return {
            'user_id': user_id,
            'document': document_data,
            'success': False,
            'message': f"Type de document non pris en charge : {document_type}",
        }

    document_column = column_mapping[document_type]

    # Utilisez une clause WHERE pour spécifier les conditions de mise à jour
    conn = connect_pg.connect()
    query = f"""
        UPDATE uniride.ur_document_verification
        SET {document_column} = %s
        WHERE u_id = %s
    """
    
    # Exécutez la requête en passant les valeurs nécessaires
    connect_pg.execute_command(conn, query, (status, user_id))
    
    connect_pg.disconnect(conn)

    # Créez une structure de résultat dans le format spécifié
    result = {
        'user_id': user_id,
        'document': document_data,
        'success': True,
        'message': f"Le statut du document {document_type} pour l'utilisateur {user_id} a été mis à jour.",
    }

    return result




def document_user(user_id):
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
            'user_id': user_id,
            'documents': [],
            'success': False,
            'message': "Aucun document trouvé pour l'utilisateur.",
        }

    documents = []
    # Mapper les noms de colonnes aux types de documents
    column_mapping = {
        'd_license': 'license',
        'd_id_card': 'card',
        'd_school_certificate': 'school_certificate',
    }


    for document_row in document_data:
        document = []
        for column_name in document_row.keys():
            if column_name.startswith('d_'):
                document_type = column_mapping.get(column_name, None)
                if document_type:
                    document_url = document_row[column_name]
                    status_column = f'v_{column_name[2:]}_verified'
                    document_status = document_row.get(status_column, None)

                    document.append({
                        'url': document_url,
                        'status': str(document_status),
                        'type': document_type,
                    })

        documents.append({'document': document})

    return {
        'user_id': user_id,
        'documents': documents,
    
    }

def count_users():
    conn = connect_pg.connect()
    query = "SELECT COUNT(*) FROM uniride.ur_user"
    result = connect_pg.get_query(conn, query)
    connect_pg.disconnect(conn)

    # Assurez-vous que le résultat est une liste non vide avant d'extraire la première valeur
    if result and isinstance(result, list) and result[0]:
        return result[0][0]
    else:
        return None  # Ou une valeur par défaut selon votre logique


