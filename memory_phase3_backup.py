
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
    """
    Save information only if an equivalent memory does not exist.

    Comparison ignores capitalization and repeated whitespace.
    Existing records are never deleted or rewritten.
    """
    if not isinstance(information, str):
        raise TypeError("Memory information must be a string.")

    information = information.strip()

    if not information:
        raise ValueError("Memory information cannot be empty.")

    def normalize(text):
        return " ".join(text.split()).casefold()

    normalized_information = normalize(information)
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        existing_memories = connection.execute(
            "SELECT information FROM memories"
        ).fetchall()

        for (existing_information,) in existing_memories:
            if normalize(existing_information) == normalized_information:
                return False

        connection.execute(
            "INSERT INTO memories (information) VALUES (?)",
            (information,),
        )
        connection.commit()
        return True
    finally:
        connection.close()



def get_memories():
    """Retrieve all saved personal information."""
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        return connection.execute("""
            SELECT id, information
            FROM memories
            ORDER BY id
        """).fetchall()
    finally:
        connection.close()



def get_relevant_memories(query, limit=5, min_score=0.12):
    """
    Retrieve personal memories ranked by relevance and preference topic.

    Topic-specific questions prioritize matching memories.
    Newer matching preference statements take priority over older ones.
    This function only reads existing records and never modifies memories.
    """
    if not isinstance(query, str) or not query.strip():
        return []

    if limit <= 0:
        return []

    query_lower = query.casefold()

    stop_words = {
        "the", "and", "for", "you", "are", "was", "were",
        "not", "with", "this", "that", "from", "have",
        "has", "had", "what", "which", "when", "where",
        "how", "why", "can", "could", "would", "should",
        "please", "tell", "show", "about", "your", "my",
        "me", "do", "does", "did", "is", "it", "in", "on",
        "to", "of", "a", "an", "i", "am", "we", "our",
        "like", "likes", "liked", "love", "loves",
        "favorite", "favourite", "prefer", "prefers",
        "preferred", "hobby",
    }

    def words(text):
        tokens = set(
            re.findall(r"\b[a-zA-Z0-9+#.]+\b", text.casefold())
        )
        return tokens - stop_words

    query_words = words(query)

    programming_languages = {
        "python", "java", "javascript", "typescript",
        "c", "c++", "c#", "go", "rust", "ruby", "kotlin",
        "swift", "php", "scala", "r", "dart", "perl",
        "matlab", "sql",
    }

    academic_subjects = {
        "math", "maths", "mathematics", "science",
        "physics", "chemistry", "biology", "english",
        "tamil", "history", "geography", "computer",
        "computer science", "computer networks",
        "machine learning", "deep learning",
    }

    # Identify the preference category requested by the user.
    topic = None

    topic_phrases = {
        "programming_language": (
            "programming language", "coding language",
            "language do i like", "language do i prefer",
            "language is my favorite", "language is my favourite",
        ),
        "subject": (
            "favorite subject", "favourite subject",
            "subject do i like", "subject do i prefer",
            "academic subject",
        ),
        "hobby": (
            "my hobby", "what is my hobby", "what are my hobbies",
            "hobbies do i have",
        ),
        "food": (
            "favorite food", "favourite food",
            "food do i like", "food do i prefer",
        ),
        "music": (
            "what music", "music do i like", "music do i prefer",
            "favorite music", "favourite music", "music preference",
            "music genre", "what genre",
        ),
        "color": (
            "favorite color", "favourite color",
            "favorite colour", "favourite colour",
            "color do i like", "colour do i like",
        ),
        "sport": (
            "favorite sport", "favourite sport",
            "sport do i like", "sport do i prefer",
        ),
    }

    for category, phrases in topic_phrases.items():
        if any(phrase in query_lower for phrase in phrases):
            topic = category
            break

    # Also recognize common forms such as "What is my hobby?"
    if topic is None:
        if "programming language" in query_lower:
            topic = "programming_language"
        elif "subject" in query_lower:
            topic = "subject"
        elif "hobby" in query_lower or "hobbies" in query_lower:
            topic = "hobby"
        elif "food" in query_lower:
            topic = "food"
        elif "music" in query_lower or "song" in query_lower:
            topic = "music"
        elif "color" in query_lower or "colour" in query_lower:
            topic = "color"
        elif "sport" in query_lower:
            topic = "sport"

    preference_question = (
        topic is not None
        or any(phrase in query_lower for phrase in (
            "what do i like",
            "what do i prefer",
            "what is my favorite",
            "what is my favourite",
        ))
    )

    def classify_memory(information):
        """
        Return the topic explicitly supported by a memory.
        Ambiguous statements are not assigned to unrelated topics.
        """
        text = information.casefold().strip()
        memory_words = words(text)

        if text.startswith(("full_name:", "nickname:")):
            return "identity"

        # Explicit topic labels take precedence.
        if any(phrase in text for phrase in (
            "programming language", "coding language",
            "favorite programming language",
            "favourite programming language",
        )):
            return "programming_language"

        if any(phrase in text for phrase in (
            "favorite subject", "favourite subject",
            "academic subject",
        )):
            return "subject"

        if "hobby" in text or "hobbies" in text:
            return "hobby"

        if any(phrase in text for phrase in (
            "favorite food", "favourite food",
            "food i like", "food i prefer",
        )):
            return "food"

        if any(phrase in text for phrase in (
            "favorite color", "favourite color",
            "favorite colour", "favourite colour",
        )):
            return "color"

        if any(phrase in text for phrase in (
            "favorite sport", "favourite sport",
        )):
            return "sport"

        # Detect generic "I like X" statements.
        is_like_statement = (
            text.startswith(("i like ", "i love ", "i prefer "))
            or text.startswith((
                "that i like ", "that i love ", "that i prefer ",
            ))
            or " i like " in f" {text} "
            or " i love " in f" {text} "
            or " i prefer " in f" {text} "
        )

        if is_like_statement:
            if memory_words & programming_languages:
                return "programming_language"

            if memory_words & {
                "music", "song", "songs", "singing",
                "melody", "melodies",
            }:
                return "music"

            if memory_words & {
                "pizza", "biryani", "food", "burger",
                "rice", "dosa", "idli", "pasta",
            }:
                return "food"

            if memory_words & {
                "red", "blue", "green", "yellow", "black",
                "white", "purple", "pink", "orange", "brown",
            }:
                return "color"

            if memory_words & academic_subjects:
                return "subject"

            if memory_words & {
                "cricket", "football", "tennis", "badminton",
                "basketball", "volleyball", "hockey",
            }:
                return "sport"

        return None

    memories = get_memories()
    ranked = []

    for memory_id, information in memories:
        memory_lower = information.casefold()
        memory_words = words(information)
        memory_topic = classify_memory(information)

        # For topic-specific questions, exclude memories that are
        # explicitly about another category.
        if topic is not None:
            if memory_topic != topic:
                continue

        intersection = len(query_words & memory_words)
        union = len(query_words | memory_words)

        jaccard = intersection / union if union else 0.0
        coverage = (
            intersection / len(query_words)
            if query_words else 0.0
        )
        score = 0.7 * jaccard + 0.3 * coverage

        # A topic match is useful even if the memory wording differs
        # from the question.
        if topic is not None:
            score = max(score, 0.25)

        if score < min_score:
            continue

        is_preference = (
            memory_topic is not None
            or memory_lower.startswith((
                "i like ", "i love ", "i prefer ",
                "my favorite ", "my favourite ",
                "my preferred ", "preferred ",
                "favorite ", "favourite ",
            ))
        )

        ranked.append({
            "id": memory_id,
            "information": information,
            "score": round(score, 4),
            "_is_preference": is_preference,
            "_topic": memory_topic,
        })

    if preference_question:
        ranked.sort(
            key=lambda item: (
                item["_is_preference"],
                item["id"],
                item["score"],
            ),
            reverse=True,
        )
    else:
        ranked.sort(
            key=lambda item: (item["score"], item["id"]),
            reverse=True,
        )

    results = ranked[:limit]

    # Preserve the original public result structure.
    for item in results:
        item.pop("_is_preference", None)
        item.pop("_topic", None)

    return results

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

    Historical experiences do not override the current request.
    Stored experiences do not train the LLM.
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
            tokens = set(
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
            return tokens - ignored

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

            if not union:
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
                "blocked": 0,
                "declined": 0,
                "success_rate": 0.0,
                "by_tool": [],
            }

        totals = connection.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN outcome = 'SUCCESS'
                    THEN 1 ELSE 0 END) AS successes,
                SUM(CASE WHEN outcome = 'FAILURE'
                    THEN 1 ELSE 0 END) AS failures,
                SUM(CASE WHEN outcome = 'BLOCKED'
                    THEN 1 ELSE 0 END) AS blocked,
                SUM(CASE WHEN outcome = 'DECLINED'
                    THEN 1 ELSE 0 END) AS declined
            FROM experiences
        """).fetchone()

        by_tool = connection.execute("""
            SELECT
                failed_tool,
                COUNT(*) AS attempts,
                SUM(CASE WHEN outcome = 'SUCCESS'
                    THEN 1 ELSE 0 END) AS successes,
                SUM(CASE WHEN outcome = 'FAILURE'
                    THEN 1 ELSE 0 END) AS failures,
                SUM(CASE WHEN outcome = 'BLOCKED'
                    THEN 1 ELSE 0 END) AS blocked,
                SUM(CASE WHEN outcome = 'DECLINED'
                    THEN 1 ELSE 0 END) AS declined
            FROM experiences
            GROUP BY failed_tool
            ORDER BY attempts DESC
        """).fetchall()

        total = totals["total"] or 0
        successes = totals["successes"] or 0
        failures = totals["failures"] or 0
        blocked = totals["blocked"] or 0
        declined = totals["declined"] or 0

        # Exclude blocked and declined decisions from attempted
        # recovery calculations.
        attempted_recoveries = successes + failures

        success_rate = (
            round(successes / attempted_recoveries * 100, 2)
            if attempted_recoveries
            else 0.0
        )

        return {
            "total": total,
            "successes": successes,
            "failures": failures,
            "blocked": blocked,
            "declined": declined,
            "success_rate": success_rate,
            "by_tool": [dict(row) for row in by_tool],
        }
    finally:
        connection.close()

def set_current_preference(topic, value):
    """Set the current preference without deleting historical memories."""
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS current_preferences (
                topic TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        connection.execute("""
            INSERT INTO current_preferences (topic, value)
            VALUES (?, ?)
            ON CONFLICT(topic) DO UPDATE SET value = excluded.value
        """, (topic, value))

        connection.commit()
    finally:
        connection.close()


def get_current_preference(topic):
    """Retrieve the current preference for a topic."""
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS current_preferences (
                topic TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        row = connection.execute(
            "SELECT value FROM current_preferences WHERE topic = ?",
            (topic,),
        ).fetchone()

        return row[0] if row else None
    finally:
        connection.close()