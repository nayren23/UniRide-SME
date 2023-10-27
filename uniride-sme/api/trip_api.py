"""Trip related routes"""
from flask import Blueprint, request, jsonify

from models.bo.trip_bo import TripBO

trip = Blueprint("trip", __name__)

@trip.route("/trip/register", methods=["GET"])
def register():
    """Sign up endpoint"""
    response = jsonify({"message": "USER_CREATED_SUCCESSFULLY"}), 200

    return response


