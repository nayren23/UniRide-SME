"""Car service module"""
import psycopg2 as psy
from uniride_sme import connect_pg
from uniride_sme.model.bo.car_bo import CarBO
from uniride_sme.model.dto.car_dto import CarDTO
from uniride_sme.utils.exception.exceptions import InvalidInputException, MissingInputException
from uniride_sme.utils.exception.car_exceptions import CarAlreadyExist, CarNotFoundException


def add_car(car: CarBO) -> None:
    """Insert the car in the database"""
    # validate values
    valid_model(car.model)
    valid_license_plate(car.license_plate)
    valid_country_license_plate(car.country_license_plate)
    valid_color(car.color)
    valid_brand(car.brand)
    validate_user_id(car.user_id)
    validate_total_places(car.total_places)

    query = (
        "INSERT INTO uniride.ur_vehicle(v_model,"
        "v_license_plate, v_country_license_plate, v_color, v_brand, u_id, v_total_places) "
        " VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING v_id"
    )

    values = (
        car.model,
        car.license_plate,
        car.country_license_plate,
        car.color,
        car.brand,
        car.user_id,
        car.total_places,
    )
    try:
        conn = connect_pg.connect()
        car_id = connect_pg.execute_command(conn, query, values)
        car.id = car_id
        connect_pg.disconnect(conn)
    except psy.Error as e:
        raise CarAlreadyExist() from e


def valid_model(model) -> None:
    """Check if the model car is valid"""
    if not model:
        raise InvalidInputException("MODEL_CAR_CANNOT_BE_NULL")


def valid_license_plate(license_plate) -> None:
    """Check if the license plate car is valid"""
    if not license_plate:
        raise InvalidInputException("LICENSE_PLATE_CAR_CANNOT_BE_NULL")

    # Ajoutez d'autres critères de validation en fonction de vos besoins
    length_licence_plate = 9
    if len(license_plate) < length_licence_plate:
        raise InvalidInputException("LICENSE_PLATE_TOO_SHORT")
    if len(license_plate) > length_licence_plate:
        raise InvalidInputException("LICENSE_PLATE_TOO_HIGHT")


def valid_country_license_plate(country_license_plate) -> None:
    """Check if the country liecence plate car is valid"""
    if not country_license_plate:
        raise InvalidInputException("COUNTRY_LICENSE_PLATE_CAR_CANNOT_BE_NULL")

    # Ajoutez d'autres critères de validation en fonction de vos besoins
    length_country_licence_plate = 2
    if len(country_license_plate) > length_country_licence_plate:
        raise InvalidInputException("LICENSE_PLATE_TOO_HIGHT")


def valid_color(color) -> None:
    """Check if the color car is valid"""
    if not color:
        raise InvalidInputException("COLOR_CAR_CANNOT_BE_NULL")


def valid_brand(brand) -> None:
    """Check if the brand car is valid"""
    if not brand:
        raise InvalidInputException("BRAND_CAR_CANNOT_BE_NULL")


def validate_user_id(user_id) -> None:
    """Check if the user id is valid"""
    if not user_id:
        raise MissingInputException("USER_ID_CANNOT_BE_NULL")
    if user_id < 0:
        raise InvalidInputException("USER_ID_CANNOT_BE_NEGATIVE")


def validate_total_places(total_places) -> None:
    """Check if the total passenger count is valid"""
    if not total_places:
        raise MissingInputException("TOTAL_PLACES_CANNOT_BE_NULL")
    if total_places < 0:
        raise InvalidInputException("TOTAL_PLACES_CANNOT_BE_NEGATIVE")
    if total_places > 4:
        raise InvalidInputException("TOTAL_PLACES_TOO_HIGH")


def get_car_info_by_user_id(user_id) -> CarBO:
    """Get car information by user ID"""

    query = """
        SELECT *
        FROM uniride.ur_vehicle
        WHERE u_id = %s
    """
    params = (user_id,)
    conn = connect_pg.connect()
    info_car = connect_pg.get_query(conn, query, params, True)
    connect_pg.disconnect(conn)

    if not info_car:
        raise CarNotFoundException("CAR_NOT_FOUND")
    info_car = info_car[0]

    car_bo = CarBO(
        model=info_car["v_model"],
        license_plate=info_car["v_license_plate"],
        country_license_plate=info_car["v_country_license_plate"],
        color=info_car["v_color"],
        brand=info_car["v_brand"],
        user_id=info_car["u_id"],
        total_places=info_car["v_total_places"],
    )

    return car_bo


def format_get_information_car(info_car: CarBO) -> CarDTO:
    """Format the information car to return"""
    car_dto = CarDTO(
        model=info_car.model,
        license_plate=info_car.license_plate,
        country_license_plate=info_car.country_license_plate,
        color=info_car.color,
        brand=info_car.brand,
        total_places=info_car.total_places,
    )

    return car_dto


def update_car_information_in_db(car: CarBO) -> None:
    """Update car information"""
    valid_model(car.model)
    valid_license_plate(car.license_plate)
    valid_country_license_plate(car.country_license_plate)
    valid_color(car.color)
    valid_brand(car.brand)
    validate_user_id(car.user_id)
    validate_total_places(car.total_places)

    query = """
        UPDATE uniride.ur_vehicle
        SET v_model = %s, v_license_plate = %s, v_country_license_plate = %s, v_color = %s, v_brand = %s, v_total_places = %s
        WHERE u_id = %s
    """
    values = (
        car.model,
        car.license_plate,
        car.country_license_plate,
        car.color,
        car.brand,
        car.total_places,
        car.user_id,
    )
    conn = connect_pg.connect()
    connect_pg.execute_command(conn, query, values)
    connect_pg.disconnect(conn)
