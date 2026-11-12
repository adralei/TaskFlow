
"""Tests for claim evidence selection and validation."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from claim_evidence import prepare_claim_review


PACKET = {
    "review_status": "PENDING_MANUAL_REVIEW",
    "citation_audit": {
        "references_valid": True
    },
    "account_evidence": {
        "member_count": 5,
        "max_members": 5
    },
    "cited_lines_for_review": [
        {
            "citations": [
                {
                    "chunk_id": "invitations:2",
                    "source": "invitations.md",
                    "content": "Disabled at member limit."
                }
            ]
        }
    ]
}


class TestClaimEvidence(unittest.TestCase):

    def test_account_evidence(self):
        result = prepare_claim_review({
            "claim": "Limit is 5/5.",
            "evidence_type": "ACCOUNT",
            "account_fields": [
                "member_count",
                "max_members"
            ]
        }, PACKET)

        self.assertTrue(result["success"])
        self.assertEqual(
            result["data"]["evidence"][0]["value"],
            5
        )
        self.assertEqual(
            result["data"]["review_verdict"],
            "NOT_REVIEWED"
        )

    def test_document_evidence(self):
        result = prepare_claim_review({
            "claim": "Invite button disabled.",
            "evidence_type": "DOCUMENT",
            "document_ids": ["invitations:2"]
        }, PACKET)

        self.assertTrue(result["success"])
        self.assertEqual(
            result["data"]["evidence"][0]["chunk_id"],
            "invitations:2"
        )

    def test_missing_account_field(self):
        result = prepare_claim_review({
            "claim": "Account role.",
            "evidence_type": "ACCOUNT",
            "account_fields": ["role"]
        }, PACKET)

        self.assertEqual(
            result["error"],
            "EVIDENCE_NOT_FOUND"
        )

    def test_unretrieved_document(self):
        result = prepare_claim_review({
            "claim": "Free supports 5.",
            "evidence_type": "DOCUMENT",
            "document_ids": ["plans:1"]
        }, PACKET)

        self.assertEqual(
            result["error"],
            "EVIDENCE_NOT_FOUND"
        )

    def test_mixed_evidence_rejected(self):
        result = prepare_claim_review({
            "claim": "Mixed evidence.",
            "evidence_type": "ACCOUNT",
            "account_fields": ["member_count"],
            "document_ids": ["invitations:2"]
        }, PACKET)

        self.assertEqual(
            result["error"],
            "INVALID_INPUT"
        )

    def test_invalid_packet_rejected(self):
        invalid_packet = {
            **PACKET,
            "citation_audit": {
                "references_valid": False
            }
        }

        result = prepare_claim_review({
            "claim": "Account limit.",
            "evidence_type": "ACCOUNT",
            "account_fields": ["member_count"]
        }, invalid_packet)

        self.assertEqual(
            result["error"],
            "INVALID_PACKET"
        )

    def test_blank_claim_rejected(self):
        result = prepare_claim_review({
            "claim": "   ",
            "evidence_type": "ACCOUNT",
            "account_fields": ["member_count"]
        }, PACKET)

        self.assertEqual(
            result["error"],
            "INVALID_INPUT"
        )


    def test_both_evidence_success(self):
        packet = {
            **PACKET,
            "account_evidence": {
                **PACKET["account_evidence"],
                "member_limit_reached": True
            }
        }

        result = prepare_claim_review({
            "claim": "Limit reached, invitations blocked.",
            "evidence_type": "BOTH",
            "account_fields": [
                "member_limit_reached"
            ],
            "document_ids": [
                "invitations:2"
            ]
        }, packet)

        self.assertTrue(result["success"])

        kinds = [
            item["kind"]
            for item in result["data"]["evidence"]
        ]

        self.assertEqual(
            kinds,
            ["ACCOUNT", "DOCUMENT"]
        )

        self.assertEqual(
            result["data"]["review_verdict"],
            "NOT_REVIEWED"
        )

    def test_both_requires_account_fields(self):
        result = prepare_claim_review({
            "claim": "Missing account evidence.",
            "evidence_type": "BOTH",
            "document_ids": ["invitations:2"]
        }, PACKET)

        self.assertEqual(
            result["error"],
            "INVALID_INPUT"
        )

    def test_both_requires_document_ids(self):
        result = prepare_claim_review({
            "claim": "Missing document evidence.",
            "evidence_type": "BOTH",
            "account_fields": ["member_count"]
        }, PACKET)

        self.assertEqual(
            result["error"],
            "INVALID_INPUT"
        )

    def test_both_rejects_unretrieved_document(self):
        result = prepare_claim_review({
            "claim": "Unsupported combined claim.",
            "evidence_type": "BOTH",
            "account_fields": ["member_count"],
            "document_ids": ["plans:999"]
        }, PACKET)

        self.assertFalse(result["success"])

        self.assertEqual(
            result["error"],
            "EVIDENCE_NOT_FOUND"
        )



if __name__ == "__main__":
    unittest.main()
