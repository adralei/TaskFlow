
import json
import sys
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from review_decision import (
    build_review_decision,
    save_review_decision,
)


CLAIM_REVIEW = {
    "claim": "Member limit reached.",
    "evidence_type": "ACCOUNT",
    "evidence": [
        {
            "kind": "ACCOUNT",
            "field": "member_limit_reached",
            "value": True
        }
    ],
    "review_verdict": "NOT_REVIEWED"
}


def make_decision(verdict="SUPPORTED"):
    return {
        "verdict": verdict,
        "reason": "Evidence reviewed for this test."
    }


class TestReviewDecision(unittest.TestCase):

    def test_valid_decision(self):
        event = build_review_decision(
            CLAIM_REVIEW,
            make_decision(),
            "reviewer-001"
        )

        self.assertEqual(
            event["verdict"],
            "SUPPORTED"
        )
        self.assertEqual(
            event["reviewer_id"],
            "reviewer-001"
        )
        self.assertEqual(
            len(event["evidence_sha256"]),
            64
        )

    def test_not_reviewed_cannot_be_submitted(self):
        with self.assertRaises(ValidationError):
            build_review_decision(
                CLAIM_REVIEW,
                make_decision("NOT_REVIEWED"),
                "reviewer-001"
            )

    def test_missing_reason_rejected(self):
        with self.assertRaises(ValidationError):
            build_review_decision(
                CLAIM_REVIEW,
                {
                    "verdict": "UNSUPPORTED",
                    "reason": " "
                },
                "reviewer-001"
            )

    def test_missing_reviewer_rejected(self):
        with self.assertRaises(ValueError):
            build_review_decision(
                CLAIM_REVIEW,
                make_decision(),
                ""
            )

    def test_decision_saved_without_overwrite(self):
        event = build_review_decision(
            CLAIM_REVIEW,
            make_decision("NEEDS_MORE_EVIDENCE"),
            "reviewer-001"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            path = save_review_decision(
                event,
                root
            )

            saved = json.loads(
                path.read_text(encoding="utf-8")
            )

            self.assertEqual(
                saved["event_id"],
                event["event_id"]
            )

            with self.assertRaises(FileExistsError):
                save_review_decision(
                    event,
                    root
                )


if __name__ == "__main__":
    unittest.main()
