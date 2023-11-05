#!/usr/bin/python

import psycopg2
from uniride_sme.config import config


def connect(filename="config.ini", section="postgresql"):
    """Connect to the PostgreSQL database server"""
    conn = None
    try:
        # read connection parameters
        params = config(filename, section)

        # connect to the PostgreSQL server
        print("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**params)

        conn.set_client_encoding("UTF8")

        # create a cursor
        cur = conn.cursor()

        # execute a statement
        print("PostgreSQL database version:")
        cur.execute("SELECT version()")

        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            return conn


def disconnect(conn):
    # close the connexion
    conn.close()
    print("Database connection closed.")


def execute_command(conn, query, params=None):
    """Execute a SQL command"""
    cur = conn.cursor()

    returning_value = None

    print(query)
    cur.execute(query, params)
    if "returning" in query.lower():
        returning_value = cur.fetchone()[0]

    # Close communication with the PostgreSQL database server
    cur.close()
    # Commit the changes
    conn.commit()
    return returning_value


def get_query(conn, query, params=None):
    """Query data from db"""
    try:
        rows = None
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return error
    return rows


if __name__ == "__main__":
    connect()
