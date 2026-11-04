
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

import main


class MainRoutingIntegrationTests(unittest.TestCase):
    """Integration tests for the interactive main conversation loop."""

    def setUp(self):
        self.original_history = (
            main.SESSION_CONVERSATION_HISTORY.copy()
        )

    def tearDown(self):
        main.SESSION_CONVERSATION_HISTORY[:] = (
            self.original_history
        )

    def run_main_with_input(self, inputs):
        """Run the real main loop with simulated user input."""

        output = StringIO()

        with patch(
            "builtins.input",
            side_effect=inputs,
        ), patch(
            "main.handle_memory_command",
            return_value=None,
        ), patch(
            "main.predict_intent",
            return_value="chat",
        ), patch(
            "main.save_java_examples_from_response",
        ), redirect_stdout(output):
            main.main()

        return output.getvalue()

    def test_ordinary_message_uses_normal_response_path(self):
        """Ordinary conversation should not invoke the tool executor."""

        with patch(
            "main.respond_to_user",
            return_value="Hello from JARVIS",
        ) as mock_response, patch(
            "main.execute_conditional_task",
        ) as mock_executor:
            self.run_main_with_input(["Hello JARVIS", "exit"])

        mock_response.assert_called_once_with("Hello JARVIS")
        mock_executor.assert_not_called()

    def test_website_request_uses_conditional_executor(self):
        """Website requests must pass through the conditional executor."""

        with patch(
            "main.respond_to_user",
            return_value="Normal response",
        ) as mock_response, patch(
            "main.execute_conditional_task",
            return_value="Website action handled",
        ) as mock_executor:
            self.run_main_with_input(["Open Google", "exit"])

        mock_executor.assert_called_once_with("Open Google")
        mock_response.assert_not_called()

    def test_weather_request_uses_conditional_executor(self):
        """Weather requests should use the tool-routing path."""

        with patch(
            "main.respond_to_user",
            return_value="Normal response",
        ) as mock_response, patch(
            "main.execute_conditional_task",
            return_value="Weather action handled",
        ) as mock_executor:
            self.run_main_with_input(
                ["Get the weather in Chennai", "exit"]
            )

        mock_executor.assert_called_once_with(
            "Get the weather in Chennai"
        )
        mock_response.assert_not_called()

    def test_none_from_executor_falls_back_to_normal_response(self):
        """An executor returning None should trigger a fallback."""

        with patch(
            "main.respond_to_user",
            return_value="Fallback response",
        ) as mock_response, patch(
            "main.execute_conditional_task",
            return_value=None,
        ) as mock_executor:
            self.run_main_with_input(["Open Google", "exit"])

        mock_executor.assert_called_once_with("Open Google")
        mock_response.assert_called_once_with("Open Google")

    def test_empty_input_is_ignored(self):
        """Empty input should not trigger either response path."""

        with patch(
            "main.respond_to_user",
        ) as mock_response, patch(
            "main.execute_conditional_task",
        ) as mock_executor:
            self.run_main_with_input(["", "   ", "exit"])

        mock_response.assert_not_called()
        mock_executor.assert_not_called()

    def test_exit_stops_without_processing_a_message(self):
        """Typing exit should stop the loop immediately."""

        with patch(
            "main.respond_to_user",
        ) as mock_response, patch(
            "main.execute_conditional_task",
        ) as mock_executor:
            output = self.run_main_with_input(["exit"])

        self.assertIn("Goodbye", output)
        mock_response.assert_not_called()
        mock_executor.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
