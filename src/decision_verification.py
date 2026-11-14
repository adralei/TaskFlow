
import hashlib
import json
import re

try:
    from src.review_decision import build_review_decision
except ImportError:  # pragma: no cover
    from review_decision import build_review_decision


def calculate_evidence_hash(evidence: list) -> str:
    evidence_json = json.dumps(
        evidence,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False
    )

    return hashlib.sha256(
        evidence_json.encode("utf-8")
    ).hexdigest()


def verify_decision_against_review(
    event: dict,
    current_review: dict
) -> dict:

    if (
        not isinstance(event, dict)
        or event.get("event_type")
            != "CLAIM_REVIEW_DECISION"
        or event.get("verdict") not in (
            "SUPPORTED",
            "UNSUPPORTED",
            "NEEDS_MORE_EVIDENCE"
        )
        or not isinstance(event.get("evidence_sha256"), str)
        or not re.fullmatch(
            r"[0-9a-f]{64}",
            event["evidence_sha256"]
        )
    ):
        return {
            "matches": False,
            "reason": "INVALID_EVENT"
        }

    if (
        not isinstance(current_review, dict)
        or current_review.get("review_verdict")
            != "NOT_REVIEWED"
        or not isinstance(current_review.get("claim"), str)
        or not current_review["claim"].strip()
        or current_review.get("evidence_type")
            not in ("ACCOUNT", "DOCUMENT", "BOTH")
        or not isinstance(
            current_review.get("evidence"), list
        )
        or not current_review["evidence"]
    ):
        return {
            "matches": False,
            "reason": "INVALID_REVIEW"
        }

    if event.get("claim") != current_review["claim"]:
        return {
            "matches": False,
            "reason": "CLAIM_CHANGED"
        }

    if (
        event.get("evidence_type")
        != current_review["evidence_type"]
    ):
        return {
            "matches": False,
            "reason": "EVIDENCE_TYPE_CHANGED"
        }

    try:
        current_hash = calculate_evidence_hash(
            current_review["evidence"]
        )

    except (TypeError, ValueError, OverflowError):
        return {
            "matches": False,
            "reason": "INVALID_REVIEW"
        }

    if current_hash != event["evidence_sha256"]:
        return {
            "matches": False,
            "reason": "EVIDENCE_CHANGED"
        }

    return {
        "matches": True,
        "reason": "MATCH"
    }


if __name__ == "__main__":

    original_review = {
        "claim": "Member limit reached.",
        "evidence_type": "ACCOUNT",
        "evidence": [
            {
                "kind": "ACCOUNT",
                "field": "member_count",
                "value": 5
            }
        ],
        "review_verdict": "NOT_REVIEWED"
    }

    # Synthetic event, not an actual human approval.
    event = build_review_decision(
        original_review,
        {
            "verdict": "NEEDS_MORE_EVIDENCE",
            "reason": "Synthetic verification demonstration."
        },
        reviewer_id="demo-reviewer"
    )

    print("=== DECISION VERIFICATION ===")

    unchanged = verify_decision_against_review(
        event,
        original_review
    )

    print("\nUnchanged evidence:")
    print(unchanged)

    changed_review = {
        **original_review,
        "evidence": [
            {
                "kind": "ACCOUNT",
                "field": "member_count",
                "value": 4
            }
        ]
    }

    changed = verify_decision_against_review(
        event,
        changed_review
    )

    print("\nChanged evidence:")
    print(changed)
