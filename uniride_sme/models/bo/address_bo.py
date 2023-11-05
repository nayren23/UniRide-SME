
from uniride_sme import connect_pg
from datetime import datetime
import requests

class AddressBO:
    def __init__(self, 
                 address_id = None, 
                 street_number = None, 
                 street_name= None, 
                 city = None, 
                 postal_code = None, 
                 latitude = None, 
                 longitude = None,
                 description = "", 
                 timestamp_modification = None
                 ):
        self.id = address_id
        self.street_number = street_number
        self.street_name = street_name
        self.city = city
        self.postal_code = postal_code
        self.latitude = latitude
        self.longitude = longitude
        self.description = description
        self.timestamp_modification = timestamp_modification

    def add_in_db(self):
        """Insert the address in the database"""
        existing_address_id = self.address_exists()

        # Check if the address already exists
        if existing_address_id :
            self.id = existing_address_id[0][0]
        else:
            # validate values            
            self.valid_street_number()
            self.valid_street_name()
            self.valid_city()
            self.valid_postal_code()
            self.get_latitude_longitude_from_address()
            self.valid_latitude()
            self.valid_longitude()
            self.valid_description()
            # Add more validation methods as needed

            # retrieve not None values
            attr_dict = {}
            for attr, value in self.__dict__.items():
                if value:
                    attr_dict["a_" + attr] = value

            # format for sql query
            fields = ", ".join(attr_dict.keys())
            placeholders = ", ".join(["%s"] * len(attr_dict))
            values = tuple(attr_dict.values())

            query = f"INSERT INTO uniride.ur_address ({fields}) VALUES ({placeholders}) RETURNING a_id"

            conn = connect_pg.connect()
            address_id = connect_pg.execute_command(conn, query, values)
            self.id = address_id
            
    
    def valid_street_number(self):
        if self.street_number is None:
            raise ValueError("street_number cannot be null")
        if len(self.street_number) > 10:    
            raise ValueError("street_number cannot be greater than 10")

    def valid_street_name(self):
        return isinstance(self.street_name, str) and len(self.street_name) <= 255

    def valid_city(self):
        return isinstance(self.city, str) and len(self.city) <= 255

    def valid_postal_code(self):
        return isinstance(self.postal_code, str) and len(self.postal_code) == 5

    def valid_latitude(self):
        return isinstance(self.latitude, float)

    def valid_longitude(self):
        return isinstance(self.longitude, float)

    def valid_description(self):
        return isinstance(self.description, str) and len(self.description) <= 50

    def valid_timestamp_modification(self):
        return isinstance(self.timestamp_modification, datetime)

    def valid(self):
        return self.valid_street_number() and self.valid_street_name() and self.valid_city() and \
               self.valid_postal_code() and self.valid_latitude() and self.valid_longitude() and \
               self.valid_description() and self.valid_timestamp_modification()

    def address_exists(self):
        """Check if the address already exists in the database"""

        query = """
        SELECT a_id
        FROM uniride.ur_address
        WHERE a_street_number = %s AND a_street_name = %s AND a_city = %s
        """
    
        conn = connect_pg.connect()
        address_id = connect_pg.get_query(conn, query, (self.street_number, self.street_name, self.city))
        connect_pg.disconnect(conn)
        
        return address_id
    
    def get_latitude_longitude_from_address(self):
        """Get the latitude and longitude of the address, use the API Adresse GOUV"""
            
        # URL API Adresse GOUV  /search/
        url_search = "https://api-adresse.data.gouv.fr/search/"

        address = self.street_number + " " + self.street_name + " " + self.city
        
        # Parameter for research
        params = {
            'q': address,
            'limit': 1,
            'autocomplete': 0
        }

        # We launch the request  l'API /search/
        response = requests.get(url_search, params=params)

        # We get the data in JSON from the response
        data = response.json()

        if data['features'] != []:
            # Get the coordonate from first adress
            self.latitude = data['features'][0]['geometry']['coordinates'][1]
            self.longitude = data['features'][0]['geometry']['coordinates'][0]
        else:    
            raise ValueError("Invalid address")