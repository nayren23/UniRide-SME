"""Car service module"""



from uniride_sme import connect_pg
from uniride_sme.model.bo.car_bo import CarBO

from uniride_sme.utils.exception.exceptions import (
    InvalidInputException,

)


def add_in_db(self):
        """Insert the car in the database"""

        # validate values
        valid_model()
        valid_licence_plate()
        valid_country_licence_plate()
        valid_color()
        valid_brand()

        # retrieve not None values
        attr_dict = {}
        for attr, value in self.__dict__.items():
            if value:
                attr_dict["a_" + attr] = value

        # format for sql query
        fields = ", ".join(attr_dict.keys())
        placeholders = ", ".join(["%s"] * len(attr_dict))
        values = tuple(attr_dict.values())

        query = f"INSERT INTO uniride.ur_vehicle ({fields}) VALUES ({placeholders}) RETURNING v_id"

        conn = connect_pg.connect()
        car_id = connect_pg.execute_command(conn, query, values)
        self.id_car = car_id

def valid_model(self):
    """Check if the model car is valid"""
    if self.model is None:
        raise InvalidInputException("MODEL_CAR_CANNOT_BE_NULL")


def valid_licence_plate(self):
    """Check if the liecence plate car  is valid"""
    if self.licence_plate is None:
        raise InvalidInputException("LICENCE_PLATE_CAR_CANNOT_BE_NULL")

def valid_country_licence_plate(self):
    """Check if the country liecence plate car is valid"""
    if self.country_licence_plate is None:
        raise InvalidInputException("COUNTRY_LICENCE_PLATE_CAR_CANNOT_BE_NULL")

def valid_color(self):
    """Check if the color car is valid"""
    if self.color is None:
        raise InvalidInputException("COLOR_CAR_CANNOT_BE_NULL")

def valid_brand(self):
    """Check if the brand car is valid"""
    if self.brand is None:
        raise InvalidInputException("BRAND_CAR_CANNOT_BE_NULL")
    
def concatene_car(self):
    """Concatene the information of car"""
    return self.model + " " + self.licence_plate + " " + self.country_licence_plate + " " + self.color + "" + self.brand