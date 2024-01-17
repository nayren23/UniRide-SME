"""User role utils"""
from enum import Enum
from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from uniride_sme.utils.exception.exceptions import ForbiddenException


class RoleUser(Enum):
    """RoleUser Enum"""

    ADMINISTRATOR = 0
    DRIVER = 1
    PASSENGER = 2
    PENDING = 3


def role_required(role: RoleUser = RoleUser.PASSENGER):
    """Decorator to check if the user has the required role"""

    def decorator(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            try:
                user_role = get_jwt_identity()["role"]
                if role.value < user_role:
                    raise ForbiddenException("INVALID_ROLE")
                return func(*args, **kwargs)
            except ForbiddenException as e:
                return jsonify(message=e.message), e.status_code

        return wrapper

    return decorator
