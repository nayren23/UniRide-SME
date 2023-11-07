"""Exceptions for AddressBO endpoints"""

from uniride_sme.utils.exception.exceptions import ApiException

class AddressNotFoundException(ApiException):
    """Exception for when the address isn't found"""

    def __init__(self):
        super().__init__("ADDRESS_NOT_FOUND", 422)
        

class InvalidAddressException(ApiException):
    """Exception for when an invalid address is encountered"""

    def __init__(self):
        super().__init__("INVALID_ADDRESS", 422)


class MissingInputException(ApiException):
    """Exception for missing input"""

    def __init__(self, message):
        super().__init__(message, 400)
        
#If an intermediate address is not the university, raise an exception
class InvalidIntermediateAddressException(ApiException):
    """Exception for when an invalid intermediate address is encountered"""

    def __init__(self):
        super().__init__("INVALID_INTERMEDIATE_ADDRESS", 422)

class InvalidInputException(ApiException):
    """Exception for invalid input"""

    def __init__(self, message):
        super().__init__(message, 422)