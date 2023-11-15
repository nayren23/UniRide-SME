"""TripStatus Enum"""
from enum import Enum


class TripStatus(Enum):
    """TripStatus Enum"""

    PENDING = 1
    CANCELED = 2
    COMPLETED = 3
    ONCOURSE = 4
