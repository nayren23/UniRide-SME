""" This module contains the CarBO class. """


import dataclasses

@dataclasses.dataclass
class CarBO:
    """Car business object"""

    def __init__(
        self,
        car_id: int = None,
        model: str = None,
        license_plate: str = None,
        country_license_plate: str = None,
        color: str = None,
        brand: str = None,
        timestamp_addition = None,
        timestamp_modification=None,
        user_id: int = None

    ):
        self.id = car_id
        self.model = model
        self.license_plate = license_plate
        self.country_license_plate = country_license_plate
        self.color = color
        self.brand = brand
        self.timestamp_addition = timestamp_addition
        self.timestamp_modification = timestamp_modification
        self.user_id = user_id