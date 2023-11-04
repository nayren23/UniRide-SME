"""File related functions"""
import os

from uniride_sme.utils.exception.exceptions import FileException


def allowed_file(filename, allowed_extensions):
    """Check if file's extension is allowed"""
    extension = filename.rsplit(".", 1)[1].lower()
    if "." not in filename or extension not in allowed_extensions:
        raise FileException("INVALID_FILE_EXTENSION", 422)
    return extension


def save_file(file, directory, allowed_extensions, user_id):
    """Save file"""
    extension = allowed_file(file.filename, allowed_extensions)
    file_name = f"{user_id}.{extension}"
    file.save(os.path.join(directory, file_name))
    return file_name


def delete_file(file, directory):
    """Delete file"""
    os.remove(os.path.join(directory, file))
