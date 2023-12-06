"""Contains the business object of the trip"""
import dataclasses

from uniride_sme import app
from uniride_sme.model.bo.address_bo import AddressBO
from uniride_sme.utils.cartography.route_checker_factory import RouteCheckerFactory


@dataclasses.dataclass
class TripBO:
    """Business object of the trip"""

    def __init__(
        self,
        trip_id: int = None,
        passenger_count: int = None,
        total_passenger_count: int = None,
        timestamp_creation=None,
        timestamp_proposed=None,
        status: int = None,  # En cours, en attente, annulé, terminé
        price: float = None,
        user_id: int = None,
        departure_address_bo: AddressBO = None,
        arrival_address_bo: AddressBO = None,
    ):
        self.id = trip_id
        self.passenger_count = passenger_count
        self.total_passenger_count = total_passenger_count
        self.timestamp_creation = timestamp_creation
        self.timestamp_proposed = timestamp_proposed
        self.status = status
        self.price = price
        self.user_id = user_id
        self.choice_route_checker = app.config["ROUTE_CHECKER"]
        self.route_checker = RouteCheckerFactory.create_route_checker(self.choice_route_checker)

        self.departure_address = departure_address_bo
        self.arrival_address = arrival_address_bo

    def __repr__(self) -> str:
        return f"TripBO({self.id}, {self.total_passenger_count}, {self.timestamp_creation}, {self.timestamp_proposed}, {self.status}, {self.price}, {self.user_id}, {self.departure_address}, {self.arrival_address})"
