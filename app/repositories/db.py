from contextlib import contextmanager

import mysql.connector
from flask import current_app


def get_connection():
    connection = mysql.connector.connect(
        host=current_app.config["MYSQL_HOST"],
        port=current_app.config["MYSQL_PORT"],
        user=current_app.config["MYSQL_USER"],
        password=current_app.config["MYSQL_PASSWORD"],
        database=current_app.config["MYSQL_DATABASE"],
        charset=current_app.config["MYSQL_CHARSET"],
        collation=current_app.config["MYSQL_COLLATION"],
        use_unicode=True,
    )
    connection.set_charset_collation(
        charset=current_app.config["MYSQL_CHARSET"],
        collation=current_app.config["MYSQL_COLLATION"],
    )
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    finally:
        cursor.close()
    return connection


@contextmanager
def get_cursor(commit=False):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
