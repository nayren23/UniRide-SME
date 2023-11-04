"""Standard Exceptions"""


class ApiException(Exception):
    """Exception for the API"""

    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code


class InternalServerErrorException(ApiException):
    """Exception for internal server error"""

    def __init__(self):
        super().__init__("INTERNAL_SERVER_ERROR", 500)


class InvalidInputException(ApiException):
    """Exception for invalid input"""

    def __init__(self, message):
        super().__init__(message, 422)


class MissingInputException(ApiException):
    """Exception for missing input"""

    def __init__(self, message):
        super().__init__(message, 400)


class FileException(ApiException):
    """Exception for file related errors"""

    def __init__(self, message, status_code):
        super().__init__(message, status_code)


class EmailException(ApiException):
    """Exception for email related errors"""

    def __init__(self, message, status_code):
        super().__init__(message, status_code)
