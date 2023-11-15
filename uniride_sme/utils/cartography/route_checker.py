"""Abstract class for checking route viability and getting distance"""

from abc import ABC, abstractmethod


class RouteChecker(ABC):
    """Abstract class for checking route viability and getting distance"""

    @abstractmethod
    def check_if_route_is_viable(self, origin, destination, intermediate_point):
        """Check if the route is viable"""

    @abstractmethod
    def get_distance(self, origin, destination):
        """Get the distance between two points"""
