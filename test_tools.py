
import unittest
from unittest.mock import MagicMock, patch

import agent
import tools


class ToolExecutionTests(unittest.TestCase):

    # ========================================================
    # APPLICATION AND WEBSITE TESTS
    # ========================================================

    @patch("tools.subprocess.Popen")
    def test_notepad_launch_is_accepted(self, mock_popen):
        result = tools.open_application("Notepad")

        mock_popen.assert_called_once_with(["notepad.exe"])
        self.assertTrue(result["success"])
        self.assertEqual(result["tool"], "open_application")

    def test_unsupported_application_is_rejected(self):
        result = tools.open_application("UnknownApp")

        self.assertFalse(result["success"])
        self.assertEqual(result["tool"], "open_application")

    @patch("tools.subprocess.Popen", side_effect=OSError("Launch failed"))
    def test_application_launch_error_is_reported(self, mock_popen):
        result = tools.open_application("notepad")

        self.assertFalse(result["success"])
        self.assertIn("Could not open", result["error"])

    @patch("tools.webbrowser.open", return_value=True)
    def test_google_open_is_accepted(self, mock_open):
        result = tools.open_website("Google")

        mock_open.assert_called_once_with("https://www.google.com")
        self.assertTrue(result["success"])
        self.assertEqual(result["tool"], "open_website")

    @patch("tools.webbrowser.open", return_value=False)
    def test_browser_failure_is_reported(self, mock_open):
        result = tools.open_website("YouTube")

        self.assertFalse(result["success"])
        self.assertIn("did not confirm", result["error"])

    def test_unsupported_website_is_rejected(self):
        result = tools.open_website("UnknownWebsite")

        self.assertFalse(result["success"])
        self.assertEqual(result["tool"], "open_website")

    # ========================================================
    # TOOL RESULT VALIDATION TESTS
    # ========================================================

    def test_rejects_non_boolean_success_flag(self):
        fake_result = {
            "success": "true",
            "tool": "fake_tool",
            "data": "Completed",
        }

        with patch.dict(
            agent.TOOL_REGISTRY,
            {"fake_tool": lambda: fake_result},
        ):
            result = agent.execute_tool("fake_tool")

        self.assertFalse(result["success"])
        self.assertIn("success flag", result["error"])

    def test_rejects_success_without_data(self):
        fake_result = {
            "success": True,
            "tool": "fake_tool",
            "data": None,
        }

        with patch.dict(
            agent.TOOL_REGISTRY,
            {"fake_tool": lambda: fake_result},
        ):
            result = agent.execute_tool("fake_tool")

        self.assertFalse(result["success"])
        self.assertIn("without result data", result["error"])

    def test_rejects_failure_without_error_message(self):
        fake_result = {
            "success": False,
            "tool": "fake_tool",
            "error": "",
        }

        with patch.dict(
            agent.TOOL_REGISTRY,
            {"fake_tool": lambda: fake_result},
        ):
            result = agent.execute_tool("fake_tool")

        self.assertFalse(result["success"])
        self.assertIn("without providing an error", result["error"])

    def test_rejects_mismatched_tool_name(self):
        fake_result = {
            "success": True,
            "tool": "another_tool",
            "data": "Completed",
        }

        with patch.dict(
            agent.TOOL_REGISTRY,
            {"fake_tool": lambda: fake_result},
        ):
            result = agent.execute_tool("fake_tool")

        self.assertFalse(result["success"])
        self.assertIn("mismatched tool name", result["error"])

    def test_rejects_verified_status_without_verification_evidence(self):
        fake_result = {
            "success": True,
            "tool": "fake_tool",
            "data": "Action requested",
            "status": "verified",
        }

        with patch.dict(
            agent.TOOL_REGISTRY,
            {"fake_tool": lambda: fake_result},
        ):
            result = agent.execute_tool("fake_tool")

        self.assertFalse(result["success"])
        self.assertIn("execution status", result["error"])

    def test_rejects_missing_execution_status(self):
        fake_result = {
            "success": True,
            "tool": "fake_tool",
            "data": "Action requested",
        }

        with patch.dict(
            agent.TOOL_REGISTRY,
            {"fake_tool": lambda: fake_result},
        ):
            result = agent.execute_tool("fake_tool")

        self.assertFalse(result["success"])
        self.assertIn("execution status", result["error"])

    def test_rejects_unknown_execution_status(self):
        fake_result = {
            "success": True,
            "tool": "fake_tool",
            "data": "Action requested",
            "status": "completed",
        }

        with patch.dict(
            agent.TOOL_REGISTRY,
            {"fake_tool": lambda: fake_result},
        ):
            result = agent.execute_tool("fake_tool")

        self.assertFalse(result["success"])
        self.assertIn("execution status", result["error"])

    # ========================================================
    # EXECUTION STATUS TESTS
    # ========================================================

    def test_application_launch_reports_accepted_not_verified(self):
        with patch("tools.subprocess.Popen"):
            result = tools.open_application("Notepad")

        self.assertTrue(result["success"])
        self.assertEqual(result["tool"], "open_application")
        self.assertEqual(result.get("status"), "accepted")

    @patch("tools.webbrowser.open", return_value=True)
    def test_website_open_reports_accepted_not_verified(self, mock_open):
        result = tools.open_website("Google")

        self.assertTrue(result["success"])
        self.assertEqual(result["tool"], "open_website")
        self.assertEqual(result.get("status"), "accepted")

    @patch("tools.subprocess.Popen", side_effect=OSError("Launch failed"))
    def test_failed_application_launch_reports_failed_status(self, mock_popen):
        result = tools.open_application("Notepad")

        self.assertFalse(result["success"])
        self.assertEqual(result["tool"], "open_application")
        self.assertEqual(result.get("status"), "failed")

    # ========================================================
    # STRUCTURED VERIFICATION RESULT TESTS
    # ========================================================

    def test_verification_requires_evidence(self):
        result = agent.make_verification_result(
            True,
            "open_application",
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["evidence"])

    def test_verification_result_accepts_supplied_evidence(self):
        result = agent.make_verification_result(
            True,
            "open_application",
            evidence={
                "check": "Independent application check",
                "observed": "The requested application was detected.",
            },
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "verified")
        self.assertEqual(
            result["evidence"]["check"],
            "Independent application check",
        )
        self.assertEqual(
            result["evidence"]["observed"],
            "The requested application was detected.",
        )

    def test_failed_verification_stays_failed(self):
        result = agent.make_verification_result(
            False,
            "open_application",
            error="The requested condition could not be confirmed.",
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")
        self.assertIsNotNone(result["error"])

    def test_verification_evidence_must_not_be_speculation(self):
        result = agent.make_verification_result(
            True,
            "open_application",
            evidence="The application probably opened.",
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["evidence"])

    # ========================================================
    # INDEPENDENT INTERNET VERIFICATION TESTS
    # ========================================================

    @patch("agent.urllib.request.urlopen")
    def test_internet_verification_confirms_successful_response(
        self,
        mock_urlopen,
    ):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = agent.verify_internet_connection()

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["tool"], "check_internet")
        self.assertIsInstance(result["evidence"], dict)

        self.assertEqual(
            result["evidence"]["check"],
            "Independent HTTP HEAD request",
        )
        self.assertEqual(
            result["evidence"]["observed"],
            "HTTP 200 returned by https://www.google.com",
        )

    @patch("agent.urllib.request.urlopen")
    def test_internet_verification_rejects_server_error(
        self,
        mock_urlopen,
    ):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 500
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = agent.verify_internet_connection()

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["evidence"])
        self.assertIsNotNone(result["error"])

    @patch("agent.urllib.request.urlopen")
    def test_internet_verification_handles_connection_error(
        self,
        mock_urlopen,
    ):
        mock_urlopen.side_effect = OSError("Connection unavailable")

        result = agent.verify_internet_connection()

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")
        self.assertIn("Connection unavailable", result["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
