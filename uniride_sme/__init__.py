"""Initialisation of the api"""
import os
from datetime import timedelta
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from uniride_sme.config import Config

load_dotenv()
app = Flask(__name__)
app.config.from_object(Config)
app.config["PATH"] = os.path.dirname(__file__)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1000 * 1000
cors = CORS(app, resources={r"*": {"origins": "*"}})
api = Api(app)
mail = Mail(app)
jwt = JWTManager(app)
