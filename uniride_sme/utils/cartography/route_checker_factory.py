"""Factory for creating instances of RouteChecker"""

from uniride_sme.utils.cartography.google_maps_route_checker import GoogleMapsRouteChecker
from uniride_sme.utils.cartography.open_street_map_route_checker import OpenStreetMapRouteChecker
from uniride_sme.utils.exception.exceptions import MissingInputException


class RouteCheckerFactory:
    """Factory for creating instances of RouteChecker"""

    @staticmethod
    def create_route_checker(route_checker_choice):
        """Create an instance of RouteChecker"""
        match route_checker_choice:
            case "google":
                return GoogleMapsRouteChecker()

            case "osm":
                return OpenStreetMapRouteChecker()

            case _:
                raise MissingInputException("INVALID_ROUTE_CHECKER_CHOICE_ENVIRONMENT_VARIABLE")
