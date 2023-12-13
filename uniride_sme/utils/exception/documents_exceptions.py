"""Documents exceptions module"""
from uniride_sme.utils.exception.exceptions import ApiException


class DocumentsNotFoundException(ApiException):
    """Exception for when the documents isn't found"""

    def __init__(self):
        super().__init__("DOCUMENTS_NOT_FOUND", 422)
