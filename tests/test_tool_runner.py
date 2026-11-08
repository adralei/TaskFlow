
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tool_runner import safe_run_investigation


class TestSafeToolRunner(unittest.TestCase):

    def test_valid_request(self):
        response = safe_run_investigation(
            {"ticket_id": "TCK-001"},
            "tenant-001"
        )

        self.assertTrue(response.success)
        self.assertIsNone(response.error)
        self.assertEqual(
            response.data["ticket_id"],
            "TCK-001"
        )

    def test_unauthorized_request(self):
        response = safe_run_investigation(
            {"ticket_id": "TCK-001"},
            "tenant-002"
        )

        self.assertFalse(response.success)
        self.assertEqual(
            response.error,
            "ACCESS_DENIED"
        )
        self.assertIsNone(response.data)

    def test_invalid_input(self):
        response = safe_run_investigation(
            {"ticket_id": 123},
            "tenant-001"
        )

        self.assertFalse(response.success)
        self.assertEqual(
            response.error,
            "INVALID_INPUT"
        )

    def test_extra_field_rejected(self):
        response = safe_run_investigation(
            {
                "ticket_id": "TCK-001",
                "tenant_id": "tenant-002"
            },
            "tenant-001"
        )

        self.assertFalse(response.success)
        self.assertEqual(
            response.error,
            "INVALID_INPUT"
        )

    def test_ticket_not_found(self):
        response = safe_run_investigation(
            {"ticket_id": "TCK-999"},
            "tenant-001"
        )

        self.assertFalse(response.success)
        self.assertEqual(
            response.error,
            "TICKET_NOT_FOUND"
        )

    def test_invalid_tool_output(self):
        with patch(
            "tool_runner.run_investigation",
            side_effect=ValidationError.from_exception_data(
                "InvestigationResult",
                [
                    {
                        "type": "missing",
                        "loc": ("ticket_id",),
                        "input": {}
                    }
                ]
            )
        ):
            response = safe_run_investigation(
                {"ticket_id": "TCK-001"},
                "tenant-001"
            )

        self.assertFalse(response.success)
        self.assertEqual(
            response.error,
            "INVALID_TOOL_OUTPUT"
        )

    def test_data_access_error(self):
        with patch(
            "tool_runner.run_investigation",
            side_effect=OSError("File unavailable")
        ):
            response = safe_run_investigation(
                {"ticket_id": "TCK-001"},
                "tenant-001"
            )

        self.assertFalse(response.success)
        self.assertEqual(
            response.error,
            "DATA_ACCESS_ERROR"
        )

    def test_unexpected_error(self):
        with patch(
            "tool_runner.run_investigation",
            side_effect=RuntimeError("Unexpected failure")
        ):
            response = safe_run_investigation(
                {"ticket_id": "TCK-001"},
                "tenant-001"
            )

        self.assertFalse(response.success)
        self.assertEqual(
            response.error,
            "INTERNAL_ERROR"
        )


if __name__ == "__main__":
    unittest.main()
