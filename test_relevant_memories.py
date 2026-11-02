
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import memory


class RelevantMemoryTests(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name) / "test_memory.sqlite3"
        )

        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            memory.initialize_memory()

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_relevant_memory_is_returned(self):
        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            memory.save_memory(
                "My favorite programming language is Java."
            )
            memory.save_memory(
                "I am building the ShopSpot marketplace project."
            )

            results = memory.get_relevant_memories(
                "Which programming language do I prefer?"
            )

        self.assertTrue(results)
        self.assertEqual(
            results[0]["information"],
            "My favorite programming language is Java.",
        )

    def test_unrelated_memory_is_not_returned(self):
        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            memory.save_memory(
                "I am building the ShopSpot marketplace project."
            )

            results = memory.get_relevant_memories(
                "What is my favorite programming language?",
                min_score=0.20,
            )

        self.assertEqual(results, [])

    def test_empty_query_returns_no_results(self):
        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            memory.save_memory("I prefer Java.")

            self.assertEqual(memory.get_relevant_memories(""), [])
            self.assertEqual(memory.get_relevant_memories("   "), [])

    def test_limit_is_respected(self):
        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            memory.save_memory("I enjoy Java programming.")
            memory.save_memory("I practice Java coding.")
            memory.save_memory("I study Java development.")

            results = memory.get_relevant_memories(
                "Java programming coding development",
                limit=2,
                min_score=0.0,
            )

        self.assertEqual(len(results), 2)

    def test_nonpositive_limit_returns_no_results(self):
        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            memory.save_memory("I prefer Java.")

            self.assertEqual(
                memory.get_relevant_memories("Java", limit=0),
                [],
            )


    def test_newer_programming_preference_ranks_above_older_one(self):
        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            memory.save_memory(
                "My favorite programming language is Java."
            )
            memory.save_memory(
                "I like Python as my programming language."
            )

            results = memory.get_relevant_memories(
                "What programming language do I like?",
                min_score=0.0,
            )

        self.assertTrue(results)
        self.assertEqual(
            results[0]["information"],
            "I like Python as my programming language.",
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)
