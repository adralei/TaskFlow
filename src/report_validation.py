
import re


CITATION_ID = r"[A-Za-z0-9_-]+:\d+"

CITATION_GROUP_PATTERN = re.compile(
    r"\[([^\[\]\n]+)\]|\(([^()\n]+)\)"
)

CITATION_LIST_PATTERN = re.compile(
    rf"\s*{CITATION_ID}"
    rf"(?:\s*,\s*{CITATION_ID})*\s*"
)


def validate_report_references(
    report: str,
    retrieved_hits: list[dict]
):
    available_ids = {
        hit["chunk_id"]
        for hit in retrieved_hits
    }

    cited_ids = []
    noncanonical_ids = []

    for match in CITATION_GROUP_PATTERN.finditer(report):
        bracketed = match.group(1)
        parenthesized = match.group(2)

        group_text = bracketed or parenthesized

        if not CITATION_LIST_PATTERN.fullmatch(group_text):
            continue

        ids = re.findall(
            CITATION_ID,
            group_text
        )

        for chunk_id in ids:
            if chunk_id not in cited_ids:
                cited_ids.append(chunk_id)

            if (
                parenthesized is not None
                and chunk_id not in noncanonical_ids
            ):
                noncanonical_ids.append(chunk_id)

    unknown_ids = [
        chunk_id
        for chunk_id in cited_ids
        if chunk_id not in available_ids
    ]

    return {
        "references_valid": (
            bool(cited_ids)
            and not unknown_ids
        ),
        "cited_ids": cited_ids,
        "unknown_ids": unknown_ids,
        "noncanonical_ids": noncanonical_ids,
    }
