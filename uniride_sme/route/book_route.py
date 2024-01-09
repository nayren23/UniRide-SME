"""Book related routes"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from uniride_sme.service import book_service, user_service
from uniride_sme.utils import email
from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.field import validate_fields

book = Blueprint("book", __name__, url_prefix="/book")


@book.route("", methods=["POST"])
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
        response = jsonify(message=e.message), e.status_code

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
        booker = user_service.get_user_by_id(json_object["booker_id"])
        email.send_reservation_response_email(booker.student_email, booker.firstname, json_object["trip_id"])
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@book.route("/requests", methods=["GET"])
@jwt_required()
def get_bookings():
    """Respond to a booking request endpoint"""
    try:
        user_id = get_jwt_identity()
        bookings = book_service.get_bookings(user_id)
        response = jsonify(bookings=bookings), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response

@book.route("/cancel", methods=["Delete"])
@jwt_required()
def cancel_request_trip():
    """Cancel trip endpoint"""
    try:
        user_id = get_jwt_identity()
        request_data = request.get_json()
        trip_id = request_data.get("trip_id")
        book_service.cancel_request_trip(user_id, trip_id)
        response = jsonify({"message": "TRIP_CANCELED_SUCCESSFULLY"}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response
