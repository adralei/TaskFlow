
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class ReviewDecisionRequest(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    verdict: Literal[
        "SUPPORTED",
        "UNSUPPORTED",
        "NEEDS_MORE_EVIDENCE"
    ]

    reason: str = Field(
        min_length=5,
        max_length=1000
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value):
        value = value.strip()

        if len(value) < 5:
            raise ValueError(
                "A meaningful reason is required."
            )

        return value


def build_review_decision(
    claim_review: dict,
    decision_data: dict,
    reviewer_id: str
) -> dict:

    # Reviewer identity must come from a trusted
    # application context, not an LLM tool call.
    if (
        not isinstance(reviewer_id, str)
        or not reviewer_id.strip()
    ):
        raise ValueError("Reviewer identity is required.")

    decision = ReviewDecisionRequest.model_validate(
        decision_data
    )

    if (
        not isinstance(claim_review, dict)
        or claim_review.get("review_verdict") != "NOT_REVIEWED"
        or not isinstance(claim_review.get("claim"), str)
        or not claim_review["claim"].strip()
        or claim_review.get("evidence_type")
            not in ("ACCOUNT", "DOCUMENT", "BOTH")
        or not isinstance(claim_review.get("evidence"), list)
        or not claim_review["evidence"]
    ):
        raise ValueError("Invalid claim review.")

    # Stable representation of the reviewed evidence.
    evidence_json = json.dumps(
        claim_review["evidence"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False
    )

    evidence_hash = hashlib.sha256(
        evidence_json.encode("utf-8")
    ).hexdigest()

    return {
        "event_id": str(uuid4()),
        "event_type": "CLAIM_REVIEW_DECISION",
        "claim": claim_review["claim"],
        "evidence_type": claim_review["evidence_type"],
        "evidence_sha256": evidence_hash,
        "verdict": decision.verdict,
        "reason": decision.reason,
        "reviewer_id": reviewer_id.strip(),
        "reviewed_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }


def save_review_decision(
    event: dict,
    project_root: Path
) -> Path:

    output_dir = project_root / "artifacts" / "decisions"

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        output_dir / f"{event['event_id']}.json"
    )

    # Exclusive creation: never overwrite a prior event.
    with output_path.open(
        "x",
        encoding="utf-8"
    ) as file:
        json.dump(
            event,
            file,
            ensure_ascii=False,
            indent=2
        )

    return output_path


if __name__ == "__main__":

    # Synthetic demonstration only.
    # No real reviewer decision is being made.
    example_review = {
        "claim": "The member limit is reached.",
        "evidence_type": "ACCOUNT",
        "evidence": [
            {
                "kind": "ACCOUNT",
                "field": "member_limit_reached",
                "value": True
            }
        ],
        "review_verdict": "NOT_REVIEWED"
    }

    example_decision = {
        "verdict": "NEEDS_MORE_EVIDENCE",
        "reason": (
            "Demonstration decision only; "
            "the claim has not undergone human review."
        )
    }

    event = build_review_decision(
        example_review,
        example_decision,
        reviewer_id="demo-reviewer"
    )

    path = save_review_decision(
        event,
        Path(__file__).resolve().parent.parent
    )

    print("=== REVIEW DECISION DEMO ===")
    print("Event type:", event["event_type"])
    print("Verdict:", event["verdict"])
    print("Reviewer:", event["reviewer_id"])
    print("Reason:", event["reason"])
    print("Evidence SHA-256:", event["evidence_sha256"])
    print("Saved to:", path)
