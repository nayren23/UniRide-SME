"""Document_Verification service module"""
from uniride_sme import app
from uniride_sme import connect_pg
from uniride_sme.model.bo.documents_bo import DocumentsBO
from uniride_sme.utils.file import save_file, delete_file
from uniride_sme.utils.exception.exceptions import MissingInputException
from uniride_sme.utils.exception.documents_exceptions import DocumentsNotFoundException

def document_to_verify_number():
    conn = connect_pg.connect()
    query = "SELECT * FROM uniride.ur_document_verification natural join uniride.ur_user where u_id = u_id"
    documents = connect_pg.get_query(conn, query)
    connect_pg.disconnect(conn)

    
    return documents
    
