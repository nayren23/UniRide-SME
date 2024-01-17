"""Criteria exceptions module"""
from uniride_sme.utils.exception.exceptions import ApiException


class TooManyCriteriaException(ApiException):
    """Exception for when the documents isn't found"""

    def __init__(self):
        super().__init__("TOO_MANY_CRITERIA", 417)
