
from decision_binding import verify_bound_decision


def evaluate_resolution_eligibility(
    event: dict,
    claim_request: dict,
    packet: dict,
    packet_id: str,
    customer_confirmed: bool,
    operator_approved: bool,
) -> dict:

    def blocked(reason):
        return {
            "eligible": False,
            "reason": reason,
            "ticket_updated": False,
        }

    # These inputs must originate from trusted,
    # authenticated application workflows.
    if (
        type(customer_confirmed) is not bool
        or type(operator_approved) is not bool
    ):
        return blocked("INVALID_APPROVAL_INPUT")

    # Verify the decision against its evidence,
    # ticket and original review packet.
    verification = verify_bound_decision(
        event,
        claim_request,
        packet,
        packet_id,
    )

    if not verification["matches"]:
        return blocked("DECISION_VERIFICATION_FAILED")

    # Evidence support is required, but alone
    # is not enough to resolve a ticket.
    if event.get("verdict") != "SUPPORTED":
        return blocked("REVIEW_NOT_SUPPORTED")

    try:
        ticket_status = packet["account_evidence"]["status"]
    except (KeyError, TypeError):
        return blocked("INVALID_TICKET_STATUS")

    if ticket_status != "open":
        return blocked("TICKET_NOT_OPEN")

    if not customer_confirmed:
        return blocked("CUSTOMER_CONFIRMATION_REQUIRED")

    if not operator_approved:
        return blocked("OPERATOR_APPROVAL_REQUIRED")

    # This is ONLY a precondition check.
    # No ticket data is modified.
    return {
        "eligible": True,
        "reason": "PRECONDITIONS_MET",
        "ticket_updated": False,
    }
