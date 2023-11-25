""" This module contains the AddressBO class. """
import dataclasses


@dataclasses.dataclass
class AddressBO:
    """Address business object"""

    def __init__(
        self,
        address_id: str = None,
        street_number: str = None,
        street_name: str = None,
        city: str = None,
        postal_code: str = None,
        latitude: float = None,
        longitude: float = None,
        timestamp_modification=None,
    ):
        self.id = address_id
        self.street_number = street_number
        self.street_name = street_name
        self.city = city
        self.postal_code = postal_code
        self.latitude = latitude
        self.longitude = longitude
        self.timestamp_modification = timestamp_modification
