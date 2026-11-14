
import sys
import unittest
from copy import deepcopy
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from decision_binding import (
    build_bound_decision,
    verify_bound_decision,
)


PACKET = {
    "review_status": "PENDING_MANUAL_REVIEW",
    "citation_audit": {
        "references_valid": True
    },
    "account_evidence": {
        "ticket_id": "TCK-001",
        "member_count": 5,
        "max_members": 5,
        "member_limit_reached": True,
    },
    "cited_lines_for_review": [
        {
            "citations": [
                {
                    "chunk_id": "invitations:2",
                    "source": "invitations.md",
                    "content": "Invitations disabled at limit.",
                }
            ]
        }
    ]
}

CLAIM_REQUEST = {
    "claim": "Member limit blocks invitations.",
    "evidence_type": "BOTH",
    "account_fields": [
        "member_limit_reached"
    ],
    "document_ids": [
        "invitations:2"
    ]
}


class TestDecisionBinding(unittest.TestCase):

    def setUp(self):
        self.packet = deepcopy(PACKET)
        self.claim_request = deepcopy(CLAIM_REQUEST)

        self.event = build_bound_decision(
            self.claim_request,
            self.packet,
            "packet-001",
            {
                "verdict": "NEEDS_MORE_EVIDENCE",
                "reason": "Synthetic review decision."
            },
            "test-reviewer"
        )

    def test_matching_context(self):
        result = verify_bound_decision(
            self.event,
            self.claim_request,
            self.packet,
            "packet-001"
        )

        self.assertEqual(
            result,
            {"matches": True, "reason": "MATCH"}
        )

    def test_different_packet_id_rejected(self):
        result = verify_bound_decision(
            self.event,
            self.claim_request,
            self.packet,
            "packet-002"
        )

        self.assertEqual(
            result["reason"],
            "PACKET_ID_MISMATCH"
        )

    def test_different_ticket_rejected(self):
        updated = deepcopy(self.packet)

        updated["account_evidence"]["ticket_id"] = "TCK-002"

        result = verify_bound_decision(
            self.event,
            self.claim_request,
            updated,
            "packet-001"
        )

        self.assertEqual(
            result["reason"],
            "TICKET_MISMATCH"
        )

    def test_changed_packet_rejected(self):
        updated = deepcopy(self.packet)

        updated["account_evidence"]["member_count"] = 4

        result = verify_bound_decision(
            self.event,
            self.claim_request,
            updated,
            "packet-001"
        )

        self.assertEqual(
            result["reason"],
            "PACKET_CHANGED"
        )

    def test_changed_claim_evidence_rejected(self):
        updated_request = deepcopy(self.claim_request)

        updated_request["account_fields"] = [
            "member_count"
        ]

        result = verify_bound_decision(
            self.event,
            updated_request,
            self.packet,
            "packet-001"
        )

        self.assertEqual(
            result["reason"],
            "EVIDENCE_CHANGED"
        )

    def test_missing_binding_rejected(self):
        unbound_event = deepcopy(self.event)
        del unbound_event["packet_id"]

        result = verify_bound_decision(
            unbound_event,
            self.claim_request,
            self.packet,
            "packet-001"
        )

        self.assertEqual(
            result["reason"],
            "INVALID_EVENT"
        )


if __name__ == "__main__":
    unittest.main()
