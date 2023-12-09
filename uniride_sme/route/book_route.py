"""Book related routes"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from uniride_sme.service import book_service

from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.field import validate_fields

book = Blueprint("book", __name__, url_prefix="/book")


@book.route("/", methods=["POST"])
@jwt_required()
def book_trip():
    """Book a trip endpoint"""

    response = jsonify({"message": "TRIP_BOOKED_SUCCESSFULLY"}), 200
    try:
        user_id = get_jwt_identity()
        json_object = request.json

        validate_fields(
            json_object,
            {
                "trip_id": int,
                "passenger_count": int,
            },
        )
        book_service.book_trip(json_object["trip_id"], user_id, json_object["passenger_count"])
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@book.route("/respond", methods=["POST"])
@jwt_required()
def respond_booking():
    """Respond to a booking request endpoint"""

    response = jsonify({"message": "BOOKING_RESPONDED_SUCCESSFULLY"}), 200
    try:
        user_id = get_jwt_identity()
        json_object = request.json

        validate_fields(
            json_object,
            {
                "trip_id": int,
                "booker_id": int,
                "response": int,
            },
        )
        book_service.respond_booking(json_object["trip_id"], user_id, json_object["booker_id"], json_object["response"])
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response
