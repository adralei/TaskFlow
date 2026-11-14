
import sys
import unittest
from copy import deepcopy
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from decision_binding import build_bound_decision
from resolution_gate import evaluate_resolution_eligibility


PACKET = {
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
            "citations": [
                {
                    "chunk_id": "invitations:2",
                    "source": "invitations.md",
                    "content": "Invitations disabled at member limit.",
                }
            ]
        }
    ],
}


CLAIM_REQUEST = {
    "claim": "Member limit blocks invitations.",
    "evidence_type": "BOTH",
    "account_fields": ["member_limit_reached"],
    "document_ids": ["invitations:2"],
}


class TestResolutionGate(unittest.TestCase):

    def setUp(self):
        self.packet = deepcopy(PACKET)
        self.claim_request = deepcopy(CLAIM_REQUEST)

        # This is synthetic test data.
        # It is NOT an actual human approval.
        self.event = build_bound_decision(
            self.claim_request,
            self.packet,
            "packet-001",
            {
                "verdict": "SUPPORTED",
                "reason": "Synthetic review for unit testing.",
            },
            reviewer_id="test-reviewer",
        )

    def evaluate(self, **overrides):
        arguments = {
            "event": self.event,
            "claim_request": self.claim_request,
            "packet": self.packet,
            "packet_id": "packet-001",
            "customer_confirmed": True,
            "operator_approved": True,
        }

        arguments.update(overrides)

        return evaluate_resolution_eligibility(
            **arguments
        )

    def test_all_preconditions_met(self):
        result = self.evaluate()

        self.assertEqual(
            result["reason"],
            "PRECONDITIONS_MET"
        )
        self.assertTrue(result["eligible"])
        self.assertFalse(result["ticket_updated"])

    def test_unsupported_review_blocked(self):
        event = build_bound_decision(
            self.claim_request,
            self.packet,
            "packet-001",
            {
                "verdict": "UNSUPPORTED",
                "reason": "Synthetic unsupported claim.",
            },
            reviewer_id="test-reviewer",
        )

        result = self.evaluate(event=event)

        self.assertFalse(result["eligible"])
        self.assertEqual(
            result["reason"],
            "REVIEW_NOT_SUPPORTED"
        )

    def test_customer_confirmation_required(self):
        result = self.evaluate(
            customer_confirmed=False
        )

        self.assertEqual(
            result["reason"],
            "CUSTOMER_CONFIRMATION_REQUIRED"
        )

    def test_operator_approval_required(self):
        result = self.evaluate(
            operator_approved=False
        )

        self.assertEqual(
            result["reason"],
            "OPERATOR_APPROVAL_REQUIRED"
        )

    def test_invalid_approval_input_rejected(self):
        result = self.evaluate(
            customer_confirmed="true"
        )

        self.assertEqual(
            result["reason"],
            "INVALID_APPROVAL_INPUT"
        )

    def test_changed_packet_blocked(self):
        updated = deepcopy(self.packet)
        updated["account_evidence"]["member_count"] = 4

        result = self.evaluate(packet=updated)

        self.assertEqual(
            result["reason"],
            "DECISION_VERIFICATION_FAILED"
        )

    def test_different_ticket_blocked(self):
        updated = deepcopy(self.packet)
        updated["account_evidence"]["ticket_id"] = "TCK-002"

        result = self.evaluate(packet=updated)

        self.assertEqual(
            result["reason"],
            "DECISION_VERIFICATION_FAILED"
        )

    def test_ticket_not_open(self):
        packet = deepcopy(self.packet)
        packet["account_evidence"]["status"] = "resolved"

        # Bind the event to the same resolved packet
        # to isolate the ticket-status condition.
        event = build_bound_decision(
            self.claim_request,
            packet,
            "packet-001",
            {
                "verdict": "SUPPORTED",
                "reason": "Synthetic review for testing.",
            },
            reviewer_id="test-reviewer",
        )

        result = self.evaluate(
            packet=packet,
            event=event
        )

        self.assertEqual(
            result["reason"],
            "TICKET_NOT_OPEN"
        )


if __name__ == "__main__":
    unittest.main()
