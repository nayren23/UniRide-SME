"""Configure database connection"""
# !/usr/bin/python
from configparser import ConfigParser
from dotenv import load_dotenv

import os


class Config:
    """Config variables"""

    load_dotenv()

    SECRET_KEY = os.getenv("SECRET_KEY")
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")

    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = False
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    UNIVERSITY_EMAIL_DOMAIN = os.getenv("UNIVERSITY_EMAIL_DOMAIN")

    PFP_UPLOAD_FOLDER = os.getenv("PFP_UPLOAD_FOLDER")
    LICENSE_UPLOAD_FOLDER = os.getenv("LICENSE_UPLOAD_FOLDER")
    ID_CARD_UPLOAD_FOLDER = os.getenv("ID_CARD_UPLOAD_FOLDER")
    SCHOOL_CERTIFICATE_UPLOAD_FOLDER = os.getenv("SCHOOL_CERTIFICATE_UPLOAD_FOLDER")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    FRONT_END_URL = os.getenv("FRONT_END_URL")

    # University address
    UNIVERSITY_STREET_NUMBER = str(os.getenv("UNIVERSITY_STREET_NUMBER"))
    UNIVERSITY_STREET_NAME = str(os.getenv("UNIVERSITY_STREET_NAME"))
    UNIVERSITY_CITY = str(os.getenv("UNIVERSITY_CITY"))
    UNIVERSITY_POSTAL_CODE = str(os.getenv("UNIVERSITY_POSTAL_CODE"))

    # Api key for google maps
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    print("SECRET_KEY", os.getenv("SECRET_KEY"))
    RATE_PER_KM = float(os.getenv("RATE_PER_KM"))
    COST_PER_KM = float(os.getenv("COST_PER_KM"))
    BASE_RATE = float(os.getenv("BASE_RATE"))

    ACCEPT_TIME_DIFFERENCE_MINUTES = int(os.getenv("ACCEPT_TIME_DIFFERENCE_MINUTES"))


def config(filename="config.ini", section="postgresql"):
    """Configure database connection"""
    parser = ConfigParser()  # create a parser
    parser.read(filename)  # read config file
    db = {}  # get section, default to postgresql
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f"Section {section} not found in the {filename} file")
    return db
