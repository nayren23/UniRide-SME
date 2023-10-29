"""Rest API"""
# !/usr/bin/env python
# -*- coding: utf-8 -*-
from uniride_sme import app
from uniride_sme.config import config
from uniride_sme.api.user_api import user


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

    app.register_blueprint(user)
    # Launch Flask server0
    app.run(
        debug=params["debug"],
        host=params["host"],
        port=params["port"],
        ssl_context=context,
    )
