#!/usr/bin/python
from configparser import ConfigParser
import os

def config(filename='config.ini', section='postgresql'):
    parser = ConfigParser() # create a parser
    filePath = os.path.join(os.path.dirname(__file__), filename)
    readFiles = parser.read(filePath) # read config file
    if len(readFiles) == 0:
        raise Exception('Could not read config file {0}'.format(filename))
    
    db = {} # get section, default to postgresql
    if section == 'postgresql':
        db['dbname'] = os.getenv("DBNAME")
        db['user'] = os.getenv("DBUSER")
        db['password'] = os.getenv("DB_PWD")
        db['port'] = os.getenv("DB_PORT", 5432)
        db['host'] = os.getenv("DB_HOST", "127.0.0.1")
    
    if db == {} or None in db.values():
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    return db