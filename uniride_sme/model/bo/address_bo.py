""" This module contains the AddressBO class. """
import dataclasses


@dataclasses.dataclass
class AddressBO:  # pylint: disable=too-many-instance-attributes
    """Address business object"""

    def __init__(  # pylint: disable=too-many-arguments, too-many-locals
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

    def get_full_address(self) -> str:
        """Return a simple concatenated full address string"""
        return f"{self.street_number} {self.street_name}, {self.city}, {self.postal_code}"
