
import json
from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


class ClaimEvidenceRequest(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    claim: str = Field(
        min_length=1,
        max_length=500
    )

    evidence_type: Literal["ACCOUNT", "DOCUMENT"]

    account_fields: list[str] = Field(
        default_factory=list
    )

    document_ids: list[str] = Field(
        default_factory=list
    )

    @field_validator("claim")
    @classmethod
    def nonempty_claim(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Claim cannot be blank.")

        return value

    @model_validator(mode="after")
    def match_evidence_type(self):

        if self.evidence_type == "ACCOUNT":
            if not self.account_fields or self.document_ids:
                raise ValueError(
                    "ACCOUNT requires only account_fields."
                )

        else:
            if not self.document_ids or self.account_fields:
                raise ValueError(
                    "DOCUMENT requires only document_ids."
                )

        fields = self.account_fields or self.document_ids

        if len(fields) != len(set(fields)):
            raise ValueError(
                "Duplicate evidence references."
            )

        return self


def prepare_claim_review(
    request_data: dict,
    packet: dict
) -> dict:

    try:
        request = ClaimEvidenceRequest.model_validate(
            request_data
        )

    except ValidationError:
        return {
            "success": False,
            "error": "INVALID_INPUT"
        }

    try:
        if (
            packet["review_status"] != "PENDING_MANUAL_REVIEW"
            or packet["citation_audit"]["references_valid"]
            is not True
        ):
            return {
                "success": False,
                "error": "INVALID_PACKET"
            }

        evidence = []

        if request.evidence_type == "ACCOUNT":

            account = packet["account_evidence"]

            for field in request.account_fields:

                if field not in account:
                    return {
                        "success": False,
                        "error": "EVIDENCE_NOT_FOUND"
                    }

                evidence.append({
                    "kind": "ACCOUNT",
                    "field": field,
                    "value": account[field]
                })

        else:
            sources = {}

            for line in packet["cited_lines_for_review"]:
                for citation in line["citations"]:

                    chunk_id = citation["chunk_id"]

                    if (
                        chunk_id in sources
                        and sources[chunk_id] != citation
                    ):
                        return {
                            "success": False,
                            "error": "INVALID_PACKET"
                        }

                    sources[chunk_id] = citation

            for chunk_id in request.document_ids:

                if chunk_id not in sources:
                    return {
                        "success": False,
                        "error": "EVIDENCE_NOT_FOUND"
                    }

                citation = sources[chunk_id]

                evidence.append({
                    "kind": "DOCUMENT",
                    "chunk_id": chunk_id,
                    "source": citation["source"],
                    "content": citation["content"]
                })

        return {
            "success": True,
            "data": {
                "claim": request.claim,
                "evidence_type": request.evidence_type,
                "evidence": evidence,
                "review_verdict": "NOT_REVIEWED"
            }
        }

    except (KeyError, TypeError, ValueError):
        return {
            "success": False,
            "error": "INVALID_PACKET"
        }


if __name__ == "__main__":

    project_root = Path(__file__).resolve().parent.parent

    packet_files = sorted(
        (project_root / "artifacts").glob(
            "grounding-review-*.json"
        )
    )

    if not packet_files:
        raise FileNotFoundError(
            "Run support_rag_agent.py to create a packet."
        )

    packet = json.loads(
        packet_files[-1].read_text(
            encoding="utf-8"
        )
    )

    examples = [
        {
            "claim": "Çalışma alanında 5/5 üye var.",
            "evidence_type": "ACCOUNT",
            "account_fields": [
                "member_count",
                "max_members"
            ]
        },
        {
            "claim": (
                "Üye limiti dolunca davet butonu "
                "pasifleşir."
            ),
            "evidence_type": "DOCUMENT",
            "document_ids": [
                "invitations:2"
            ]
        }
    ]

    print("=== STRUCTURED CLAIM REVIEW ===")

    for example in examples:
        result = prepare_claim_review(
            example,
            packet
        )

        print(f"\nClaim: {example['claim']}")
        print(f"Success: {result['success']}")

        if result["success"]:
            data = result["data"]

            print(
                "Evidence type:",
                data["evidence_type"]
            )
            print(
                "Evidence count:",
                len(data["evidence"])
            )
            print(
                "Review verdict:",
                data["review_verdict"]
            )

        else:
            print("Error:", result["error"])
