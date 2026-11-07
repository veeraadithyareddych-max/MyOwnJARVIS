import os
import tempfile
import unittest
from unittest.mock import patch

import memory


class TestMemoryUpdate(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()

        self.database_path = os.path.join(
            self.temp_directory.name,
            "test_memory.sqlite3",
        )

        self.database_patch = patch.object(
            memory,
            "DATABASE_NAME",
            self.database_path,
        )

        self.database_patch.start()

        memory.initialize_memory()

    def tearDown(self):
        self.database_patch.stop()
        self.temp_directory.cleanup()

    def test_update_memory_changes_existing_memory(self):
        self.assertTrue(
            memory.save_memory(
                "User prefers Java programming."
            )
        )

        memory_id = memory.get_memories()[0][0]

        updated = memory.update_memory(
            memory_id,
            "User prefers Python programming.",
        )

        self.assertTrue(updated)

        memories = memory.get_memories()

        self.assertEqual(
            memories[0][1],
            "User prefers Python programming.",
        )

    def test_update_memory_recalculates_category(self):
        memory.save_memory(
            "User is studying computer science."
        )

        memory_id = memory.get_memories()[0][0]

        updated = memory.update_memory(
            memory_id,
            "User is building a software project.",
        )

        self.assertTrue(updated)

        connection = memory.sqlite3.connect(
            memory.DATABASE_NAME
        )

        try:
            row = connection.execute(
                """
                SELECT category
                FROM memory_categories
                WHERE memory_id = ?
                """,
                (memory_id,),
            ).fetchone()
        finally:
            connection.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "project")

    def test_update_memory_rejects_duplicate_information(self):
        memory.save_memory(
            "User prefers Java."
        )

        memory.save_memory(
            "User prefers Python."
        )

        memories = memory.get_memories()

        first_id = memories[0][0]
        second_id = memories[1][0]

        updated = memory.update_memory(
            second_id,
            "  USER   PREFERS   JAVA.  ",
)

        self.assertFalse(updated)

        memories = memory.get_memories()

        self.assertEqual(
            memories[0][1],
            "User prefers Java.",
        )

        self.assertEqual(
            memories[1][1],
            "User prefers Python.",
        )

    def test_update_memory_returns_false_for_missing_id(self):
        updated = memory.update_memory(
            999999,
            "User prefers Java.",
        )

        self.assertFalse(updated)

    def test_update_memory_rejects_empty_information(self):
        memory.save_memory(
            "User prefers Java."
        )

        memory_id = memory.get_memories()[0][0]

        with self.assertRaises(ValueError):
            memory.update_memory(
                memory_id,
                "   ",
            )

    def test_update_memory_rejects_invalid_information_type(self):
        memory.save_memory(
            "User prefers Java."
        )

        memory_id = memory.get_memories()[0][0]

        with self.assertRaises(TypeError):
            memory.update_memory(
                memory_id,
                123,
            )

    def test_update_memory_rejects_invalid_id_type(self):
        with self.assertRaises(TypeError):
            memory.update_memory(
                "1",
                "User prefers Java.",
            )

    def test_forget_memory_removes_existing_memory(self):
        memory.save_memory(
            "User prefers Java."
        )

        memory_id = memory.get_memories()[0][0]

        removed = memory.forget_memory(
            memory_id
        )

        self.assertTrue(removed)

        self.assertEqual(
            memory.get_memories(),
            [],
        )

    def test_forget_memory_removes_category(self):
        memory.save_memory(
            "User is studying computer science."
        )

        memory_id = memory.get_memories()[0][0]

        removed = memory.forget_memory(
            memory_id
        )

        self.assertTrue(removed)

        connection = memory.sqlite3.connect(
            memory.DATABASE_NAME
        )

        try:
            row = connection.execute(
                """
                SELECT memory_id
                FROM memory_categories
                WHERE memory_id = ?
                """,
                (memory_id,),
            ).fetchone()
        finally:
            connection.close()

        self.assertIsNone(row)

    def test_forget_memory_returns_false_for_missing_id(self):
        removed = memory.forget_memory(
            999999
        )

        self.assertFalse(removed)

    def test_forget_memory_rejects_invalid_id_type(self):
        with self.assertRaises(TypeError):
            memory.forget_memory(
                "1"
            )

    def test_forget_memory_does_not_remove_other_memories(self):
        memory.save_memory(
            "User prefers Java."
        )

        memory.save_memory(
            "User is studying computer science."
        )

        memories = memory.get_memories()

        first_id = memories[0][0]

        removed = memory.forget_memory(
            first_id
        )

        self.assertTrue(removed)

        remaining_memories = memory.get_memories()

        self.assertEqual(
            len(remaining_memories),
            1,
        )

        self.assertEqual(
            remaining_memories[0][1],
            "User is studying computer science.",
        )

if __name__ == "__main__":
    unittest.main()
