
import sys
import unittest
from copy import deepcopy
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from review_decision import build_review_decision
from decision_verification import (
    verify_decision_against_review
)


REVIEW = {
    "claim": "Member limit reached.",
    "evidence_type": "ACCOUNT",
    "evidence": [
        {
            "kind": "ACCOUNT",
            "field": "member_count",
            "value": 5
        }
    ],
    "review_verdict": "NOT_REVIEWED"
}


class TestDecisionVerification(unittest.TestCase):

    def setUp(self):
        self.review = deepcopy(REVIEW)

        self.event = build_review_decision(
            self.review,
            {
                "verdict": "NEEDS_MORE_EVIDENCE",
                "reason": "Synthetic test decision."
            },
            "test-reviewer"
        )

    def test_unchanged_evidence_matches(self):
        result = verify_decision_against_review(
            self.event,
            self.review
        )

        self.assertEqual(
            result,
            {"matches": True, "reason": "MATCH"}
        )

    def test_changed_evidence_detected(self):
        updated = deepcopy(self.review)

        updated["evidence"][0]["value"] = 4

        result = verify_decision_against_review(
            self.event,
            updated
        )

        self.assertEqual(
            result["reason"],
            "EVIDENCE_CHANGED"
        )
        self.assertFalse(result["matches"])

    def test_changed_claim_detected(self):
        updated = deepcopy(self.review)
        updated["claim"] = "Different claim."

        result = verify_decision_against_review(
            self.event,
            updated
        )

        self.assertEqual(
            result["reason"],
            "CLAIM_CHANGED"
        )

    def test_changed_evidence_type_detected(self):
        updated = deepcopy(self.review)
        updated["evidence_type"] = "DOCUMENT"

        result = verify_decision_against_review(
            self.event,
            updated
        )

        self.assertEqual(
            result["reason"],
            "EVIDENCE_TYPE_CHANGED"
        )

    def test_invalid_event_rejected(self):
        invalid_event = {
            **self.event,
            "evidence_sha256": "not-a-real-hash"
        }

        result = verify_decision_against_review(
            invalid_event,
            self.review
        )

        self.assertEqual(
            result["reason"],
            "INVALID_EVENT"
        )

    def test_invalid_current_review_rejected(self):
        invalid_review = {
            **self.review,
            "evidence": []
        }

        result = verify_decision_against_review(
            self.event,
            invalid_review
        )

        self.assertEqual(
            result["reason"],
            "INVALID_REVIEW"
        )


if __name__ == "__main__":
    unittest.main()
