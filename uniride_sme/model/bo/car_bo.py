""" This module contains the CarBO class. """

import dataclasses
from typing import Optional


@dataclasses.dataclass
class CarBO:  # pylint: disable=too-many-instance-attributes
    """Car business object"""

    id: Optional[int] = None
    model: Optional[str] = None
    license_plate: Optional[str] = None
    country_license_plate: Optional[str] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    timestamp_addition: Optional[str] = None
    timestamp_modification: Optional[str] = None
    user_id: Optional[int] = None
    total_places: Optional[int] = None
