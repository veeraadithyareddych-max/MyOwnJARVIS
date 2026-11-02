
import sqlite3
import json
import re
from datetime import datetime

DATABASE_NAME = "jarvis_memory.sqlite3"


# ============================================================
# 1. MEMORY CATEGORY DETECTION
# ============================================================



def detect_memory_category(information):
    """Classify memories by their most specific matching category."""
    text = information.lower()

    # Education: subjects and academic details
    if any(word in text for word in [
        "student", "college", "university", "degree",
        "semester", "academic year", "studying",
        "department", "engineering", "favorite subject",
        "favourite subject", "maths", "mathematics",
        "science subject", "school"
    ]):
        return "education"

    # Projects and development work
    if any(word in text for word in [
        "project", "application", "website", "hackathon",
        "duplicate prevention test", "developing",
        "built an app", "building an app"
    ]):
        return "project"

    # Goals and ambitions
    if any(word in text for word in [
        "goal", "aim", "want to become", "want to get",
        "career target", "salary target", "plan to",
        "my ambition", "i hope to", "placement"
    ]):
        return "goal"

    # Technical skills and programming
    if any(word in text for word in [
        "programming language", "coding", "python",
        "java", "javascript", "programming skill",
        "proficient", "technical skill"
    ]):
        return "skill"

    # Personal identity
    if any(word in text for word in [
        "full_name:", "nickname:", "my name",
        "call me", "my birthday", "my age"
    ]):
        return "personal"

    # Preferences and hobbies
    if any(word in text for word in [
        "favorite", "favourite", "i like", "i love",
        "i enjoy", "i prefer", "my hobby", "i also like"
    ]):
        return "preference"

    return "general"



# ============================================================
# 2. INITIALIZE DATABASE TABLES
# ============================================================

def initialize_memory():
    """
    Create required tables if they do not exist.
    Existing memory and experience records are preserved.
    """
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                information TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS memory_categories (
                memory_id INTEGER PRIMARY KEY,
                category TEXT NOT NULL,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS current_preferences (
                topic TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS removed_likes (
                topic TEXT NOT NULL,
                item TEXT NOT NULL,
                PRIMARY KEY (topic, item)
            )
        """)

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

        connection.commit()
    finally:
        connection.close()


def initialize_memory_categories():
    """Create the memory categories table."""
    initialize_memory()


def categorize_existing_memories():
    """
    Categorize existing memories that do not yet have a category.
    Existing memory text and IDs are not changed.
    """
    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        rows = connection.execute("""
            SELECT m.id, m.information
            FROM memories AS m
            LEFT JOIN memory_categories AS c
                ON m.id = c.memory_id
            WHERE c.memory_id IS NULL
        """).fetchall()

        for memory_id, information in rows:
            category = detect_memory_category(information)

            connection.execute("""
                INSERT OR IGNORE INTO memory_categories
                    (memory_id, category)
                VALUES (?, ?)
            """, (memory_id, category))

        connection.commit()
        return len(rows)
    finally:
        connection.close()



def recategorize_all_memories():
    """Update category labels without changing or deleting memories."""
    initialize_memory()

    conn = sqlite3.connect("jarvis_memory.sqlite3")
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, information FROM memories")
        memories = cursor.fetchall()

        for memory_id, information in memories:
            category = detect_memory_category(information)

            cursor.execute(
                """
                INSERT INTO memory_categories (memory_id, category)
                VALUES (?, ?)
                ON CONFLICT(memory_id)
                DO UPDATE SET category = excluded.category
                """,
                (memory_id, category)
            )

        conn.commit()
        return len(memories)

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_memories_by_category(category):
    """Return memories belonging to a category, newest first."""
    if not isinstance(category, str) or not category.strip():
        return []

    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        rows = connection.execute("""
            SELECT m.id, m.information
            FROM memories AS m
            JOIN memory_categories AS c
                ON m.id = c.memory_id
            WHERE c.category = ?
            ORDER BY m.id DESC
        """, (category.strip().casefold(),)).fetchall()

        return rows
    finally:
        connection.close()


# ============================================================
# 3. SAVE PERSONAL MEMORIES
# ============================================================

def save_memory(information):
    """
    Save information if an equivalent memory does not exist.

    Duplicate checking ignores capitalization and repeated
    whitespace. Existing records are never deleted or rewritten.

    Returns True if saved, False if an equivalent record exists.
    """
    if not isinstance(information, str):
        raise TypeError("Memory information must be a string.")

    information = information.strip()

    if not information:
        raise ValueError("Memory information cannot be empty.")

    def normalize(text):
        return " ".join(text.split()).casefold()

    normalized_information = normalize(information)

    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        existing_memories = connection.execute(
            "SELECT information FROM memories"
        ).fetchall()

        for (existing_information,) in existing_memories:
            if normalize(existing_information) == normalized_information:
                return False

        cursor = connection.execute(
            "INSERT INTO memories (information) VALUES (?)",
            (information,),
        )

        memory_id = cursor.lastrowid
        category = detect_memory_category(information)

        connection.execute("""
            INSERT INTO memory_categories (memory_id, category)
            VALUES (?, ?)
        """, (memory_id, category))

        connection.commit()
        return True
    finally:
        connection.close()


def get_memories():
    """Retrieve all saved personal information, oldest first."""
    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        return connection.execute("""
            SELECT id, information
            FROM memories
            ORDER BY id
        """).fetchall()
    finally:
        connection.close()


# ============================================================
# 4. SEARCH RELEVANT PERSONAL MEMORIES
# ============================================================

def get_relevant_memories(query, limit=5, min_score=0.12):
    """
    Retrieve personal memories ranked by text relevance and topic.

    Topic-specific questions prioritize matching memories.
    This function only reads existing memory records.
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

    topic = None

    topic_phrases = {
            "favorite_programming_language": (
            "favorite programming language",
            "favourite programming language",
            "my preferred programming language",
            "my preferred coding language",
            "what is my favorite programming language",
            "what is my favourite programming language",
        ),
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
        """Return a topic explicitly supported by a memory."""
        text = information.casefold().strip()
        memory_words = words(text)

        if text.startswith(("full_name:", "nickname:")):
            return "identity"

        if any(phrase in text for phrase in (
            "favorite programming language",
            "favourite programming language",
            "my preferred programming language",
            "my preferred coding language",
        )):
            return "favorite_programming_language"

        if any(phrase in text for phrase in (
            "programming language",
            "coding language",
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

        is_like_statement = (
            text.startswith((
                "i like ", "i love ", "i prefer ",
                "i enjoy ", "i also like ", "i also love ",
            ))
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

        compatible_topics = {
            "programming_language": {
                "programming_language",
                "favorite_programming_language",
            },
            "favorite_programming_language": {
                "favorite_programming_language",
            },
        }

        if topic is not None:
            allowed_topics = compatible_topics.get(topic, {topic})

            if memory_topic not in allowed_topics:
                continue

        intersection = len(query_words & memory_words)
        union = len(query_words | memory_words)

        jaccard = intersection / union if union else 0.0
        coverage = (
            intersection / len(query_words)
            if query_words else 0.0
        )
        score = 0.7 * jaccard + 0.3 * coverage

                # Give a relevance boost only when a memory matches
        # the detected topic. Do not boost unrelated memories.
        if topic is not None and memory_topic == topic:
            score = max(score, 0.25)

        if score <= 0 or score < min_score:
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

        # Remove duplicate memory text from the retrieval results.
    # This does not delete or modify database records.
    unique_ranked = []
    seen_information = set()

    for item in ranked:
        normalized_information = " ".join(
            item["information"].casefold().split()
        )

        if normalized_information in seen_information:
            continue

        seen_information.add(normalized_information)
        unique_ranked.append(item)

    results = unique_ranked[:limit]

    for item in results:
        item.pop("_is_preference", None)
        item.pop("_topic", None)

    return results


# ============================================================
# 5. SAVE AGENT EXPERIENCES
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
    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)

    try:
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
# 6. RETRIEVE RECENT EXPERIENCES
# ============================================================

def get_recent_experiences(limit=5):
    """Retrieve the most recent agent experiences."""
    if limit <= 0:
        return []

    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    try:
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
# 7. RETRIEVE RELEVANT EXPERIENCES
# ============================================================

def get_relevant_experiences(
    failed_tool,
    error_message="",
    limit=5,
    user_request="",
):
    """
    Rank prior recovery experiences by request relevance,
    error similarity, recovery arguments, outcome, and recency.
    """
    if limit <= 0:
        return []

    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    try:
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
            tokens = set(re.findall(
                r"\b[a-zA-Z]{3,}\b",
                (text or "").lower(),
            ))
            ignored = (
                stop_words if ignored_words is None
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
            user_request, request_stop_words
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
                current_error_words, past_error_words
            )
            request_similarity = word_similarity(
                current_request_words, past_request_words
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
                recovery_argument_text, request_stop_words
            )

            argument_similarity = word_similarity(
                current_request_words, recovery_argument_words
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
# 8. EXPERIENCE AND RECOVERY STATISTICS
# ============================================================

def get_experience_stats():
    """Return statistics about recorded recovery outcomes."""
    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    try:
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

        attempted_recoveries = successes + failures

        success_rate = (
            round(successes / attempted_recoveries * 100, 2)
            if attempted_recoveries else 0.0
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


# ============================================================
# 9. CURRENT PREFERENCES
# ============================================================

def set_current_preference(topic, value):
    """Update the current preference without deleting history."""
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Preference topic cannot be empty.")

    if not isinstance(value, str) or not value.strip():
        raise ValueError("Preference value cannot be empty.")

    topic = topic.strip().casefold()
    value = value.strip()

    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)

    try:
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
    if not isinstance(topic, str) or not topic.strip():
        return None

    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        row = connection.execute(
            "SELECT value FROM current_preferences WHERE topic = ?",
            (topic.strip().casefold(),),
        ).fetchone()

        return row[0] if row else None
    finally:
        connection.close()


# ============================================================
# 10. REMOVED LIKES
# ============================================================

def remove_like(topic, item):
    """Mark an item as no longer liked without deleting history."""
    if not isinstance(topic, str) or not isinstance(item, str):
        return False

    topic = topic.strip().casefold()
    item = item.strip().casefold()

    if not topic or not item:
        return False

    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        connection.execute("""
            INSERT OR IGNORE INTO removed_likes (topic, item)
            VALUES (?, ?)
        """, (topic, item))

        connection.commit()
        return True
    finally:
        connection.close()


def get_removed_likes(topic):
    """Return items explicitly marked as no longer liked."""
    if not isinstance(topic, str) or not topic.strip():
        return set()

    topic = topic.strip().casefold()
    initialize_memory()
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        rows = connection.execute(
            "SELECT item FROM removed_likes WHERE topic = ?",
            (topic,),
        ).fetchall()

        return {row[0] for row in rows}
    finally:
        connection.close()
