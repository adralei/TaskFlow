
import hashlib
import json

from claim_evidence import prepare_claim_review
from review_decision import build_review_decision
from decision_verification import (
    verify_decision_against_review,
)


def packet_fingerprint(packet: dict) -> str:
    serialized = json.dumps(
        packet,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def get_ticket_id(packet: dict) -> str:
    ticket_id = packet["account_evidence"]["ticket_id"]

    if not isinstance(ticket_id, str) or not ticket_id.strip():
        raise ValueError("Invalid ticket ID.")

    return ticket_id


def build_bound_decision(
    claim_request: dict,
    packet: dict,
    packet_id: str,
    decision_data: dict,
    reviewer_id: str,
) -> dict:

    if not isinstance(packet_id, str) or not packet_id.strip():
        raise ValueError("Packet ID is required.")

    ticket_id = get_ticket_id(packet)

    claim_result = prepare_claim_review(
        claim_request,
        packet
    )

    if not claim_result["success"]:
        raise ValueError(
            f"Claim review failed: {claim_result['error']}"
        )

    event = build_review_decision(
        claim_result["data"],
        decision_data,
        reviewer_id
    )

    # Attach the trusted review context.
    event["ticket_id"] = ticket_id
    event["packet_id"] = packet_id
    event["packet_sha256"] = packet_fingerprint(packet)

    return event


def verify_bound_decision(
    event: dict,
    claim_request: dict,
    packet: dict,
    packet_id: str,
) -> dict:

    if not isinstance(event, dict):
        return {
            "matches": False,
            "reason": "INVALID_EVENT"
        }

    if not isinstance(packet_id, str) or not packet_id.strip():
        return {
            "matches": False,
            "reason": "INVALID_PACKET_ID"
        }

    if (
        not isinstance(event.get("packet_id"), str)
        or not isinstance(event.get("ticket_id"), str)
        or not isinstance(event.get("packet_sha256"), str)
    ):
        return {
            "matches": False,
            "reason": "INVALID_EVENT"
        }

    if event["packet_id"] != packet_id:
        return {
            "matches": False,
            "reason": "PACKET_ID_MISMATCH"
        }

    try:
        ticket_id = get_ticket_id(packet)
        current_packet_hash = packet_fingerprint(packet)

    except (
        KeyError,
        TypeError,
        ValueError,
        OverflowError,
    ):
        return {
            "matches": False,
            "reason": "INVALID_PACKET"
        }

    if event["ticket_id"] != ticket_id:
        return {
            "matches": False,
            "reason": "TICKET_MISMATCH"
        }

    if event["packet_sha256"] != current_packet_hash:
        return {
            "matches": False,
            "reason": "PACKET_CHANGED"
        }

    claim_result = prepare_claim_review(
        claim_request,
        packet
    )

    if not claim_result["success"]:
        return {
            "matches": False,
            "reason": "INVALID_CLAIM_REVIEW"
        }

    # Reuse existing evidence verification.
    return verify_decision_against_review(
        event,
        claim_result["data"]
    )
