from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flask_mail import Mail
from uniride_sme.config import Config
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config.from_object(Config)
cors = CORS(app, resources={r"*": {"origins": "*"}})
api = Api(app)
mail = Mail(app)
