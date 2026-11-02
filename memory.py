
import sqlite3

DATABASE_NAME = "jarvis_memory.sqlite3"


def initialize_memory():
    """Create the memory table if it doesn't exist."""

    connection = sqlite3.connect(DATABASE_NAME)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            information TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def save_memory(information):
    """Save information in the local database."""

    connection = sqlite3.connect(DATABASE_NAME)

    connection.execute(
        "INSERT INTO memories (information) VALUES (?)",
        (information,)
    )

    connection.commit()
    connection.close()


def get_memories():
    """Retrieve all saved information."""

    connection = sqlite3.connect(DATABASE_NAME)

    results = connection.execute(
        "SELECT id, information FROM memories ORDER BY id"
    ).fetchall()

    connection.close()
    return results
