
import json
import re

from datetime import datetime, timezone
from pathlib import Path

from report_validation import (
    CITATION_GROUP_PATTERN,
    CITATION_LIST_PATTERN,
    CITATION_ID,
    validate_report_references,
)


EVIDENCE_FIELDS = [
    "ticket_id",
    "status",
    "priority",
    "workspace",
    "plan",
    "member_count",
    "max_members",
    "member_limit_reached",
]


def extract_line_citations(line: str):
    found = []

    for match in CITATION_GROUP_PATTERN.finditer(line):
        group = match.group(1) or match.group(2)

        if not CITATION_LIST_PATTERN.fullmatch(group):
            continue

        for chunk_id in re.findall(CITATION_ID, group):
            if chunk_id not in found:
                found.append(chunk_id)

    return found


def build_review_packet(
    report_text: str,
    retrieved_hits: list[dict],
    investigation_data: dict,
):
    audit = validate_report_references(
        report_text,
        retrieved_hits
    )

    if not audit["references_valid"]:
        raise ValueError(
            "Report contains missing or unknown citations."
        )

    sources = {
        hit["chunk_id"]: hit
        for hit in retrieved_hits
    }

    cited_lines = []
    uncited_lines = []

    for raw_line in report_text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        citation_ids = extract_line_citations(line)

        if not citation_ids:
            uncited_lines.append(line)
            continue

        citations = []

        for chunk_id in citation_ids:
            hit = sources[chunk_id]

            citations.append({
                "chunk_id": chunk_id,
                "source": hit["source"],
                "content": hit["content"],
            })

        cited_lines.append({
            "text": line,
            "citations": citations,
            "manual_verdict": "NOT_REVIEWED",
        })

    account_evidence = {
        field: investigation_data[field]
        for field in EVIDENCE_FIELDS
    }

    return {
        "review_status": "PENDING_MANUAL_REVIEW",
        "report_text": report_text,
        "account_evidence": account_evidence,
        "citation_audit": audit,
        "cited_lines_for_review": cited_lines,
        "uncited_lines_for_review": uncited_lines,
    }


def save_review_packet(
    packet: dict,
    project_root: Path,
):
    output_dir = project_root / "artifacts"
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%S%fZ")

    output_path = (
        output_dir / f"grounding-review-{timestamp}.json"
    )

    output_path.write_text(
        json.dumps(
            packet,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return output_path
