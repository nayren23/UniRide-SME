"""This module contains maths formulas """

import math


def haversine(lat1, lon1, lat2, lon2):
    """
    Harvesine formula.
    Returns the distance between the 2 coordinate in meters.
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    radius = 6371.0

    distance = radius * c

    return distance * 1000
