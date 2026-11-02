
import unittest

from memory import (
    get_memories,
    get_relevant_memories,
    get_current_preference,
    get_removed_likes,
)


class TestPhase4Memory(unittest.TestCase):

    def test_memory_database_is_readable(self):
        self.assertIsInstance(get_memories(), list)

    def test_favorite_language_retrieval(self):
        results = get_relevant_memories(
            "What is my favorite programming language?",
            limit=10,
            min_score=0.0,
        )

        information = [
            item["information"].casefold()
            for item in results
        ]

        self.assertTrue(
            any(
                "favorite programming language" in text
                and "java" in text
                for text in information
            ),
            "Expected the explicit Java favorite to be retrieved.",
        )

    def test_language_likes_retrieval(self):
        results = get_relevant_memories(
            "What programming languages do I like?",
            limit=10,
            min_score=0.0,
        )

        information = [
            item["information"].casefold()
            for item in results
        ]

        self.assertTrue(
            any("python" in text for text in information)
        )
        self.assertTrue(
            any("javascript" in text for text in information)
        )

    def test_food_history_is_not_empty(self):
        results = get_relevant_memories(
            "What is my favorite food?",
            limit=10,
            min_score=0.0,
        )

        self.assertTrue(
            any("food" in item["information"].casefold()
                for item in results)
        )

    def test_preference_lookup_is_safe(self):
        value = get_current_preference("programming_language")
        self.assertTrue(value is None or isinstance(value, str))

    def test_removed_likes_lookup_is_safe(self):
        removed = get_removed_likes("programming_language")
        self.assertIsInstance(removed, set)

    def test_retrieval_result_structure(self):
        results = get_relevant_memories(
            "What programming languages do I like?",
            limit=5,
        )

        for item in results:
            self.assertIn("id", item)
            self.assertIn("information", item)
            self.assertIn("score", item)


if __name__ == "__main__":
    unittest.main(verbosity=2)
