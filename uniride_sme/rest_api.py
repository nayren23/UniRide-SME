"""Rest API"""
# !/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from flask import jsonify
from uniride_sme import app
from uniride_sme.config import config
from uniride_sme.api.user_api import user
from uniride_sme.api.trip_api import trip
from uniride_sme.api.address_api import address

@app.after_request
def after_request(response):
    """Add Headers to response"""
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
    return response


@app.after_request
def reformat_jwt_response(response):
    """Reformat the response for jwt errors"""
    response_json = response.get_json()
    if response_json and "msg" in response_json:
        message = (
            "TOKEN_" + response_json["msg"].split(":")[0].replace(" ", "_").upper()
        )
        response_json["message"] = message
        del response_json["msg"]
        response.data = json.dumps(response_json)
    return response


@app.errorhandler(413)
def file_too_large(e):
    """Return a custom response when a file is too large"""
    return jsonify(message="FILE_TOO_LARGE"), 413


if __name__ == "__main__":
    # read server parameters
    params = config("config.ini", "server")
    context = (params["cert"], params["key"])  # certificate and key files

    app.register_blueprint(user)
    app.register_blueprint(trip)
    app.register_blueprint(address)
    # Launch Flask server0
    app.run(
        debug=params["debug"],
        host=params["host"],
        port=params["port"],
        ssl_context=context,
    )
