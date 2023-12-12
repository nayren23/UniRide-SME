"""Trip related routes"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity

from uniride_sme.model.bo.trip_bo import TripBO
from uniride_sme.model.bo.address_bo import AddressBO

from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.trip_status import TripStatus
from uniride_sme.utils.field import validate_fields
from uniride_sme.utils.pagination import create_pagination
from uniride_sme.service.trip_service import (
    add_trip,
    get_driver_trips,
    get_available_trips_to,
    get_trip_by_id,
)

trip = Blueprint("trip", __name__, url_prefix="/trip")


@trip.route("/propose", methods=["POST"])
@jwt_required()
def propose_trip():
    """Propose a trip endpoint
    "We define the  price of the trip and the status of the trip as pending
    """

    response = jsonify({"message": "TRIP_CREATED_SUCCESSFULLY"}), 200
    try:
        user_id = get_jwt_identity()
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
            departure_address_bo=AddressBO(id=json_object.get("address_departure_id", None)),
            arrival_address_bo=AddressBO(id=json_object.get("address_arrival_id", None)),
            status=TripStatus.PENDING.value,
        )
        add_trip(trip_bo)
        response = jsonify({"message": "CREATED_SUCCESSFULLY", "trip_id": trip_bo.id}), 200

    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@trip.route("", methods=["POST"])
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

        available_trips = get_available_trips_to(trip_bo)

        # We need to paginate the data
        meta, paginated_data = create_pagination(request, available_trips)

        response = jsonify({"trips": paginated_data, "meta": meta}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@trip.route("/driver/current", methods=["GET"])
@jwt_required()
def get_current_driver_trips():
    """Get all the current trips of a driver"""
    try:
        user_id = get_jwt_identity()

        available_trips = get_driver_trips(user_id)

        # We need to paginate the data
        meta, paginated_data = create_pagination(request, available_trips)

        response = jsonify({"trips": paginated_data, "meta": meta}), 200

    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@trip.route("/<trip_id>", methods=["GET"])
def get_trip(trip_id):
    """Get a trip by id endpoint"""
    try:
        trip_detailed_dto = get_trip_by_id(trip_id)
        response = jsonify(trip_detailed_dto), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response
