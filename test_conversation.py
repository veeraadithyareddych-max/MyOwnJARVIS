
import unittest
from unittest.mock import patch

import main


class ConversationContextTests(unittest.TestCase):
    """Tests for JARVIS short-term conversation context."""

    def setUp(self):
        self.original_history = main.SESSION_CONVERSATION_HISTORY.copy()
        self.original_last_successful_action = main.LAST_SUCCESSFUL_ACTION
        main.SESSION_CONVERSATION_HISTORY.clear()

    def tearDown(self):
        main.SESSION_CONVERSATION_HISTORY.clear()
        main.SESSION_CONVERSATION_HISTORY.extend(self.original_history)
        main.LAST_SUCCESSFUL_ACTION = self.original_last_successful_action

    def test_empty_history_builds_prompt(self):
        prompt = main.build_conversation_prompt(
            "Tell me about Java."
        )

        self.assertIn("This is the start of the conversation.", prompt)
        self.assertIn("Tell me about Java.", prompt)

    def test_last_successful_action_starts_empty(self):
        """A new conversation must not have a previous executable action."""

        self.assertIsNone(main.LAST_SUCCESSFUL_ACTION)

    def test_last_successful_action_can_be_stored(self):
        """A successful executable action can be stored for follow-up requests."""

        main.LAST_SUCCESSFUL_ACTION = {
            "tool": "open_website",
            "arguments": {
                "site_name": "youtube",
            },
        }

        self.assertEqual(
            main.LAST_SUCCESSFUL_ACTION["tool"],
            "open_website",
        )
        self.assertEqual(
            main.LAST_SUCCESSFUL_ACTION["arguments"]["site_name"],
            "youtube",
        )

    def test_resolve_it_uses_last_successful_action(self):
        """The word 'it' should resolve to the last successful website action."""

        main.LAST_SUCCESSFUL_ACTION = {
            "tool": "open_website",
            "arguments": {
                "site_name": "youtube",
            },
        }

        resolved = main.resolve_conversational_reference(
            "Open it again."
        )

        self.assertEqual(
            resolved,
            "Open YouTube again.",
        )

    def test_resolve_that_uses_last_successful_action(self):
        """The word 'that' should resolve to the last successful website action."""

        main.LAST_SUCCESSFUL_ACTION = {
            "tool": "open_website",
            "arguments": {
                "site_name": "youtube",
            },
        }

        resolved = main.resolve_conversational_reference(
            "Open that again."
        )

        self.assertEqual(
            resolved,
            "Open YouTube again.",
        )

    def test_resolve_it_uses_last_successful_application_action(self):
        """The word 'it' should resolve to the last successful application action."""

        main.LAST_SUCCESSFUL_ACTION = {
            "tool": "open_application",
            "arguments": {
                "app_name": "notepad",
            },
        }

        resolved = main.resolve_conversational_reference(
            "Open it again."
        )

        self.assertEqual(
            resolved,
            "Open Notepad again.",
        )

    def test_resolve_the_website_uses_last_successful_action(self):
        """'the website' should resolve to the last successful website action."""

        main.LAST_SUCCESSFUL_ACTION = {
            "tool": "open_website",
            "arguments": {
                "site_name": "youtube",
            },
        }

        resolved = main.resolve_conversational_reference(
            "Open the website again."
        )

        self.assertEqual(
            resolved,
            "Open YouTube again.",
        )

    def test_resolve_does_not_replace_it_inside_other_words(self):
        """Only the standalone word 'it' should be replaced."""

        main.LAST_SUCCESSFUL_ACTION = {
            "tool": "open_website",
            "arguments": {
                "site_name": "youtube",
            },
        }

        resolved = main.resolve_conversational_reference(
            "Visit it again."
        )

        self.assertEqual(
            resolved,
            "Visit YouTube again.",
        )

    def test_resolve_it_does_not_use_failed_or_missing_action(self):
        """An unavailable previous action must not invent a reference."""

        main.LAST_SUCCESSFUL_ACTION = None

        resolved = main.resolve_conversational_reference(
            "Open it again."
        )

        self.assertEqual(
            resolved,
            "Open it again.",
        )

    def test_record_successful_action_stores_tool_and_arguments(self):
        """A successful tool result should become the last successful action."""

        main.LAST_SUCCESSFUL_ACTION = None

        main.record_successful_action(
            "open_website",
            {"site_name": "youtube"},
            {
                "success": True,
                "tool": "open_website",
                "data": "YouTube opened.",
                "status": "accepted",
            },
        )

        self.assertEqual(
            main.LAST_SUCCESSFUL_ACTION,
            {
                "tool": "open_website",
                "arguments": {
                    "site_name": "youtube",
                },
            },
        )


    def test_record_successful_action_ignores_failed_result(self):
        """A failed tool result must not become the last successful action."""

        main.LAST_SUCCESSFUL_ACTION = None

        main.record_successful_action(
            "open_website",
            {"site_name": "youtube"},
            {
                "success": False,
                "tool": "open_website",
                "error": "Website failed to open.",
                "status": "failed",
            },
        )

        self.assertIsNone(main.LAST_SUCCESSFUL_ACTION)

    def test_recent_conversation_is_included(self):
        main.SESSION_CONVERSATION_HISTORY.extend([
            ("Tell me about Java inheritance.",
             "Inheritance lets a class reuse another class's behavior."),
        ])

        prompt = main.build_conversation_prompt(
            "Explain that again."
        )

        self.assertIn("Tell me about Java inheritance.", prompt)
        self.assertIn("Inheritance lets a class reuse", prompt)
        self.assertIn("Explain that again.", prompt)

    def test_multiple_turns_keep_their_order(self):
        main.SESSION_CONVERSATION_HISTORY.extend([
            ("Tell me about Java.", "Java is a programming language."),
            ("What is a class?", "A class is a blueprint for objects."),
        ])

        prompt = main.build_conversation_prompt(
            "Give me an example."
        )

        first = prompt.index("Tell me about Java.")
        second = prompt.index("What is a class?")

        self.assertLess(first, second)

    def test_history_is_limited_to_recent_turns(self):
        for number in range(main.MAX_CONVERSATION_TURNS + 2):
            main.SESSION_CONVERSATION_HISTORY.append(
                (f"User message {number}", f"Assistant reply {number}")
            )

        prompt = main.build_conversation_prompt("Continue.")

        self.assertNotIn("User message 0", prompt)
        self.assertNotIn("Assistant reply 0", prompt)
        self.assertIn(
            f"User message {main.MAX_CONVERSATION_TURNS + 1}",
            prompt,
        )

    def test_base_prompt_is_preserved(self):
        memory_prompt = (
            "Current question: What language do I prefer?\n"
            "Relevant memory: programming_language: Java"
        )

        prompt = main.build_conversation_prompt(
            "What language do I prefer?",
            memory_prompt,
        )

        self.assertIn("Relevant memory: programming_language: Java", prompt)

    @patch("main.ask_local_ai")
    def test_general_question_uses_conversation_prompt(self, mock_ai):
        mock_ai.return_value = "Java inheritance allows class reuse."

        main.SESSION_CONVERSATION_HISTORY.append(
            ("Tell me about Java inheritance.", "Inheritance allows class reuse.")
        )

        response = main.respond_to_user("Explain that again.")

        self.assertEqual(
            response,
            "Java inheritance allows class reuse.",
        )
        mock_ai.assert_called_once()

        submitted_prompt = mock_ai.call_args.args[0]
        self.assertIn("Tell me about Java inheritance.", submitted_prompt)
        self.assertIn("Explain that again.", submitted_prompt)


if __name__ == "__main__":
    unittest.main()
