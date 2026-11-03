
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

    @patch("agent.format_tool_result")
    @patch("agent.execute_with_ai_recovery")
    @patch("agent.execute_with_recovery")
    def test_wrong_application_recovery_is_not_counted_as_success(
        self,
        mock_execute,
        mock_recovery,
        mock_format,
    ):
        """Opening another application must not satisfy the request."""

        mock_execute.return_value = (
            self.failure_result("open_application"),
            1,
            False,
        )

        mock_recovery.return_value = (
            self.success_result("open_application"),
            True,
            "open_application",
            {"app_name": "calculator"},
        )

        mock_format.return_value = "Application action completed"

        result = agent.execute_conditional_task("Open Notepad.")

        self.assertIn("Task incomplete", result)
        self.assertNotIn(
            "Recovery completed successfully.",
            result,
        )

    @patch("agent.verify_internet_connection")
    @patch("agent.format_tool_result")
    @patch("agent.execute_with_recovery")
    def test_internet_verification_success_is_reported(
        self,
        mock_execute,
        mock_format,
        mock_verify,
    ):
        """Successful independent verification should be reported."""

        mock_execute.return_value = (
            self.success_result("check_internet"),
            1,
            True,
        )

        mock_format.return_value = "Internet is working"

        mock_verify.return_value = {
            "success": True,
            "tool": "check_internet",
            "status": "verified",
            "evidence": {
                "check": "Independent HTTP request",
                "observed": "HTTP 200 returned by the test server.",
            },
            "error": None,
        }

        result = agent.execute_conditional_task(
            "Check my internet connection."
        )

        self.assertIn("Task completed successfully.", result)
        self.assertIn("independently verified", result)
        self.assertIn("HTTP 200", result)
        mock_verify.assert_called_once_with()

    @patch("agent.verify_internet_connection")
    @patch("agent.format_tool_result")
    @patch("agent.execute_with_recovery")
    def test_internet_verification_failure_is_reported(
        self,
        mock_execute,
        mock_format,
        mock_verify,
    ):
        """A failed independent check must not claim verification."""

        mock_execute.return_value = (
            self.success_result("check_internet"),
            1,
            True,
        )

        mock_format.return_value = "Internet check action succeeded"

        mock_verify.return_value = {
            "success": False,
            "tool": "check_internet",
            "status": "failed",
            "evidence": None,
            "error": "Independent connection check failed.",
        }

        result = agent.execute_conditional_task(
            "Check my internet connection."
        )

        self.assertIn("independent verification failed", result)
        self.assertNotIn(
            "Internet connectivity independently verified.",
            result,
        )
        self.assertIn("Independent connection check failed.", result)

    @patch("agent.verify_internet_connection")
    @patch("agent.format_tool_result")
    @patch("agent.execute_with_recovery")
    def test_malformed_verification_evidence_is_rejected(
        self,
        mock_execute,
        mock_format,
        mock_verify,
    ):
        """A success flag cannot replace valid verification evidence."""

        mock_execute.return_value = (
            self.success_result("check_internet"),
            1,
            True,
        )

        mock_format.return_value = "Internet check action succeeded"

        mock_verify.return_value = {
            "success": True,
            "tool": "check_internet",
            "status": "verified",
            "evidence": {
                "check": "   ",
                "observed": "",
            },
            "error": "Malformed verification evidence.",
        }

        result = agent.execute_conditional_task(
            "Check my internet connection."
        )

        self.assertIn("independent verification failed", result)
        self.assertNotIn(
            "Internet connectivity independently verified.",
            result,
        )
        self.assertIn("Malformed verification evidence.", result)

    @patch("agent.verify_internet_connection")
    @patch("agent.format_tool_result")
    @patch("agent.execute_with_recovery")
    def test_application_launch_is_not_internet_verified(
        self,
        mock_execute,
        mock_format,
        mock_verify,
    ):
        """An application launch must not trigger internet verification."""

        mock_execute.return_value = (
            self.success_result("open_application"),
            1,
            True,
        )

        mock_format.return_value = "Application launch request accepted"

        result = agent.execute_conditional_task("Open Notepad.")

        self.assertIn("Application launch request accepted", result)
        self.assertIn("Action accepted.", result)
        self.assertIn(
            "outcome has not been independently verified",
            result,
        )
        self.assertNotIn("Task completed successfully.", result)
        self.assertNotIn(
        "Internet connectivity independently verified.",
        result,
        )
        mock_verify.assert_not_called()

    @patch("agent.verify_internet_connection")
    @patch("agent.format_tool_result")
    @patch("agent.execute_with_ai_recovery")
    @patch("agent.execute_with_recovery")
    @patch("agent.ask_local_ai_for_next_action")
    def test_wrong_weather_city_recovery_does_not_satisfy_request(
        self,
        mock_next_action,
        mock_execute,
        mock_ai_recovery,
        mock_format,
        mock_verify,
    ):
        """Recovery for a different city must not satisfy the original request."""

        mock_next_action.side_effect = [
            {
                "done": False,
                "tool": "check_internet",
                "arguments": {},
                "message": "Check internet",
            },
            {
                "done": False,
                "tool": "get_weather",
                "arguments": {"city": "Mumbai"},
                "message": "Get Mumbai weather",
            },
            {
                "done": True,
                "message": "Task completed successfully.",
            },
        ]

        mock_execute.side_effect = [
            (self.success_result("check_internet"), 1, True),
            (self.failure_result("get_weather"), 1, False),
        ]

        mock_ai_recovery.return_value = (
            self.success_result("get_weather"),
            True,
            "get_weather",
            {"city": "Delhi"},
        )

        mock_format.side_effect = [
            "Internet is working",
            "Mumbai weather request failed",
            "Delhi weather retrieved",
        ]

        mock_verify.return_value = {
            "success": True,
            "tool": "check_internet",
            "status": "verified",
            "evidence": {
                "check": "Independent HTTP request",
                "observed": "HTTP 200 returned by the test server.",
            },
            "error": None,
        }

        result = agent.execute_conditional_task(
            "Check my internet connection and get the weather in Mumbai."
        )

        self.assertIn("incomplete", result.lower())
        self.assertNotIn("Task completed successfully.", result)

    @patch("agent.execute_with_recovery")
    @patch("agent.ask_local_ai_for_next_action")
    def test_agent_stops_after_maximum_steps(
        self,
        mock_next_action,
        mock_execute,
    ):
        """The agent must stop when the AI never finishes the task."""

        mock_next_action.return_value = {
            "done": False,
            "tool": "get_weather",
            "arguments": {"city": "Mumbai"},
            "message": "Get the weather",
        }

        mock_execute.return_value = (
            self.success_result("get_weather"),
            1,
            True,
        )

        result = agent.execute_conditional_task(
            "Check the internet and get the weather in Mumbai."
        )

        self.assertIn("maximum of 5 actions", result)
        self.assertEqual(mock_execute.call_count, 5)
        self.assertEqual(mock_next_action.call_count, 5)

    @patch("agent.format_tool_result")
    @patch("agent.ask_local_ai_for_next_action")
    @patch("agent.execute_with_recovery")
    def test_wrong_weather_city_is_not_counted_as_success(
        self,
        mock_execute,
        mock_next_action,
        mock_format,
    ):
        """Weather for the wrong city must not satisfy the request."""

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
                "arguments": {"city": "Delhi"},
            },
            {
                "done": True,
                "message": "Everything is complete.",
            },
        ]

        mock_format.return_value = "Action succeeded"

        result = agent.execute_conditional_task(
            "Check my internet connection and get the weather in Mumbai."
        )

        self.assertIn("Task incomplete", result)
        self.assertIn("Mumbai", result)

    @patch("agent.verify_internet_connection")
    @patch("agent.format_tool_result")
    @patch("agent.execute_with_recovery")
    @patch("agent.ask_local_ai_for_next_action")
    def test_wrong_application_is_not_counted_as_success(
        self,
        mock_next_action,
        mock_execute,
        mock_format,
        mock_verify,
    ):
        """The AI must not substitute another application."""

        mock_next_action.side_effect = [
            {
                "done": False,
                "tool": "check_internet",
                "arguments": {},
            },
            {
                "done": False,
                "tool": "open_application",
                "arguments": {"app_name": "Calculator"},
            },
        ]

        mock_execute.return_value = (
            self.success_result("check_internet"),
            1,
            True,
        )

        mock_format.return_value = "Action succeeded"

        mock_verify.return_value = {
            "success": True,
            "tool": "check_internet",
            "status": "verified",
            "evidence": {
                "check": "Independent HTTP request",
                "observed": "HTTP 200 returned by the test server.",
            },
            "error": None,
        }

        result = agent.execute_conditional_task(
            "Check my internet connection and open Notepad."
        )

        self.assertIn("Task incomplete", result)
        self.assertIn("notepad", result.lower())
        self.assertIn("calculator", result.lower())

        # Only the internet check should execute.
        self.assertEqual(mock_execute.call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
