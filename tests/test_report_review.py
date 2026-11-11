
import json
import sys
import tempfile
import unittest

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from report_review import (
    build_review_packet,
    save_review_packet,
)


HITS = [
    {
        "chunk_id": "plans:3",
        "source": "plans.md",
        "content": "Member limits depend on the plan.",
    },
    {
        "chunk_id": "invitations:2",
        "source": "invitations.md",
        "content": "The invite button is disabled at the limit.",
    },
]

ACCOUNT = {
    "ticket_id": "TCK-001",
    "status": "open",
    "priority": "unknown",
    "workspace": "Acme Workspace",
    "plan": "Free",
    "member_count": 5,
    "max_members": 5,
    "member_limit_reached": True,
}


class TestReportReview(unittest.TestCase):

    def test_multiple_sources_attached(self):
        packet = build_review_packet(
            "Limit reached [plans:3, invitations:2].",
            HITS,
            ACCOUNT,
        )

        line = packet["cited_lines_for_review"][0]

        self.assertEqual(
            [c["chunk_id"] for c in line["citations"]],
            ["plans:3", "invitations:2"]
        )

        self.assertEqual(
            packet["review_status"],
            "PENDING_MANUAL_REVIEW"
        )

    def test_unknown_citation_blocked(self):
        with self.assertRaises(ValueError):
            build_review_packet(
                "Unknown rule [plans:999].",
                HITS,
                ACCOUNT,
            )

    def test_uncited_lines_preserved(self):
        packet = build_review_packet(
            "Ticket remains open.\n"
            "Plan rule [plans:3].",
            HITS,
            ACCOUNT,
        )

        self.assertEqual(
            packet["uncited_lines_for_review"],
            ["Ticket remains open."]
        )

    def test_packet_saved_as_json(self):
        packet = build_review_packet(
            "Plan rule [plans:3].",
            HITS,
            ACCOUNT,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = save_review_packet(
                packet,
                Path(temp_dir)
            )

            saved = json.loads(
                path.read_text(encoding="utf-8")
            )

            self.assertTrue(path.exists())
            self.assertEqual(
                saved["account_evidence"]["member_count"],
                5
            )


if __name__ == "__main__":
    unittest.main()
