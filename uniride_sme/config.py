"""Configure database connection"""
#!/usr/bin/python
from configparser import ConfigParser


def config(filename="config.ini", section="postgresql"):
    """Configure database connection"""
    parser = ConfigParser()  # create a parser
    parser.read(filename)  # read config file
    db = {}  # get section, default to postgresql
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f"Section {section} not found in the {filename} file")
    return db
