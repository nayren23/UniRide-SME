"""Trip related routes"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from uniride_sme.model.bo.trip_bo import TripBO
from uniride_sme.model.bo.address_bo import AddressBO
from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.trip_status import TripStatus
from uniride_sme.utils.field import validate_fields
from uniride_sme.utils.pagination import create_pagination
from uniride_sme.service import trip_service
from uniride_sme.utils.email import send_cancelation_email
from uniride_sme.utils.role_user import RoleUser, role_required

trip = Blueprint("trip", __name__, url_prefix="/trip")


@trip.route("/propose", methods=["POST"])
@role_required(RoleUser.DRIVER)
def propose_trip():
    """Propose a trip endpoint
    "We define the  price of the trip and the status of the trip as pending
    """

    response = jsonify({"message": "TRIP_CREATED_SUCCESSFULLY"}), 200
    try:
        user_id = get_jwt_identity()["id"]
        json_object = request.json

        validate_fields(
            json_object,
            {
                "total_passenger_count": int,
                "timestamp_proposed": str,
                "address_departure_id": int,
                "address_arrival_id": int,
            },
        )

        trip_bo = TripBO(
            total_passenger_count=json_object.get("total_passenger_count", None),
            timestamp_proposed=json_object.get("timestamp_proposed", None).strip(),
            user_id=user_id,
            departure_address=AddressBO(id=json_object.get("address_departure_id", None)),
            arrival_address=AddressBO(id=json_object.get("address_arrival_id", None)),
            status=TripStatus.PENDING.value,
        )
        trip_service.add_trip(trip_bo)
        response = jsonify({"message": "CREATED_SUCCESSFULLY", "trip_id": trip_bo.id}), 200

    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@trip.route("", methods=["POST"])
@role_required()
def get_available_trips():
    """Get all the available trips endpoint"""

    try:
        json_object = request.json

        validate_fields(request.json, {"departure": dict, "arrival": dict, "trip": dict})
        validate_fields(
            json_object["departure"], {"street_number": str, "street_name": str, "city": str, "postal_code": str}
        )
        validate_fields(
            json_object["arrival"], {"street_number": str, "street_name": str, "city": str, "postal_code": str}
        )
        validate_fields(json_object["trip"], {"passenger_count": int, "departure_date": str})

        departure_address_bo = AddressBO(
            street_number=(json_object.get("departure").get("street_number", None)).strip(),
            street_name=json_object.get("departure").get("street_name", None).strip(),
            city=json_object.get("departure").get("city", None).strip(),
            postal_code=json_object.get("departure").get("postal_code", None).strip(),
        )

        address_arrival_bo = AddressBO(
            street_number=json_object.get("arrival").get("street_number", None).strip(),
            street_name=json_object.get("arrival").get("street_name", None).strip(),
            city=json_object.get("arrival").get("city", None).strip(),
            postal_code=json_object.get("arrival").get("postal_code", None).strip(),
        )

        trip_bo = TripBO(
            total_passenger_count=json_object.get("trip").get("passenger_count", None),
            timestamp_proposed=json_object.get("trip").get("departure_date", None),
        )
        trip_bo.departure_address = departure_address_bo
        trip_bo.arrival_address = address_arrival_bo

        available_trips = trip_service.get_available_trips_to(trip_bo)

        # We need to paginate the data
        meta, paginated_data = create_pagination(request, available_trips)

        response = jsonify({"trips": paginated_data, "meta": meta}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@trip.route("/driver/current", methods=["GET"])
@role_required(RoleUser.DRIVER)
def get_current_driver_trips():
    """Get all the current trips of a driver"""
    try:
        user_id = get_jwt_identity()["id"]
        available_trips = trip_service.get_driver_trips(user_id)
        # We need to paginate the data
        # TODO : add pagination
        meta, paginated_data = create_pagination(request, available_trips)
        response = jsonify({"trips": available_trips, "meta": meta}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@trip.route("/<trip_id>", methods=["GET"])
@role_required()
def get_trip(trip_id):
    """Get a trip by id endpoint"""
    try:
        trip_detailed_dto = trip_service.get_trip_by_id(trip_id)
        response = jsonify(trip_detailed_dto), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@trip.route("/<trip_id>/passengers", methods=["GET"])
@role_required()
def passengers(trip_id: int):
    """Get trip passengers endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        passengers_list = trip_service.get_passengers(trip_id, user_id)
        response = jsonify(passengers_list), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@trip.route("/<trip_id>/start", methods=["PUT"])
@role_required(RoleUser.DRIVER)
def start_trip(trip_id: int):
    """Start trip endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        trip_service.start_trip(trip_id, user_id)
        response = jsonify(message="TRIP_STARTED_SUCCESSFULLY"), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@trip.route("/<trip_id>/end", methods=["PUT"])
@role_required(RoleUser.DRIVER)
def end_trip(trip_id: int):
    """End trip endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        trip_service.end_trip(trip_id, user_id)
        response = jsonify(message="TRIP_ENDED_SUCCESSFULLY"), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@trip.route("/<trip_id>/cancel", methods=["PUT"])
@role_required(RoleUser.DRIVER)
def cancel_trip(trip_id: int):
    """Cancel trip endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        trip_service.cancel_trip(trip_id, user_id)
        passengers_emails = trip_service.get_passengers_emails(trip_id)
        for passenger in passengers_emails:
            send_cancelation_email(passenger["email"], passenger["firstname"], trip_id)
        response = jsonify(message="TRIP_CANCELED_SUCCESSFULLY"), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@trip.route("/passenger/current", methods=["GET"])
@role_required()
def passenger_current_trip():
    """Get passenger current trip endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        passenger_current_trips_result = trip_service.passenger_current_trips(user_id)
        response = jsonify(passenger_current_trips_result), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@trip.route("/rating", methods=["POST"])
@role_required()
def rate_user():
    """Rate user endpoint"""
    try:
        request_data = request.get_json()
        validate_fields(request_data, {"trip_id": int, "value": int, "rating_criteria_id": int})
        trip_service.rate_user(
            request_data.get("value"), request_data.get("trip_id"), request_data.get("rating_criteria_id")
        )
        response = jsonify(message="USER_RATED_SUCCESSFULLY"), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@trip.route("/daily-trip", methods=["POST"])
@role_required(RoleUser.DRIVER)
def create_daily_trip():
    """create a daily trip endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        json_object = request.json

        validate_fields(
            json_object,
            {
                "total_passenger_count": int,
                "date_start": str,
                "date_end": str,
                "hour": str,
                "address_departure_id": int,
                "address_arrival_id": int,
                "days": list,
            },
        )

        trip_service.create_daily_trips(
            json_object.get("address_departure_id", None),
            json_object.get("address_arrival_id", None),
            json_object.get("date_start", None),
            json_object.get("date_end", None),
            json_object.get("hour", None),
            json_object.get("total_passenger_count", None),
            json_object.get("days", None),
            user_id,
            TripStatus.PENDING.value,
        )

        response = jsonify(message="DAILY_TRIP_CREATED_SUCCESSFULLY"), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response
