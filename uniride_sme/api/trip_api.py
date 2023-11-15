"""Trip related routes"""
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity

from uniride_sme import app
from uniride_sme.models.bo.trip_bo import TripBO

from uniride_sme.utils.cartography.route_checker_factory import RouteCheckerFactory

from uniride_sme.models.bo.address_bo import AddressBO
from uniride_sme.models.dto.trips_get_dto import TripsGetDTO
from uniride_sme.models.dto.trip_dto import TripDTO
from uniride_sme.models.dto.address_simple_dto import AddressSimpleDTO

from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.trip_status import TripStatus
from uniride_sme.utils.field import validate_fields

from uniride_sme.utils.pagination import create_pagination


trip = Blueprint("trip", __name__)


@trip.route("/trip/propose", methods=["POST"])
@jwt_required()
def propose_trip():
    """Propose a trip endpoint
    "We define the  price of the trip and the status of the trip as pending

    """

    response = jsonify({"message": "TRIP_CREATED_SUCCESSFULLY"}), 200
    try:
        user_id = get_jwt_identity()
        json_object = request.json

        validate_fields(json_object, {"total_passenger_count": int, "timestamp_proposed": str, "address_depart_id": int, "address_arrival_id": int})

        trip_bo = TripBO(
            total_passenger_count=json_object.get("total_passenger_count", None),
            timestamp_proposed=json_object.get("timestamp_proposed", None).strip(),
            user_id=user_id,
            address_depart_id=json_object.get("address_depart_id", None),
            address_arrival_id=json_object.get("address_arrival_id", None),
            status=TripStatus.PENDING.value,
            timestamp_creation=datetime.now(),
        )
        
        trip_bo.add_in_db()
        
        response = jsonify({"message": "CREATED_SUCCESSFULLY", "trip_id": trip_bo.id}), 200

    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@trip.route("/trips", methods=["POST"])
def get_available_trips():
    """Get all the available trips endpoint"""

    try:
        json_object = request.json

        validate_fields(request.json, {"depart": dict, "arrival": dict, "trip": dict})
        validate_fields(json_object["depart"], {"street_number": str, "street_name": str, "city": str, "postal_code": str})
        validate_fields(json_object["arrival"], {"street_number": str, "street_name": str, "city": str, "postal_code": str})
        validate_fields(json_object["trip"], {"passenger_count": int, "departure_date": str})

        depart_address_bo = AddressBO(
            street_number=(json_object.get("depart").get("street_number", None)).strip(),
            street_name=json_object.get("depart").get("street_name", None).strip(),
            city=json_object.get("depart").get("city", None).strip(),
            postal_code=json_object.get("depart").get("postal_code", None).strip(),
        )

        # We check if the address is valid
        depart_address_bo.check_address_exigeance()

        depart_address_bo.get_latitude_longitude_from_address()

        address_arrival_bo = AddressBO(
            street_number=json_object.get("arrival").get("street_number", None).strip(),
            street_name=json_object.get("arrival").get("street_name", None).strip(),
            city=json_object.get("arrival").get("city", None).strip(),
            postal_code=json_object.get("arrival").get("postal_code", None).strip(),
        )

        # We check if the address is valid
        address_arrival_bo.check_address_exigeance()

        address_arrival_bo.get_latitude_longitude_from_address()

        # We use the environment variables to get the university address
        university_street_number = app.config["UNIVERSITY_STREET_NUMBER"]
        university_street_name = app.config["UNIVERSITY_STREET_NAME"]
        university_city = app.config["UNIVERSITY_CITY"]
        university_postal_code = app.config["UNIVERSITY_POSTAL_CODE"]

        university_address_bo = AddressBO(
            street_number=university_street_number,
            street_name=university_street_name,
            city=university_city,
            postal_code=university_postal_code,
        )

        # We check if the address is valid
        university_address_bo.check_address_exigeance()

        university_address_bo.get_latitude_longitude_from_address()

        trip_bo = TripBO(
            total_passenger_count=json_object.get("trip").get("passenger_count", None),
            timestamp_proposed=json_object.get("trip").get("departure_date", None),
        )

        trip_bo.validate_total_passenger_count()
        trip_bo.validate_timestamp_proposed()

        available_trips = trip_bo.get_trips_for_university_address(depart_address_bo, address_arrival_bo, university_address_bo)

         # We need to paginate the data
         
        meta, paginated_data = create_pagination(request, available_trips)
        
        response = jsonify({"trips" : paginated_data, "meta" : meta}), 200

    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response


@trip.route("/trips/driver/current/", methods=["GET"])
@jwt_required()
def get_current_driver_trips():
    """Get all the current trips of a driver"""
    try:
        user_id = get_jwt_identity()

        trip_bo = TripBO(user_id=user_id)
        driver_current_trips = trip_bo.get_current_driver_trips()

        available_trips = []

        for current_trip in driver_current_trips:
            t_id, t_address_depart_id, t_address_arrival_id, price = current_trip

            adresse_depart = AddressBO(address_id=t_address_depart_id)
            arival_address = AddressBO(address_id=t_address_arrival_id)

            adresse_depart.check_address_existence()
            arival_address.check_address_existence()

            address_dtos = {
                "departure": AddressSimpleDTO(id=adresse_depart.id, name=adresse_depart.concatene_address()),
                "arrival": AddressSimpleDTO(id=arival_address.id, name=arival_address.concatene_address()),
            }
            trip_dto = TripDTO(
                trip_id=t_id,
                address=address_dtos,
                driver_id=user_id,
                price=price,
            )
            trips_get_dto = TripsGetDTO(trip_dto)
            available_trips.append(trips_get_dto)
            
            # We need to paginate the data
            meta, paginated_data = create_pagination(request, available_trips)
            
        response = jsonify({"trips" : paginated_data, "meta" : meta}), 200

    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response
