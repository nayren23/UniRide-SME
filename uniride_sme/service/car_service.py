"""Car service module"""



from uniride_sme import connect_pg
from uniride_sme.model.bo.car_bo import CarBO

from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,
      MissingInputException

)


def add_in_db(car: CarBO):
        """Insert the car in the database"""

        # validate values
        valid_model(car.model)
        valid_license_plate(car.license_plate)
        valid_country_license_plate(car.country_license_plate)
        valid_color(car.color)
        valid_brand(car.brand)
        validate_user_id(car.user_id)
        query = (
                "INSERT INTO uniride.ur_vehicle (v_model,"
                "v_license_plate, v_country_license_plate, v_color, v_brand, u_id) "
                " VALUES (%s, %s, %s, %s, %s, %s) RETURNING v_id"
            )

        values = (
            car.model,
            car.license_plate,
            car.country_license_plate,
            car.color,
            car.brand,
            car.user_id
        )

        conn = connect_pg.connect()
        car_id = connect_pg.execute_command(conn, query, values)

        car.id = car_id

def valid_model(model):
    """Check if the model car is valid"""
    if model is None:
        raise InvalidInputException("MODEL_CAR_CANNOT_BE_NULL")


def valid_license_plate(license_plate):
    """Check if the liecence plate car  is valid"""
    if license_plate is None:
        raise InvalidInputException("LICENSE_PLATE_CAR_CANNOT_BE_NULL")

def valid_country_license_plate(country_license_plate):
    """Check if the country liecence plate car is valid"""
    if country_license_plate is None:
        raise InvalidInputException("COUNTRY_LICENSE_PLATE_CAR_CANNOT_BE_NULL")

def valid_color(color):
    """Check if the color car is valid"""
    if color is None:
        raise InvalidInputException("COLOR_CAR_CANNOT_BE_NULL")

def valid_brand(brand):
    """Check if the brand car is valid"""
    if brand is None:
        raise InvalidInputException("BRAND_CAR_CANNOT_BE_NULL")
    

def validate_user_id(user_id):
    """Check if the user id is valid"""
    if user_id is None:
        raise MissingInputException("USER_ID_CANNOT_BE_NULL")
    if user_id < 0:
        raise InvalidInputException("USER_ID_CANNOT_BE_NEGATIVE")