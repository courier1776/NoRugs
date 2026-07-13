import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection

load_dotenv()


def create_connection() -> connection:
    """
    Create and return a PostgreSQL database connection.
    """

    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5433"),
            database=os.getenv("DB_NAME", "norugs"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD") or None,
        )
    except psycopg2.Error as error:
        raise ConnectionError(
            f"Unable to connect to PostgreSQL: {error}"
        ) from error


@contextmanager
def get_database_connection() -> Generator[connection, None, None]:
    """
    Provide a database connection and safely close it afterward.
    """

    database_connection = create_connection()

    try:
        yield database_connection
        database_connection.commit()
    except Exception:
        database_connection.rollback()
        raise
    finally:
        database_connection.close()