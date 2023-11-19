""" Field related functions"""

from uniride_sme.utils.exception.exceptions import InvalidInputException


def validate_fields(json_object, field_types):
    """
    Validate the presence and data types of fields in the json_object.

    Args:
        json_object (dict): The JSON object to validate.
        field_types (dict): A dictionary where keys are field names and values are expected data types.

    Returns:
        bool: True if all fields are present and have the correct data types, InvalidInputException otherwise.
    """

    for field, expected_type in field_types.items():
        if field not in json_object or not isinstance(json_object[field], expected_type):
            raise InvalidInputException("FIELD_VALIDATION_ERROR")
