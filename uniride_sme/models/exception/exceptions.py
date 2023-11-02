"""Standard Exceptions"""


class ApiException(Exception):
    """Exception for the API"""

    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code