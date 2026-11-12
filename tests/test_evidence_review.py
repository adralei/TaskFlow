
import json
import sys
import tempfile
import unittest

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from evidence_review import (
    build_review_markdown,
    generate_latest_review,
)


def make_packet():
    return {
        "review_status": "PENDING_MANUAL_REVIEW",
        "citation_audit": {
            "references_valid": True
        },
        "account_evidence": {
            "ticket_id": "TCK-001",
            "status": "open",
            "member_count": 5,
            "max_members": 5,
            "member_limit_reached": True,
        },
        "cited_lines_for_review": [
            {
                "text": "The invite button is disabled [invitations:2].",
                "citations": [
                    {
                        "chunk_id": "invitations:2",
                        "source": "invitations.md",
                        "content": "Disabled at member limit.",
                    }
                ],
                "manual_verdict": "NOT_REVIEWED",
            }
        ],
        "uncited_lines_for_review": [
            "Ticket TCK-001 is open."
        ],
    }


class TestEvidenceReview(unittest.TestCase):

    def test_account_and_document_sections(self):
        markdown = build_review_markdown(
            make_packet()
        )

        self.assertIn(
            "## 1. Account Evidence",
            markdown
        )
        self.assertIn(
            "**member_count:** `5`",
            markdown
        )
        self.assertIn(
            "## 2. Document Evidence",
            markdown
        )
        self.assertIn(
            "Disabled at member limit.",
            markdown
        )

    def test_uncited_line_is_preserved(self):
        markdown = build_review_markdown(
            make_packet()
        )

        self.assertIn(
            "Ticket TCK-001 is open.",
            markdown
        )
        self.assertIn(
            "Supported by Account Evidence",
            markdown
        )

    def test_invalid_citation_audit_rejected(self):
        packet = make_packet()
        packet["citation_audit"]["references_valid"] = False

        with self.assertRaises(ValueError):
            build_review_markdown(packet)

    def test_existing_review_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            artifacts = root / "artifacts"
            artifacts.mkdir()

            packet_path = (
                artifacts
                / "grounding-review-20261111T120000Z.json"
            )

            packet_path.write_text(
                json.dumps(make_packet()),
                encoding="utf-8"
            )

            _, review_path, created = (
                generate_latest_review(root)
            )

            self.assertTrue(created)
            self.assertTrue(review_path.exists())

            review_path.write_text(
                "My manual review",
                encoding="utf-8"
            )

            _, _, created_again = (
                generate_latest_review(root)
            )

            self.assertFalse(created_again)
            self.assertEqual(
                review_path.read_text(encoding="utf-8"),
                "My manual review"
            )


if __name__ == "__main__":
    unittest.main()
