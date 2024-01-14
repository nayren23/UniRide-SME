"""About utilities"""
import os
from uniride_sme import app


def get_conditions():
    """Get conditions of use"""
    file_path = os.path.join(app.config["PATH"], "resource/about/conditions_of_use.html")

    with open(file_path, "r", encoding="UTF-8") as html:
        content = html.read()

    return content
