
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from report_validation import validate_report_references


RETRIEVED_HITS = [
    {"chunk_id": "invitations:2"},
    {"chunk_id": "plans:3"},
]


class TestReportValidation(unittest.TestCase):

    def test_valid_references(self):
        report = (
            "Limit reached [plans:3]. "
            "Button disabled [invitations:2]."
        )

        result = validate_report_references(
            report, RETRIEVED_HITS
        )

        self.assertTrue(result["references_valid"])
        self.assertEqual(result["unknown_ids"], [])

    def test_parentheses_are_detected(self):
        result = validate_report_references(
            "Limit reached (plans:3).",
            RETRIEVED_HITS
        )

        self.assertTrue(result["references_valid"])
        self.assertEqual(
            result["noncanonical_ids"],
            ["plans:3"]
        )

    def test_unknown_reference_rejected(self):
        result = validate_report_references(
            "Unsupported claim [plans:999].",
            RETRIEVED_HITS
        )

        self.assertFalse(result["references_valid"])
        self.assertEqual(
            result["unknown_ids"],
            ["plans:999"]
        )

    def test_unretrieved_reference_rejected(self):
        result = validate_report_references(
            "See [invitations:3].",
            RETRIEVED_HITS
        )

        self.assertFalse(result["references_valid"])

    def test_missing_references_rejected(self):
        result = validate_report_references(
            "The member limit has been reached.",
            RETRIEVED_HITS
        )

        self.assertFalse(result["references_valid"])
        self.assertEqual(result["cited_ids"], [])

    def test_duplicate_references_deduplicated(self):
        result = validate_report_references(
            "Rule [plans:3]. Again [plans:3].",
            RETRIEVED_HITS
        )

        self.assertTrue(result["references_valid"])
        self.assertEqual(
            result["cited_ids"],
            ["plans:3"]
        )


if __name__ == "__main__":
    unittest.main()
