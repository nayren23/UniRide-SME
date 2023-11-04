"""File related functions"""
import os

from uniride_sme.utils.exception.exceptions import FileException


def allowed_file(filename, allowed_extensions):
    """Check if file's extension is allowed"""
    extension = filename.rsplit(".", 1)[1].lower()
    if "." not in filename or extension not in allowed_extensions:
        raise FileException("INVALID_FILE_EXTENSION", 422)


def save_file(file, directory, allowed_extensions, user_id):
    """Save file"""
    allowed_file(file.filename, allowed_extensions)
    file.save(os.path.join(directory, user_id + ".jpg"))
