import os
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def create_connection():
    """
    Creates a PostgreSQL connection using values stored in the .env file.
    """

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
        database=os.getenv("DB_NAME", "norugs"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD") or None,
    )


@contextmanager
def get_database_connection():
    """
    Opens a database connection and automatically commits or rolls back.
    """

    connection = create_connection()

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()