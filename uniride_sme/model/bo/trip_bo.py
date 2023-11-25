"""Contains the business object of the trip"""

from uniride_sme import app
from uniride_sme.model.bo.address_bo import AddressBO
from uniride_sme.utils.cartography.route_checker_factory import RouteCheckerFactory


class TripBO:
    """Business object of the trip"""

    def __init__(
        self,
        trip_id: int = None,
        total_passenger_count: int = None,
        timestamp_creation=None,
        timestamp_proposed=None,
        status: int = None,  # En cours, en attente, annulé, terminé
        price: float = None,
        user_id: int = None,
        depart_address_bo: AddressBO = None,
        arrival_address_bo: AddressBO = None,
    ):
        self.id = trip_id
        self.total_passenger_count = total_passenger_count
        self.timestamp_creation = timestamp_creation
        self.timestamp_proposed = timestamp_proposed
        self.status = status
        self.price = price
        self.user_id = user_id
        self.choice_route_checker = app.config["ROUTE_CHECKER"]
        self.route_checker = RouteCheckerFactory.create_route_checker(self.choice_route_checker)

        self.departure_address = depart_address_bo
        self.arrival_address = arrival_address_bo
