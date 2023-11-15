"""Configure database connection"""
# !/usr/bin/python
from configparser import ConfigParser, NoSectionError
import os
from datetime import timedelta


class Config:  # pylint: disable=too-few-public-methods
    """Config variables"""

    PATH = os.path.dirname(__file__)

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

    MAX_CONTENT_LENGTH = 5 * 1000 * 1000
    PFP_UPLOAD_FOLDER = os.getenv("PFP_UPLOAD_FOLDER")
    LICENSE_UPLOAD_FOLDER = os.getenv("LICENSE_UPLOAD_FOLDER")
    ID_CARD_UPLOAD_FOLDER = os.getenv("ID_CARD_UPLOAD_FOLDER")
    SCHOOL_CERTIFICATE_UPLOAD_FOLDER = os.getenv("SCHOOL_CERTIFICATE_UPLOAD_FOLDER")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    FRONT_END_URL = os.getenv("FRONT_END_URL")

    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PWD = os.getenv("DB_PWD")
    DB_PORT = os.getenv("DB_PORT", "5432")

    TESTING = False
    DEBUG = False

class TestingConfig(Config):
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
