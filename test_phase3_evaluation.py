
"""Phase 3: deterministic evaluation of JARVIS safeguards."""

import unittest

from agent import (
    validate_tool_arguments,
    website_was_requested,
    tool_result_succeeded,
)


class Phase3EvaluationTests(unittest.TestCase):

    def test_01_valid_weather_arguments_are_accepted(self):
        result = validate_tool_arguments(
            "get_weather",
            {"city": "Chennai"},
        )
        self.assertIsNotNone(result[0])
        self.assertIsNone(result[1])

    def test_02_unknown_tool_arguments_are_rejected(self):
        result = validate_tool_arguments(
            "delete_everything",
            {},
        )
        self.assertIsNone(result[0])
        self.assertIn("Blocked unsupported tool", result[1])

    def test_03_unrequested_website_is_detected(self):
        result = website_was_requested(
            "Get the weather in Chennai",
            {"site_name": "github"},
        )
        self.assertFalse(result)

    def test_04_requested_website_is_allowed(self):
        result = website_was_requested(
            "Open YouTube",
            {"site_name": "youtube"},
        )
        self.assertTrue(result)

    def test_05_success_requires_success_flag(self):
        result = tool_result_succeeded(
            "get_weather",
            {
                "success": True,
                "tool": "get_weather",
                "data": {"city": "Chennai"},
                "error": None,
            },
        )
        self.assertTrue(result)

    def test_06_failure_is_not_counted_as_success(self):
        result = tool_result_succeeded(
            "get_weather",
            {
                "success": False,
                "tool": "get_weather",
                "data": None,
                "error": "City not found",
            },
        )
        self.assertFalse(result)

    def test_07_wrong_tool_result_is_rejected(self):
        result = tool_result_succeeded(
            "get_weather",
            {
                "success": True,
                "tool": "open_website",
                "data": {},
                "error": None,
            },
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
