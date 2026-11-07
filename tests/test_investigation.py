
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from investigate_ticket import investigate_ticket


class TestTicketInvestigation(unittest.TestCase):

    def test_authorized_access(self):
        result = investigate_ticket(
            ticket_id="TCK-001",
            session_tenant_id="tenant-001"
        )

        self.assertTrue(result["success"])
        self.assertEqual(
            result["workspace"],
            "Acme Workspace"
        )
        self.assertTrue(result["member_limit_reached"])

    def test_unauthorized_access(self):
        result = investigate_ticket(
            ticket_id="TCK-001",
            session_tenant_id="tenant-002"
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"],
            "ACCESS_DENIED"
        )

        self.assertNotIn("workspace", result)
        self.assertNotIn("member_count", result)

    def test_ticket_not_found(self):
        result = investigate_ticket(
            ticket_id="TCK-999",
            session_tenant_id="tenant-001"
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"],
            "TICKET_NOT_FOUND"
        )

    def test_account_not_found(self):
        fake_ticket = {
            "ticket_id": "TCK-TEST",
            "tenant_id": "tenant-999"
        }

        with patch(
            "investigate_ticket.get_ticket",
            return_value=fake_ticket
        ):
            result = investigate_ticket(
                ticket_id="TCK-TEST",
                session_tenant_id="tenant-999"
            )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"],
            "ACCOUNT_NOT_FOUND"
        )


if __name__ == "__main__":
    unittest.main()
