#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_restful import Api
from flask_cors import CORS
from config import config
import os

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
api = Api(app)


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
    return response


if __name__ == "__main__":
    # read server parameters
    params = config("config.ini", "server")
    currentPath = os.path.dirname(__file__)
    cert = os.path.join(currentPath, params["cert"])
    key = os.path.join(currentPath, params["key"])
    context = (cert, key)  # certificate and key files
    # Launch Flask server0
    app.run(
        debug=params["debug"],
        host=params["host"],
        port=params["port"],
        ssl_context=context,
    )
