"""Implementation of RouteChecker using OpenStreetMap""" ""
import requests

from uniride_sme.utils.cartography.route_checker import RouteChecker
from uniride_sme import app


class OpenStreetMapRouteChecker(RouteChecker):
    """Implementation of RouteChecker using OpenStreetMap"""

    def __init__(self):
        self.mode = "driving"
        self.api_base_url = "http://router.project-osrm.org/route/v1/"

    def check_if_route_is_viable(self, origin, destination, intermediate_point):
        """Check if the route is viable"""
        accept_time_difference_minutes = app.config["ACCEPT_TIME_DIFFERENCE_MINUTES"]

        # Format coordinates as required by the OpenStreetMap API
        origin_str = f"{origin[1]},{origin[0]}"
        intermediate_point_str = f"{intermediate_point[1]},{intermediate_point[0]}"
        destination_str = f"{destination[1]},{destination[0]}"

        # Construct the URL for the OpenStreetMap API
        api_url_origin_destination = (
            f"{self.api_base_url}{self.mode}/{origin_str};{destination_str}?overview=false&steps=false"
        )
        api_url_origin_intermediate = (
            f"{self.api_base_url}{self.mode}/{origin_str};{intermediate_point_str}?overview=false&steps=false"
        )
        api_url_intermediate_destination = (
            f"{self.api_base_url}{self.mode}/{intermediate_point_str};{destination_str}?overview=false&steps=false"
        )

        # Make the API requests
        response_initial = requests.get(api_url_origin_destination, timeout=5)
        response_intermediate = requests.get(api_url_origin_intermediate, timeout=5)
        response_destination = requests.get(api_url_intermediate_destination, timeout=5)

        data_initial = response_initial.json()
        data_intermediate = response_intermediate.json()
        data_destination = response_destination.json()

        if not (
            response_initial.status_code == 200
            and response_intermediate.status_code == 200
            and response_destination.status_code == 200
            and data_initial["code"] == "Ok"
            and data_intermediate["code"] == "Ok"
            and data_destination["code"] == "Ok"
            and data_initial.get("routes")
            and data_intermediate.get("routes")
            and data_destination.get("routes")
        ):
            return False

        route_initial = data_initial["routes"][0]
        route_intermediate = data_intermediate["routes"][0]
        route_destination = data_destination["routes"][0]

        initial_duration = route_initial["duration"]
        intermediate_duration = route_intermediate["legs"][0]["duration"]
        intermediate_destination_duration = route_destination["legs"][0]["duration"]

        new_duration = intermediate_duration + intermediate_destination_duration

        time_difference_minutes = (new_duration - initial_duration) / 60

        if time_difference_minutes <= accept_time_difference_minutes:
            return True
        return False

    def get_distance(self, origin, destination):
        """Get the distance between two points"""

        origin_str = f"{origin[1]},{origin[0]}"
        destination_str = f"{destination[1]},{destination[0]}"

        # Construct the URL for the OpenStreetMap API
        api_url = f"{self.api_base_url}{self.mode}/{origin_str};{destination_str}?overview=false&steps=false"

        # Make the API request
        response = requests.get(api_url, timeout=5)
        data = response.json()

        # Extract relevant information from the API response
        if response.status_code == 200 and data["code"] == "Ok" and data.get("routes"):
            route = data["routes"][0]["legs"][0]
            initial_distance = float(route["distance"] / 1000)  # Distance in kilometers
            return initial_distance
        return None
