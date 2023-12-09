"""Book business object module"""
import dataclasses


@dataclasses.dataclass
class BookBO:
    """Book business object class"""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        user_id: int = None,
        trip_id: int = None,
        accepted: int = None,
        passenger_count: int = None,
        date_requested=None,
    ):
        self.user_id = user_id
        self.trip_id = trip_id
        self.accepted = accepted
        self.passenger_count = passenger_count
        self.date_requested = date_requested
