"""This module contains decorators for the app"""
from functools import wraps
from uniride_sme import app


def with_app_context(func):
    """Decorator to add app context to a function"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with app.app_context():
            return func(*args, **kwargs)

    return wrapper
