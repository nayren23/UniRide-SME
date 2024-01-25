"""Contains the business object of the trip"""
import dataclasses
from datetime import datetime

from uniride_sme import app
from uniride_sme.model.bo.address_bo import AddressBO
from uniride_sme.utils.cartography.route_checker_factory import RouteCheckerFactory


@dataclasses.dataclass
class TripBO:  # pylint: disable=too-many-instance-attributes
    """Business object of the trip"""

    id: int = None
    passenger_count: int = None
    total_passenger_count: int = None
    timestamp_creation: datetime = None
    timestamp_proposed: datetime = None
    status: int = None  # En cours en attente annulé terminé
    price: float = None
    user_id: int = None
    departure_address: AddressBO = None
    arrival_address: AddressBO = None
    route_checker = RouteCheckerFactory.create_route_checker(app.config["ROUTE_CHECKER"])
