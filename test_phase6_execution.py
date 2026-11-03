import unittest
from unittest.mock import patch

import agent


class Phase6ExecutionTests(unittest.TestCase):
    """Tests for safe, context-aware multi-step task execution."""

    def success_result(self, tool_name):
        return {
            "success": True,
            "tool": tool_name,
            "data": {"message": f"{tool_name} succeeded"},
        }

    def failure_result(self, tool_name):
        return {
            "success": False,
            "tool": tool_name,
            "error": f"{tool_name} failed",
        }

    @patch("agent.format_tool_result")
    @patch("agent.ask_local_ai_for_next_action")
    @patch("agent.execute_with_recovery")
    def test_both_required_tools_execute_successfully(
        self,
        mock_execute,
        mock_next_action,
        mock_format,
    ):
        """Internet and weather must both succeed for the task to complete."""

        mock_execute.side_effect = [
            (self.success_result("check_internet"), 1, True),
            (self.success_result("get_weather"), 1, True),
        ]

        mock_next_action.side_effect = [
            {
                "done": False,
                "tool": "check_internet",
                "arguments": {},
            },
            {
                "done": False,
                "tool": "get_weather",
                "arguments": {"city": "Mumbai"},
            },
        ]

        mock_format.return_value = "Action succeeded"

        result = agent.execute_conditional_task(
            "Check my internet connection and get the weather in Mumbai."
        )

        self.assertIn("All requested tool actions succeeded.", result)
        self.assertEqual(mock_execute.call_count, 2)

        executed_tools = [
            call.args[0] for call in mock_execute.call_args_list
        ]
        self.assertEqual(
            executed_tools,
            ["check_internet", "get_weather"],
        )

    @patch("agent.format_tool_result")
    @patch("agent.execute_with_ai_recovery")
    @patch("agent.ask_local_ai_for_next_action")
    @patch("agent.execute_with_recovery")
    def test_weather_does_not_execute_when_internet_fails(
        self,
        mock_execute,
        mock_next_action,
        mock_recovery,
        mock_format,
    ):
        """A failed internet prerequisite must stop the task."""

        mock_execute.return_value = (
            self.failure_result("check_internet"),
            2,
            False,
        )

        mock_next_action.return_value = {
            "done": False,
            "tool": "check_internet",
            "arguments": {},
        }

        mock_recovery.return_value = (
            self.failure_result("check_internet"),
            False,
            "check_internet",
            {},
        )

        mock_format.side_effect = lambda result: (
            "Action succeeded"
            if result.get("success") is True
            else "Internet check failed"
        )

        result = agent.execute_conditional_task(
            "Check my internet connection and get the weather in Mumbai."
        )

        self.assertIn("Task incomplete:", result)
        self.assertEqual(mock_execute.call_count, 1)

        executed_tools = [
            call.args[0] for call in mock_execute.call_args_list
        ]
        self.assertNotIn("get_weather", executed_tools)

    @patch("agent.ask_local_ai_for_next_action")
    @patch("agent.execute_with_recovery")
    def test_agent_cannot_claim_success_when_required_tools_are_missing(
        self,
        mock_execute,
        mock_next_action,
    ):
        """An AI 'done' decision cannot bypass required actions."""

        mock_next_action.return_value = {
            "done": True,
            "message": "Everything is complete.",
        }

        result = agent.execute_conditional_task(
            "Check my internet connection and get the weather in Mumbai."
        )

        self.assertIn("Task incomplete.", result)
        self.assertIn("check_internet", result)
        self.assertIn("get_weather", result)
        mock_execute.assert_not_called()

    @patch("agent.format_tool_result")
    @patch("agent.execute_with_ai_recovery")
    @patch("agent.ask_local_ai_for_next_action")
    @patch("agent.execute_with_recovery")
    def test_failed_recovery_is_not_counted_as_success(
        self,
        mock_execute,
        mock_next_action,
        mock_recovery,
        mock_format,
    ):
        """A failed recovery must not make a required action successful."""

        mock_execute.return_value = (
            self.failure_result("check_internet"),
            2,
            False,
        )

        mock_next_action.return_value = {
            "done": False,
            "tool": "check_internet",
            "arguments": {},
        }

        mock_recovery.return_value = (
            self.failure_result("check_internet"),
            False,
            "check_internet",
            {},
        )

        mock_format.side_effect = lambda result: (
            "Action succeeded"
            if result.get("success") is True
            else "Recovery failed"
        )

        result = agent.execute_conditional_task(
            "Check my internet connection and get the weather in Mumbai."
        )

        self.assertIn("Task incomplete:", result)
        self.assertIn("Recovery failed", result)
        self.assertEqual(mock_execute.call_count, 1)

    @patch("agent.format_tool_result")
    @patch("agent.execute_with_recovery")
    def test_single_tool_request_still_works(
        self,
        mock_execute,
        mock_format,
    ):
        """A single-tool request should keep using the direct-action path."""

        mock_execute.return_value = (
            self.success_result("check_internet"),
            1,
            True,
        )
        mock_format.return_value = "Internet is working"

        result = agent.execute_conditional_task(
            "Check my internet connection."
        )

        self.assertIn("Task completed successfully.", result)
        self.assertIn("Internet is working", result)
        mock_execute.assert_called_once_with(
            "check_internet",
            {},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)