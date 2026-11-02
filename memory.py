
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
    user_request="",
):
    """
    Retrieve recovery experiences using request relevance,
    recovery-argument relevance, outcome, and recency.

    The current request takes priority over conflicting historical
    recovery arguments. Stored experiences do not train the LLM.
    """

    import json

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

        stop_words = {
            "the", "and", "for", "you", "are", "was",
            "not", "with", "this", "that", "from",
            "please", "tool", "error", "failed", "failure",
            "because", "when", "then", "have", "has",
        }

        request_stop_words = stop_words | {
            "get", "weather", "current", "today", "what",
            "tell", "show", "find", "check", "want",
            "need", "give", "information", "about", "in",
        }

        def meaningful_words(text, ignored_words=None):
            words = set(
                re.findall(
                    r"\b[a-zA-Z]{3,}\b",
                    (text or "").lower(),
                )
            )
            ignored = (
                stop_words
                if ignored_words is None
                else ignored_words
            )
            return words - ignored

        def decode_arguments(value):
            if isinstance(value, dict):
                return value

            if isinstance(value, str):
                try:
                    decoded = json.loads(value)
                    if isinstance(decoded, dict):
                        return decoded
                except json.JSONDecodeError:
                    pass

            return {}

        def word_similarity(first_words, second_words):
            if not first_words or not second_words:
                return 0.0

            intersection = len(first_words & second_words)
            union = len(first_words | second_words)

            if union == 0:
                return 0.0

            jaccard = intersection / union
            coverage = intersection / len(first_words)

            return 0.7 * jaccard + 0.3 * coverage

        current_error_words = meaningful_words(error_message)
        current_request_words = meaningful_words(
            user_request,
            request_stop_words,
        )

        ranked = []

        for position, item in enumerate(experiences):
            past_error_words = meaningful_words(
                item.get("error_message", "")
            )

            past_request_words = meaningful_words(
                item.get("user_request", ""),
                request_stop_words,
            )

            error_similarity = word_similarity(
                current_error_words,
                past_error_words,
            )

            request_similarity = word_similarity(
                current_request_words,
                past_request_words,
            )

            recovery_arguments = decode_arguments(
                item.get("recovery_arguments", {})
            )

            recovery_argument_text = json.dumps(
                recovery_arguments,
                ensure_ascii=False,
                default=str,
            )

            recovery_argument_words = meaningful_words(
                recovery_argument_text,
                request_stop_words,
            )

            # Does this recovery's arguments match the current request?
            argument_similarity = word_similarity(
                current_request_words,
                recovery_argument_words,
            )

            outcome = str(item.get("outcome", "")).upper()

            if outcome == "SUCCESS":
                outcome_score = 0.10
            elif outcome == "FAILURE":
                outcome_score = -0.10
            else:
                outcome_score = 0.0

            recency_score = 0.02 * (
                (len(experiences) - position)
                / max(len(experiences), 1)
            )

            total_score = (
                0.25 * error_similarity
                + 0.40 * request_similarity
                + 0.35 * argument_similarity
                + outcome_score
                + recency_score
            )

            item["_relevance_score"] = round(total_score, 4)
            item["_error_similarity"] = round(
                error_similarity, 4
            )
            item["_request_similarity"] = round(
                request_similarity, 4
            )
            item["_argument_similarity"] = round(
                argument_similarity, 4
            )

            ranked.append(item)

        ranked.sort(
            key=lambda item: (
                item["_relevance_score"],
                item.get("id", 0),
            ),
            reverse=True,
        )

        # Keep the best-ranked version of each distinct example.
        unique_experiences = []
        seen = set()

        for item in ranked:
            signature = (
                str(item.get("failed_tool", "")).lower(),
                str(item.get("error_message", "")).strip().lower(),
                str(item.get("recovery_tool", "")).lower(),
                json.dumps(
                    decode_arguments(
                        item.get("recovery_arguments", {})
                    ),
                    sort_keys=True,
                    default=str,
                ),
                str(item.get("outcome", "")).upper(),
            )

            if signature in seen:
                continue

            seen.add(signature)
            unique_experiences.append(item)

            if len(unique_experiences) >= limit:
                break

        for item in unique_experiences:
            item.pop("_relevance_score", None)
            item.pop("_error_similarity", None)
            item.pop("_request_similarity", None)
            item.pop("_argument_similarity", None)

        return unique_experiences

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
