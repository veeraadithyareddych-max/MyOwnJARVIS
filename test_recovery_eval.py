
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

from agent import (
    execute_with_ai_recovery,
    make_tool_result,
    validate_tool_arguments,
)


class RecoveryDecisionTests(unittest.TestCase):

    def setUp(self):
        self.user_request = "Get the weather in Chennai"
        self.failed_tool = "get_weather"
        self.arguments = {"city": ""}
        self.error_message = "Please provide a city name."
        self.execution_history = [
            "Weather request failed because the city was empty."
        ]

    def test_01_recover_city_from_current_request(self):
        from llm import ask_local_ai_for_recovery

        result = ask_local_ai_for_recovery(
            user_request=self.user_request,
            failed_tool=self.failed_tool,
            arguments=self.arguments,
            error_message=self.error_message,
            execution_history="\n".join(self.execution_history),
            past_experiences=[],
        )

        self.assertIsInstance(result, dict)
        self.assertIs(result.get("recover"), True)
        self.assertEqual(result.get("tool"), "get_weather")
        self.assertEqual(
            result.get("arguments", {}).get("city"),
            "Chennai",
        )

    def test_02_current_request_overrides_conflicting_memory(self):
        from llm import ask_local_ai_for_recovery

        experiences = [
            {
                "failed_tool": "get_weather",
                "error_message": self.error_message,
                "recovery_tool": "get_weather",
                "recovery_arguments": {"city": "Mumbai"},
                "outcome": "SUCCESS",
            }
        ]

        result = ask_local_ai_for_recovery(
            user_request=self.user_request,
            failed_tool=self.failed_tool,
            arguments=self.arguments,
            error_message=self.error_message,
            execution_history="\n".join(self.execution_history),
            past_experiences=experiences,
        )

        self.assertIsInstance(result, dict)
        self.assertIs(result.get("recover"), True)
        self.assertEqual(result.get("tool"), "get_weather")
        self.assertEqual(
            result.get("arguments", {}).get("city"),
            "Chennai",
        )

    
    def test_03_declined_recovery_stops_execution(self):
        declined_decision = {
            "recover": False,
            "reason": "No safe recovery is available.",
        }

        history = self.execution_history.copy()

        with patch(
            "agent.ask_local_ai_for_recovery",
            return_value=declined_decision,
        ), patch(
            "agent.save_experience",
        ) as mock_save, patch(
            "agent.execute_tool",
        ) as mock_execute:

            result, succeeded, tool, arguments = (
                execute_with_ai_recovery(
                    user_request=self.user_request,
                    tool_name=self.failed_tool,
                    arguments=self.arguments,
                    initial_error=self.error_message,
                    execution_history=history,
                )
            )

        self.assertFalse(succeeded)
        self.assertFalse(result["success"])
        self.assertEqual(tool, "get_weather")
        self.assertEqual(arguments, {"city": ""})

        # Declined decisions should be saved separately.
        mock_save.assert_called_once()
        self.assertEqual(
            mock_save.call_args.kwargs["outcome"],
            "DECLINED",
        )
        
        
    def test_06_blocked_recovery_is_recorded_without_execution(self):
        blocked_decision = {
            "recover": True,
            "tool": "delete_everything",
            "arguments": {},
            "reason": "Attempt an unknown tool.",
        }

        history = self.execution_history.copy()

        with patch(
            "agent.ask_local_ai_for_recovery",
            return_value=blocked_decision,
        ), patch(
            "agent.save_experience",
        ) as mock_save, patch(
            "agent.execute_tool",
        ) as mock_execute:

            result, succeeded, tool, arguments = (
                execute_with_ai_recovery(
                    user_request=self.user_request,
                    tool_name=self.failed_tool,
                    arguments=self.arguments,
                    initial_error=self.error_message,
                    execution_history=history,
                )
            )

        self.assertFalse(succeeded)
        self.assertFalse(result["success"])

        # A rejected tool must be recorded as BLOCKED.
        mock_save.assert_called_once()
        self.assertEqual(
            mock_save.call_args.kwargs["outcome"],
            "BLOCKED",
        )

        # The rejected tool must never execute.
        mock_execute.assert_not_called()


        # No new tool action should execute.
        mock_execute.assert_not_called()


    def test_04_unknown_tool_is_rejected(self):
        normalized, error = validate_tool_arguments(
            "delete_everything",
            {},
        )

        self.assertTrue(
            error or normalized is None,
            "An unknown tool should not pass validation.",
        )

    def test_05_duplicate_recovery_action_is_blocked(self):
        valid_arguments = {"city": "Chennai"}

        repeated_decision = {
            "recover": True,
            "tool": "get_weather",
            "arguments": valid_arguments,
            "reason": "Retry the same action.",
        }

        captured_output = StringIO()
        history = self.execution_history.copy()

        with patch(
            "agent.ask_local_ai_for_recovery",
            return_value=repeated_decision,
        ), patch(
            "agent.execute_tool",
            return_value=make_tool_result(
                False,
                "get_weather",
                error="Simulated weather failure.",
            ),
        ) as mock_execute_tool:

            with redirect_stdout(captured_output):
                result, succeeded, tool, arguments = (
                    execute_with_ai_recovery(
                        user_request=self.user_request,
                        tool_name="get_weather",
                        arguments=valid_arguments,
                        initial_error="Simulated weather failure.",
                        execution_history=history,
                        max_recovery_attempts=2,
                    )
                )

        output = captured_output.getvalue().lower()

        self.assertIn(
            "duplicate action detected",
            output,
            "JARVIS should detect and report a repeated action.",
        )
        self.assertFalse(succeeded)
        self.assertFalse(result["success"])

        # The repeated action must be blocked before tool execution.
        self.assertEqual(mock_execute_tool.call_count, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
