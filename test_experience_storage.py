
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import memory


class ExperienceStorageTests(unittest.TestCase):

    def setUp(self):
        # Create an isolated temporary database for each test.
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(
            self.temp_dir.name,
            "test_memory.sqlite3",
        )

        self.db_patcher = patch.object(
            memory,
            "DATABASE_NAME",
            self.test_db,
        )
        self.db_patcher.start()

        memory.initialize_memory()

    def tearDown(self):
        self.db_patcher.stop()
        self.temp_dir.cleanup()

    def test_failed_outcome_is_saved(self):
        memory.save_experience(
            user_request="Get the weather in Chennai",
            failed_tool="get_weather",
            failed_arguments={"city": ""},
            error_message="Please provide a city name.",
            recovery_tool="get_weather",
            recovery_arguments={"city": "Chennai"},
            outcome="FAILURE",
        )

        connection = sqlite3.connect(self.test_db)
        try:
            row = connection.execute("""
                SELECT user_request, failed_tool, outcome
                FROM experiences
            """).fetchone()
        finally:
            connection.close()

        self.assertIsNotNone(row)
        self.assertEqual(
            row[0],
            "Get the weather in Chennai",
        )
        self.assertEqual(row[1], "get_weather")
        self.assertEqual(row[2], "FAILURE")

    def test_successful_outcome_is_saved(self):
        memory.save_experience(
            user_request="Get the weather in Mumbai",
            failed_tool="get_weather",
            failed_arguments={"city": ""},
            error_message="Please provide a city name.",
            recovery_tool="get_weather",
            recovery_arguments={"city": "Mumbai"},
            outcome="SUCCESS",
        )

        connection = sqlite3.connect(self.test_db)
        try:
            row = connection.execute("""
                SELECT outcome, recovery_arguments
                FROM experiences
            """).fetchone()
        finally:
            connection.close()

        self.assertEqual(row[0], "SUCCESS")
        self.assertIn("Mumbai", row[1])

    def test_failure_does_not_count_as_success(self):
        memory.save_experience(
            user_request="Test failed recovery",
            failed_tool="get_weather",
            failed_arguments={"city": ""},
            error_message="Test error",
            recovery_tool="get_weather",
            recovery_arguments={"city": ""},
            outcome="FAILURE",
        )

        stats = memory.get_experience_stats()

        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["failures"], 1)
        self.assertEqual(stats["successes"], 0)
        self.assertEqual(stats["success_rate"], 0.0)

    def test_existing_database_is_not_used(self):
        # The active database path must point to our temporary
        # test database, not the real project database.
        self.assertEqual(
            memory.DATABASE_NAME,
            self.test_db,
        )
        self.assertTrue(os.path.exists(self.test_db))


if __name__ == "__main__":
    unittest.main(verbosity=2)
