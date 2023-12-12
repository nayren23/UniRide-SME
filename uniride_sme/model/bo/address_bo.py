""" This module contains the AddressBO class. """
import dataclasses


@dataclasses.dataclass
class AddressBO:  # pylint: disable=too-many-instance-attributes
    """Address business object"""

    id: str = None
    street_number: str = None
    street_name: str = None
    city: str = None
    postal_code: str = None
    latitude: float = None
    longitude: float = None
    timestamp_modification = None

    def get_full_address(self) -> str:
        """Return a simple concatenated full address string"""
        return f"{self.street_number} {self.street_name}, {self.city}, {self.postal_code}"
