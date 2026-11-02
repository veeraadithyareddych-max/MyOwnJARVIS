
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import memory


class MemoryDuplicateTests(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name) / "test_memory.sqlite3"
        )

        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            memory.initialize_memory()

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_first_memory_is_saved(self):
        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            result = memory.save_memory(
                "My favorite programming language is Java."
            )

        self.assertTrue(result)

    def test_exact_duplicate_is_rejected(self):
        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            first = memory.save_memory("I like Java.")
            second = memory.save_memory("I like Java.")

        self.assertTrue(first)
        self.assertFalse(second)

    def test_case_and_whitespace_duplicates_are_rejected(self):
        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            first = memory.save_memory("I like Java.")
            second = memory.save_memory("  i LIKE java.  ")

        self.assertTrue(first)
        self.assertFalse(second)

    def test_different_memory_is_saved(self):
        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            first = memory.save_memory("I like Java.")
            second = memory.save_memory("I like Python.")

        self.assertTrue(first)
        self.assertTrue(second)

    def test_empty_memory_is_rejected(self):
        with patch.object(memory, "DATABASE_NAME", str(self.database_path)):
            with self.assertRaises(ValueError):
                memory.save_memory("   ")


if __name__ == "__main__":
    unittest.main(verbosity=2)
