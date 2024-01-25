""" This module contains the CarBO class. """

import dataclasses
from typing import Optional
from datetime import datetime


@dataclasses.dataclass
class CarBO:  # pylint: disable=too-many-instance-attributes
    """Car business object"""

    id: Optional[int] = None
    model: Optional[str] = None
    license_plate: Optional[str] = None
    country_license_plate: Optional[str] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    timestamp_addition: Optional[datetime] = None
    timestamp_modification: Optional[datetime] = None
    user_id: Optional[int] = None
    total_places: Optional[int] = None
