"""Rest API"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from config import config
from api.user import user

app = Flask(__name__)
app.register_blueprint(user)
cors = CORS(app, resources={r"*": {"origins": "*"}})
api = Api(app)


@app.after_request
def after_request(response):
    """Add Headers to response"""
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
    return response


if __name__ == "__main__":
    # read server parameters
    params = config("config.ini", "server")
    context = (params["cert"], params["key"])  # certificate and key files
    # Launch Flask server0
    app.run(
        debug=params["debug"],
        host=params["host"],
        port=params["port"],
        ssl_context=context,
    )
