"""Configure database connection"""
# !/usr/bin/python
from configparser import ConfigParser, NoSectionError
import dataclasses
import os
from datetime import timedelta
from dotenv import load_dotenv


@dataclasses.dataclass
class Config:
    """Config variables"""

    PATH = os.path.dirname(__file__)
    load_dotenv()

    SECRET_KEY = os.getenv("SECRET_KEY")
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")

    # Mail config
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = False
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_EXPIRATION = int(os.getenv("MAIL_EXPIRATION"))
    UNIVERSITY_EMAIL_DOMAIN = os.getenv("UNIVERSITY_EMAIL_DOMAIN")

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH"))
    PFP_UPLOAD_FOLDER = os.getenv("PFP_UPLOAD_FOLDER")
    LICENSE_UPLOAD_FOLDER = os.getenv("LICENSE_UPLOAD_FOLDER")
    ID_CARD_UPLOAD_FOLDER = os.getenv("ID_CARD_UPLOAD_FOLDER")
    SCHOOL_CERTIFICATE_UPLOAD_FOLDER = os.getenv("SCHOOL_CERTIFICATE_UPLOAD_FOLDER")

    # JWT config
    JWT_SALT = os.getenv("JWT_SALT").encode("utf8")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)

    # RQ config
    CACHE_TYPE = os.getenv("CACHE_TYPE")
    RQ_REDIS_URL = os.getenv("RQ_REDIS_URL")

    # Cache config
    CACHE_REDIS_HOST = os.getenv("CACHE_REDIS_HOST")
    CACHE_REDIS_PORT = os.getenv("CACHE_REDIS_PORT")
    CACHE_REDIS_PASSWORD = os.getenv("CACHE_REDIS_PASSWORD")
    CACHE_REDIS_DB = os.getenv("CACHE_REDIS_DB")

    FRONT_END_URL = os.getenv("FRONT_END_URL")

    # DB config
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PWD = os.getenv("DB_PWD")
    DB_PORT = os.getenv("DB_PORT", "5432")

    TESTING = False
    DEBUG = False

    # University address
    UNIVERSITY_STREET_NUMBER = str(os.getenv("UNIVERSITY_STREET_NUMBER"))
    UNIVERSITY_STREET_NAME = str(os.getenv("UNIVERSITY_STREET_NAME"))
    UNIVERSITY_CITY = str(os.getenv("UNIVERSITY_CITY"))
    UNIVERSITY_POSTAL_CODE = str(os.getenv("UNIVERSITY_POSTAL_CODE"))

    # Api key for google maps
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    ROUTE_CHECKER = os.getenv("ROUTE_CHECKER")

    RATE_PER_KM = float(os.getenv("RATE_PER_KM"))
    COST_PER_KM = float(os.getenv("COST_PER_KM"))
    BASE_RATE = float(os.getenv("BASE_RATE"))

    ACCEPT_TIME_DIFFERENCE_MINUTES = int(os.getenv("ACCEPT_TIME_DIFFERENCE_MINUTES"))


class TestingConfig(Config):
    """Testing Config variables"""

    TESTING = True
    DB_NAME = os.getenv("DB_NAME", "uniride") + "_test"


def config(filename="config.ini", section="postgresql"):
    """Configure database connection"""
    parser = ConfigParser()
    if not parser.read(filename):
        raise FileNotFoundError(f"Configuration file '{filename}' not found.")

    if not parser.has_section(section):
        raise NoSectionError(section)

    return dict(parser.items(section))
