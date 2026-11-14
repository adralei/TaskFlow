
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from approval_records import (
    create_approval_record,
    validate_approval_pair,
)


PACKET_HASH = "a" * 64


class TestApprovalRecords(unittest.TestCase):

    def setUp(self):
        self.customer = create_approval_record(
            "CUSTOMER",
            "customer-001",
            "TCK-001",
            "packet-001",
            PACKET_HASH,
        )

        self.operator = create_approval_record(
            "OPERATOR",
            "operator-001",
            "TCK-001",
            "packet-001",
            PACKET_HASH,
        )

    def validate(self, customer=None, operator=None):
        return validate_approval_pair(
            customer if customer is not None else self.customer,
            operator if operator is not None else self.operator,
            ticket_id="TCK-001",
            packet_id="packet-001",
            packet_sha256=PACKET_HASH,
        )

    def test_valid_approval_pair(self):
        result = self.validate()

        self.assertEqual(
            result,
            {
                "valid": True,
                "reason": "APPROVALS_VERIFIED"
            }
        )

    def test_wrong_ticket_rejected(self):
        changed = {
            **self.customer,
            "ticket_id": "TCK-002"
        }

        result = self.validate(customer=changed)

        self.assertEqual(
            result["reason"],
            "APPROVAL_CONTEXT_MISMATCH"
        )

    def test_wrong_packet_rejected(self):
        changed = {
            **self.operator,
            "packet_id": "packet-002"
        }

        result = self.validate(operator=changed)

        self.assertEqual(
            result["reason"],
            "APPROVAL_CONTEXT_MISMATCH"
        )

    def test_wrong_hash_rejected(self):
        changed = {
            **self.customer,
            "packet_sha256": "b" * 64
        }

        result = self.validate(customer=changed)

        self.assertEqual(
            result["reason"],
            "APPROVAL_CONTEXT_MISMATCH"
        )

    def test_same_actor_rejected(self):
        changed = {
            **self.operator,
            "actor_id": "customer-001"
        }

        result = self.validate(operator=changed)

        self.assertEqual(
            result["reason"],
            "SAME_ACTOR"
        )

    def test_false_approval_rejected(self):
        changed = {
            **self.customer,
            "approved": False
        }

        result = self.validate(customer=changed)

        self.assertEqual(
            result["reason"],
            "INVALID_APPROVAL_RECORD"
        )

    def test_swapped_approval_types_rejected(self):
        result = self.validate(
            customer=self.operator,
            operator=self.customer,
        )

        self.assertEqual(
            result["reason"],
            "APPROVAL_TYPE_MISMATCH"
        )


if __name__ == "__main__":
    unittest.main()
