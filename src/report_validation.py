
import re


CITATION_PATTERN = re.compile(
    r"\[([A-Za-z0-9_-]+:\d+)\]"
    r"|\(([A-Za-z0-9_-]+:\d+)\)"
)


def validate_report_references(report: str, retrieved_hits: list[dict]):
    available_ids = {
        hit["chunk_id"]
        for hit in retrieved_hits
    }

    cited_ids = []
    noncanonical_ids = []

    for match in CITATION_PATTERN.finditer(report):
        bracketed_id = match.group(1)
        parenthesized_id = match.group(2)

        chunk_id = bracketed_id or parenthesized_id

        if chunk_id not in cited_ids:
            cited_ids.append(chunk_id)

        # Recognize (chunk_id), but prefer [chunk_id].
        if (
            parenthesized_id
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
            len(cited_ids) > 0
            and len(unknown_ids) == 0
        ),
        "cited_ids": cited_ids,
        "unknown_ids": unknown_ids,
        "noncanonical_ids": noncanonical_ids,
    }
