"""Configure database connection"""
# !/usr/bin/python
from configparser import ConfigParser
import os


class Config:
    """Config variables"""

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
