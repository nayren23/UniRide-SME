#!/usr/bin/python
import psycopg2
from config import config
import os
from dotenv import load_dotenv

#Fichier pour faire le lien avec la BDD
def connect(filename='config.ini', section='postgresql'):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        params = config(filename, section) # read connection parameters
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params, host=os.getenv("DB_HOST")) # connect to the PostgreSQL server 
        conn.set_client_encoding('UTF8')
        cur = conn.cursor() # create a cursor
        print('PostgreSQL database version:')
        cur.execute('SELECT version()') # execute a statement
        db_version = cur.fetchone() # display the PostgreSQL database server version
        print(db_version)
        cur.close() # close the communication with the PostgreSQL
    except (Exception, psycopg2.DatabaseError) as error:
        print("Echec Connexion BDD",error)
    finally:
        if conn is not None:
            return conn

def disconnect(conn):
    conn.close() # close the connexion
    print('Database connection closed.')

def execute_commands(conn, commands):
    """ Execute a SQL command """
    cur = conn.cursor()
    # create table one by one
    for command in commands:
        if command :
            print(command)
            cur.execute(command)
    # close communication with the PostgreSQL database server
    cur.close()
    # commit the changes
    conn.commit()


def get_query(conn, query):
    """ query data from db """
    try:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            return rows

if __name__ == '__main__':
    connect()