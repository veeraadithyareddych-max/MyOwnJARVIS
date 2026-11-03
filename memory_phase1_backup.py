
import sqlite3
import json
import re
from datetime import datetime

DATABASE_NAME = "jarvis_memory.sqlite3"


# ============================================================
# 1. BASIC PERSONAL MEMORY
# ============================================================

def initialize_memory():
    """Create the personal memory table if it doesn't exist."""

    connection = sqlite3.connect(DATABASE_NAME)

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                information TEXT NOT NULL
            )
        """)

        connection.commit()

    finally:
        connection.close()


def save_memory(information):
    """Save information in the local database."""

    connection = sqlite3.connect(DATABASE_NAME)

    try:
        connection.execute(
            "INSERT INTO memories (information) VALUES (?)",
            (information,),
        )

        connection.commit()

    finally:
        connection.close()


def get_memories():
    """Retrieve all saved personal information."""

    connection = sqlite3.connect(DATABASE_NAME)

    try:
        results = connection.execute("""
            SELECT id, information
            FROM memories
            ORDER BY id
        """).fetchall()

        return results

    finally:
        connection.close()


# ============================================================
# 2. SAVE AGENT EXPERIENCES
# ============================================================

def save_experience(
    user_request,
    failed_tool,
    failed_arguments,
    error_message,
    recovery_tool,
    recovery_arguments,
    outcome,
):
    """Save a failed action and its recovery outcome."""

    connection = sqlite3.connect(DATABASE_NAME)

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_request TEXT NOT NULL,
                failed_tool TEXT NOT NULL,
                failed_arguments TEXT,
                error_message TEXT,
                recovery_tool TEXT,
                recovery_arguments TEXT,
                outcome TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            INSERT INTO experiences (
                user_request,
                failed_tool,
                failed_arguments,
                error_message,
                recovery_tool,
                recovery_arguments,
                outcome,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_request,
            failed_tool,
            json.dumps(failed_arguments),
            error_message,
            recovery_tool,
            json.dumps(recovery_arguments),
            outcome,
            datetime.now().isoformat(timespec="seconds"),
        ))

        connection.commit()

    finally:
        connection.close()


# ============================================================
# 3. RETRIEVE RECENT EXPERIENCES
# ============================================================

def get_recent_experiences(limit=5):
    """Retrieve the most recent agent experiences."""

    if limit <= 0:
        return []

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    try:
        table_exists = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'experiences'
        """).fetchone()

        if table_exists is None:
            return []

        rows = connection.execute("""
            SELECT *
            FROM experiences
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


# ============================================================
# 4. RETRIEVE RELEVANT EXPERIENCES
# ============================================================

def get_relevant_experiences(
    failed_tool,
    error_message="",
    limit=5,
):
    """
    Retrieve experiences involving the same failed tool.

    Rank them using error similarity, successful outcomes,
    and record recency.

    This retrieves stored experiences; it does not train
    or fine-tune the language model.
    """

    if limit <= 0:
        return []

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    try:
        table_exists = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'experiences'
        """).fetchone()

        if table_exists is None:
            return []

        rows = connection.execute("""
            SELECT *
            FROM experiences
            WHERE failed_tool = ?
            ORDER BY id DESC
            LIMIT 100
        """, (failed_tool,)).fetchall()

        experiences = [dict(row) for row in rows]

        def meaningful_words(text):
            words = set(
                re.findall(
                    r"\b[a-zA-Z]{3,}\b",
                    (text or "").lower(),
                )
            )

            stop_words = {
                "the", "and", "for", "you", "are", "was",
                "not", "with", "this", "that", "from",
                "please", "tool", "error", "failed", "failure",
            }

            return words - stop_words

        current_words = meaningful_words(error_message)

        def rank_experience(item):
            past_words = meaningful_words(
                item.get("error_message", "")
            )

            if current_words and past_words:
                similarity = (
                    len(current_words & past_words)
                    / len(current_words)
                )
            else:
                similarity = 0.0

            # A modest preference for successful recoveries.
            success_bonus = (
                0.15
                if item.get("outcome") == "SUCCESS"
                else 0.0
            )

            record_id = item.get("id", 0)

            return (
                similarity + success_bonus,
                similarity,
                record_id,
            )

        experiences.sort(
            key=rank_experience,
            reverse=True,
        )

        return experiences[:limit]

    finally:
        connection.close()


# ============================================================
# 5. EXPERIENCE AND RECOVERY STATISTICS
# ============================================================

def get_experience_stats():
    """Return statistics about recorded recovery outcomes."""

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    try:
        table_exists = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'experiences'
        """).fetchone()

        if table_exists is None:
            return {
                "total": 0,
                "successes": 0,
                "failures": 0,
                "success_rate": 0.0,
                "by_tool": [],
            }

        totals = connection.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(
                    CASE WHEN outcome = 'SUCCESS'
                    THEN 1 ELSE 0 END
                ) AS successes,
                SUM(
                    CASE WHEN outcome != 'SUCCESS'
                    THEN 1 ELSE 0 END
                ) AS failures
            FROM experiences
        """).fetchone()

        by_tool = connection.execute("""
            SELECT
                failed_tool,
                COUNT(*) AS attempts,
                SUM(
                    CASE WHEN outcome = 'SUCCESS'
                    THEN 1 ELSE 0 END
                ) AS successes
            FROM experiences
            GROUP BY failed_tool
            ORDER BY attempts DESC
        """).fetchall()

        total = totals["total"] or 0
        successes = totals["successes"] or 0
        failures = totals["failures"] or 0

        success_rate = (
            round(successes / total * 100, 2)
            if total
            else 0.0
        )

        return {
            "total": total,
            "successes": successes,
            "failures": failures,
            "success_rate": success_rate,
            "by_tool": [dict(row) for row in by_tool],
        }

    finally:
        connection.close()
