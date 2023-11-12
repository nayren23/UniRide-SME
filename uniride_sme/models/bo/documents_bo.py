"""User business owner"""
from uniride_sme import app
from uniride_sme import connect_pg
from uniride_sme.utils.file import save_file, delete_file
from uniride_sme.utils.exception.exceptions import (
    MissingInputException,
)


class DocumentsBO:
    """Documents business owner class"""

    def __init__(self, u_id: int):
        self.u_id = u_id

    def get_from_db(self):
        """Get user infos from db"""
        if not self.u_id:
            raise MissingInputException("USER_ID_MISSING")

        # get documents
        query = "select * from uniride.ur_documents where u_id = %s"
        params = (self.u_id,)

        conn = connect_pg.connect()
        infos = connect_pg.get_query(conn, query, params, True)
        for key in infos[0]:
            setattr(self, key, infos[0][key])

        # get document verification
        query = "select * from uniride.ur_document_verification where u_id = %s"
        params = (self.u_id,)
        conn = connect_pg.connect()
        infos = connect_pg.get_query(conn, query, params, True)
        for key in infos[0]:
            setattr(self, key, infos[0][key])

    def add_in_db(self, files):
        """Insert documents in the database"""
        query = "INSERT INTO uniride.ur_documents (u_id) VALUES (%s)"
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, (self.u_id,))

        query = "INSERT INTO uniride.ur_document_verification (u_id) VALUES (%s)"
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, (self.u_id,))
        self.get_from_db()
        try:
            self.save_license(files)
            self.save_id_card(files)
            self.save_school_certificate(files)
        except MissingInputException:
            pass

    def save_license(self, files):
        """Save license"""
        self.d_license = self._save_document(files, self.d_license, "license")

    def save_id_card(self, files):
        """Save id card"""
        self.d_id_card = self._save_document(files, self.d_id_card, "id_card")

    def save_school_certificate(self, files):
        """Save school certificate"""
        self.d_school_certificate = self._save_document(
            files, self.d_school_certificate, "school_certificate"
        )

    def _save_document(self, files, old_file_name, document_type):
        """Save document"""
        if document_type not in files:
            raise MissingInputException(f"MISSING_{document_type.upper()}_FILE")
        file = files[document_type]
        if file.filename == "":
            raise MissingInputException(f"MISSING_{document_type.upper()}_FILE")

        allowed_extensions = ["pdf", "png", "jpg", "jpeg"]
        directory = app.config[f"{document_type.upper()}_UPLOAD_FOLDER"]
        file_name = save_file(file, directory, allowed_extensions, self.u_id)
        try:
            if old_file_name and file_name != old_file_name:
                delete_file(old_file_name, directory)
        except FileNotFoundError:
            pass
        query = f"UPDATE uniride.ur_documents SET d_{document_type}=%s, d_timestamp_modification=CURRENT_TIMESTAMP WHERE u_id=%s"
        values = (file_name, self.u_id)
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, values)

        query = f"UPDATE uniride.ur_document_verification SET v_{document_type}_verified=false, v_timestamp_modification=CURRENT_TIMESTAMP WHERE u_id=%s"
        values = (self.u_id,)
        conn = connect_pg.connect()
        connect_pg.execute_command(conn, query, values)
        return file_name
