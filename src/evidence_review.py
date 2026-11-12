
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ACCOUNT_FIELDS = [
    "ticket_id",
    "status",
    "priority",
    "workspace",
    "plan",
    "member_count",
    "max_members",
    "member_limit_reached",
]


def build_review_markdown(packet: dict) -> str:

    if packet.get("review_status") != "PENDING_MANUAL_REVIEW":
        raise ValueError("Unexpected review status.")

    if not packet.get("citation_audit", {}).get(
        "references_valid", False
    ):
        raise ValueError("Citation audit is not valid.")

    account = packet["account_evidence"]
    cited_lines = packet["cited_lines_for_review"]
    uncited_lines = packet["uncited_lines_for_review"]

    lines = [
        "# TaskFlow - Grounding Evidence Review",
        "",
        "**Status:** PENDING_MANUAL_REVIEW",
        "",
        "> This is a manual review worksheet, "
        "not an automated factual verification.",
        "",
        "## 1. Account Evidence",
        "",
    ]

    for field in ACCOUNT_FIELDS:
        if field in account:
            lines.append(
                f"- **{field}:** `{account[field]}`"
            )

    lines.extend([
        "",
        "## 2. Document Evidence",
        "",
    ])

    # Collect unique cited document chunks.
    sources = {}

    for item in cited_lines:
        for citation in item["citations"]:
            chunk_id = citation["chunk_id"]

            if chunk_id in sources:
                if sources[chunk_id] != citation:
                    raise ValueError(
                        "Conflicting document evidence."
                    )
            else:
                sources[chunk_id] = citation

    if not sources:
        lines.append("No cited document evidence.")

    for chunk_id, source in sources.items():
        lines.extend([
            f"### {chunk_id} ({source['source']})",
            "",
        ])

        # Indent source text so Markdown displays it
        # as evidence rather than document instructions.
        for content_line in source["content"].splitlines():
            lines.append("    " + content_line)

        lines.append("")

    lines.extend([
        "## 3. Cited Lines - Manual Review",
        "",
    ])

    for index, item in enumerate(cited_lines, start=1):

        ids = [
            citation["chunk_id"]
            for citation in item["citations"]
        ]

        lines.extend([
            f"### Cited line {index}",
            "",
            f"> {item['text']}",
            "",
            f"**Citations:** {', '.join(ids)}",
            "",
            "- [ ] Supported by the cited evidence",
            "- [ ] Unsupported or incorrectly cited",
            "- [ ] Needs additional context",
            "",
            "**Reviewer notes:**",
            "",
        ])

    lines.extend([
        "## 4. Uncited Lines - Manual Review",
        "",
        "An uncited line is not automatically incorrect.",
        "It may be a heading, an account-based fact, "
        "or an unsupported claim.",
        "",
    ])

    for index, text in enumerate(uncited_lines, start=1):
        lines.extend([
            f"### Uncited line {index}",
            "",
            f"> {text}",
            "",
            "- [ ] Supported by Account Evidence",
            "- [ ] Heading or non-factual text",
            "- [ ] Needs Document Evidence",
            "- [ ] Unsupported or requires clarification",
            "",
            "**Reviewer notes:**",
            "",
        ])

    lines.extend([
        "## 5. Final Review Decision",
        "",
        "- [ ] Approved after manual review",
        "- [ ] Requires correction",
        "- [ ] Escalate to human support",
        "",
        "**Overall notes:**",
        "",
    ])

    return "\n".join(lines)


def generate_latest_review(project_root: Path):

    artifacts_dir = project_root / "artifacts"

    packets = sorted(
        artifacts_dir.glob("grounding-review-*.json")
    )

    if not packets:
        raise FileNotFoundError(
            "No grounding review packet found."
        )

    latest_packet_path = packets[-1]

    output_path = latest_packet_path.with_suffix(".md")

    # Preserve annotations if the review already exists.
    if output_path.exists():
        return latest_packet_path, output_path, False

    packet = json.loads(
        latest_packet_path.read_text(encoding="utf-8")
    )

    markdown = build_review_markdown(packet)

    output_path.write_text(
        markdown,
        encoding="utf-8"
    )

    return latest_packet_path, output_path, True


if __name__ == "__main__":

    packet_path, review_path, created = (
        generate_latest_review(PROJECT_ROOT)
    )

    print("=== EVIDENCE REVIEW ===")
    print("Source packet:", packet_path)
    print("Review Markdown:", review_path)
    print("New review created:", created)

    if not created:
        print(
            "Existing review preserved without overwriting."
        )

    print(
        "Review status: PENDING_MANUAL_REVIEW"
    )
