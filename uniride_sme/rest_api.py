"""Rest API"""
# !/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
from flask import jsonify
from uniride_sme import app
from uniride_sme.route.user_route import user
from uniride_sme.route.trip_route import trip
from uniride_sme.route.address_route import address
from uniride_sme.route.car_route import car
from uniride_sme.route.book_route import book


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
        message = ""
        if not response_json["msg"].lower().startswith("token"):
            message = "TOKEN_"
        message += response_json["msg"].split(":")[0].replace(" ", "_").upper()

        response_json["message"] = message
        del response_json["msg"]
        response.data = json.dumps(response_json)
    return response


@app.errorhandler(413)
def file_too_large(e):  # pylint: disable=unused-argument
    """Return a custom response when a file is too large"""
    return jsonify(message="FILE_TOO_LARGE"), 413


if __name__ == "__main__":
    currentPath = os.path.dirname(__file__)
    cert = os.path.join(currentPath, app.config["CERTIFICATE_CRT_FOLDER"])
    key = os.path.join(currentPath, app.config["CERTIFICATE_KEY_FOLDER"])
    context = (cert, key)  # certificate and key files

    app.register_blueprint(user)
    app.register_blueprint(trip)
    app.register_blueprint(address)
    app.register_blueprint(car)
    app.register_blueprint(book)
    # Launch Flask server0
    app.run(
        debug=app.config["FLASK_DEBUG"],
        host=app.config["FLASK_HOST"],
        port=app.config["FLASK_PORT"],
        ssl_context=context,
    )
