
import json

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)


class ApprovalRecord(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    event_id: UUID

    event_type: Literal["TICKET_RESOLUTION_APPROVAL"]

    approval_type: Literal["CUSTOMER", "OPERATOR"]

    action: Literal["RESOLVE_TICKET"]

    actor_id: str = Field(min_length=1)

    ticket_id: str = Field(min_length=1)

    packet_id: str = Field(min_length=1)

    packet_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$"
    )

    approved: Literal[True]

    approved_at: datetime

    @field_validator("actor_id", "ticket_id", "packet_id")
    @classmethod
    def reject_blank_values(cls, value):
        if not value.strip():
            raise ValueError("Value cannot be blank.")

        return value

    @field_validator("approved_at")
    @classmethod
    def require_timezone(cls, value):
        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "Timestamp must include timezone."
            )

        return value


def create_approval_record(
    approval_type: str,
    actor_id: str,
    ticket_id: str,
    packet_id: str,
    packet_sha256: str,
) -> dict:

    # In a real application, these values must be
    # supplied by an authenticated approval workflow.
    record = ApprovalRecord(
        event_id=uuid4(),
        event_type="TICKET_RESOLUTION_APPROVAL",
        approval_type=approval_type,
        action="RESOLVE_TICKET",
        actor_id=actor_id,
        ticket_id=ticket_id,
        packet_id=packet_id,
        packet_sha256=packet_sha256,
        approved=True,
        approved_at=datetime.now(timezone.utc),
    )

    return record.model_dump(mode="json")


def validate_approval_pair(
    customer_record: dict,
    operator_record: dict,
    ticket_id: str,
    packet_id: str,
    packet_sha256: str,
) -> dict:

    def rejected(reason):
        return {
            "valid": False,
            "reason": reason
        }

    try:
        customer = ApprovalRecord.model_validate_json(
            json.dumps(customer_record)
        )

        operator = ApprovalRecord.model_validate_json(
            json.dumps(operator_record)
        )

    except (ValidationError, TypeError, ValueError):
        return rejected("INVALID_APPROVAL_RECORD")

    if (
        customer.approval_type != "CUSTOMER"
        or operator.approval_type != "OPERATOR"
    ):
        return rejected("APPROVAL_TYPE_MISMATCH")

    if customer.event_id == operator.event_id:
        return rejected("DUPLICATE_APPROVAL_EVENT")

    if customer.actor_id == operator.actor_id:
        return rejected("SAME_ACTOR")

    for record in (customer, operator):
        if (
            record.ticket_id != ticket_id
            or record.packet_id != packet_id
            or record.packet_sha256 != packet_sha256
        ):
            return rejected("APPROVAL_CONTEXT_MISMATCH")

    return {
        "valid": True,
        "reason": "APPROVALS_VERIFIED"
    }


if __name__ == "__main__":

    demo_packet_hash = "a" * 64

    customer = create_approval_record(
        approval_type="CUSTOMER",
        actor_id="demo-customer",
        ticket_id="TCK-001",
        packet_id="packet-001",
        packet_sha256=demo_packet_hash,
    )

    operator = create_approval_record(
        approval_type="OPERATOR",
        actor_id="demo-operator",
        ticket_id="TCK-001",
        packet_id="packet-001",
        packet_sha256=demo_packet_hash,
    )

    print("=== STRUCTURED APPROVAL RECORDS ===")
    print("Customer event:", customer["event_id"])
    print("Operator event:", operator["event_id"])

    result = validate_approval_pair(
        customer,
        operator,
        ticket_id="TCK-001",
        packet_id="packet-001",
        packet_sha256=demo_packet_hash,
    )

    print("Validation:", result)
    print("Ticket updated: False")
    print("NOTE: Synthetic approvals only.")
