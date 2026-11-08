
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tool_contract import (
    InvestigationRequest,
    InvestigationResult,
    run_investigation,
)


class TestToolContract(unittest.TestCase):

    def test_valid_request(self):
        result = run_investigation(
            request_data={"ticket_id": "TCK-001"},
            session_tenant_id="tenant-001"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.ticket_id, "TCK-001")
        self.assertTrue(result.member_limit_reached)

    def test_invalid_ticket_id_type(self):
        with self.assertRaises(ValidationError):
            InvestigationRequest.model_validate({
                "ticket_id": 123
            })

    def test_extra_field_rejected(self):
        with self.assertRaises(ValidationError):
            InvestigationRequest.model_validate({
                "ticket_id": "TCK-001",
                "tenant_id": "tenant-002"
            })

    def test_missing_ticket_id(self):
        with self.assertRaises(ValidationError):
            InvestigationRequest.model_validate({})

    def test_invalid_success_type(self):
        with self.assertRaises(ValidationError):
            InvestigationResult.model_validate({
                "success": "yes",
                "error": None
            })

    def test_failure_requires_error(self):
        with self.assertRaises(ValidationError):
            InvestigationResult.model_validate({
                "success": False
            })

    def test_success_cannot_have_error(self):
        with self.assertRaises(ValidationError):
            InvestigationResult.model_validate({
                "success": True,
                "error": "UNKNOWN_ERROR"
            })

    def test_output_extra_field_rejected(self):
        with self.assertRaises(ValidationError):
            InvestigationResult.model_validate({
                "success": True,
                "unexpected": "value"
            })

    def test_unauthorized_result_contract(self):
        result = run_investigation(
            request_data={"ticket_id": "TCK-001"},
            session_tenant_id="tenant-002"
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error, "ACCESS_DENIED")
        self.assertIsNone(result.workspace)

    def test_broken_tool_output_rejected(self):
        with patch(
            "tool_contract.investigate_ticket",
            return_value={
                "success": "yes",
                "error": None
            }
        ):
            with self.assertRaises(ValidationError):
                run_investigation(
                    request_data={"ticket_id": "TCK-001"},
                    session_tenant_id="tenant-001"
                )


    def test_success_requires_complete_data(self):
        with self.assertRaises(ValidationError):
            InvestigationResult.model_validate({
                "success": True
            })

    def test_failure_cannot_expose_account_data(self):
        with self.assertRaises(ValidationError):
            InvestigationResult.model_validate({
                "success": False,
                "error": "ACCESS_DENIED",
                "workspace": "Acme Workspace"
            })

    def test_negative_member_count_rejected(self):
        valid_result = {
            "success": True,
            "ticket_id": "TCK-001",
            "subject": "Invitation issue",
            "status": "open",
            "priority": "unknown",
            "workspace": "Acme Workspace",
            "plan": "Free",
            "member_count": -1,
            "max_members": 5,
            "member_limit_reached": False
        }

        with self.assertRaises(ValidationError):
            InvestigationResult.model_validate(valid_result)

    def test_inconsistent_member_limit_rejected(self):
        valid_result = {
            "success": True,
            "ticket_id": "TCK-001",
            "subject": "Invitation issue",
            "status": "open",
            "priority": "unknown",
            "workspace": "Acme Workspace",
            "plan": "Free",
            "member_count": 5,
            "max_members": 5,
            "member_limit_reached": False
        }

        with self.assertRaises(ValidationError):
            InvestigationResult.model_validate(valid_result)



if __name__ == "__main__":
    unittest.main()
