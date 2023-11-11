"""Implementation of RouteChecker using Google Maps API"""
from datetime import datetime
import googlemaps

from uniride_sme.utils.cartography.route_checker import RouteChecker
from uniride_sme import app


class GoogleMapsRouteChecker(RouteChecker):
    """Implementation of RouteChecker using Google Maps API"""

    def __init__(self):
        self.google_api_key = app.config["GOOGLE_API_KEY"]
        self.mode = "driving"

    def check_if_route_is_viable(self, origin, destination, intermediate_point):
        """Check if the route is viable"""

        accept_time_difference_minutes = app.config["ACCEPT_TIME_DIFFERENCE_MINUTES"]  # TODO:change the time difference

        now = datetime.now()

        # Calculate the initial route
        gmaps = googlemaps.Client(key=self.google_api_key)

        initial_route = gmaps.directions(origin, destination, self.mode, departure_time=now)

        # Calculate the initial route with the intermediate point
        route_initial_intermediate = gmaps.directions(origin, intermediate_point, self.mode, departure_time=now)

        route_with_intermediate = gmaps.directions(intermediate_point, destination, self.mode, departure_time=now)

        # Check if the route is viable
        initial_duration = initial_route[0]["legs"][0]["duration"]["value"]  # Seconds
        intermediate_duration = route_initial_intermediate[0]["legs"][0]["duration"]["value"]  # Seconds
        intermediate_destination_duration = route_with_intermediate[0]["legs"][0]["duration"]["value"]  # Seconds

        new_duration = intermediate_duration + intermediate_destination_duration

        time_difference_minutes = (new_duration - initial_duration) / 60  # Difference time in seconds

        if not time_difference_minutes <= accept_time_difference_minutes:
            return False

        return True

    def get_distance(self, origin, destination):
        """Get the distance between two points"""
        now = datetime.now()

        gmaps = googlemaps.Client(key=self.google_api_key)

        initial_route = gmaps.directions(origin, destination, self.mode, departure_time=now)

        initial_distance = float(initial_route[0]["legs"][0]["distance"]["value"] / 1000)  # Distance en kilomètres
        print("initial_distancetype", type(initial_distance))

        return initial_distance
