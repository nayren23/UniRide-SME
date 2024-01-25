"""Book related routes"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from uniride_sme.service import book_service, user_service
from uniride_sme.utils import email
from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.field import validate_fields
from uniride_sme.model.dto.book_dto import BookResponseDTO
from uniride_sme.utils.role_user import RoleUser, role_required

book = Blueprint("book", __name__, url_prefix="/book")


@book.route("", methods=["POST"])
@role_required()
def book_trip():
    """Book a trip endpoint"""

    response = jsonify({"message": "TRIP_BOOKED_SUCCESSFULLY"}), 200
    try:
        user_id = get_jwt_identity()["id"]
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


@book.route("/respond", methods=["PUT"])
@role_required(RoleUser.DRIVER)
def respond_booking():
    """Respond to a booking request endpoint"""

    response = jsonify({"message": "BOOKING_RESPONDED_SUCCESSFULLY"}), 200
    try:
        user_id = get_jwt_identity()["id"]
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
@role_required(RoleUser.DRIVER)
def get_bookings():
    """Get bookings endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        bookings = book_service.get_bookings(user_id)
        response = jsonify(bookings=bookings), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@book.route("/<trip_id>/cancel", methods=["DELETE"])
@role_required()
def cancel_request_trip(trip_id):
    """Cancel trip endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        book_service.cancel_request_trip(user_id, trip_id)
        response = jsonify({"message": "TRIP_CANCELED_SUCCESSFULLY"}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@book.route("/join", methods=["PUT"])
@role_required()
def join_booking():
    """Join a booking request endpoint"""

    response = jsonify({"message": "BOOKING_JOIN_SUCCESSFULLY"}), 200
    try:
        user_id = get_jwt_identity()["id"]
        json_object = request.json

        validate_fields(
            json_object,
            {
                "trip_id": int,
                "booker_id": int,
                "verification_code": int,
            },
        )
        book_service.join(
            json_object["trip_id"],
            user_id,
            json_object["booker_id"],
            json_object["verification_code"],
        )
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@book.route("/<trip_id>/code", methods=["GET"])
@role_required()
def get_code(trip_id):
    """Get verification code endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        verification_code = book_service.get_verification_code(trip_id, user_id)
        response = jsonify(verification_code=verification_code), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@book.route("/<trip_id>", methods=["GET"])
@role_required()
def get_booking(trip_id):
    """Get booking endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        booking = book_service.get_booking(trip_id, user_id)
        booking_dto = BookResponseDTO(
            accepted=booking.accepted,
            joined=booking.joined,
        )
        response = jsonify(booking_dto), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response
