
from keyword_search import load_chunks
from report_validation import validate_report_references


RETRIEVED_IDS = [
    "plans:3",
    "invitations:2",
    "invitations:3",
    "plans:2",
    "invitations:1",
]


CLAIM_CASES = [
    {
        "id": "C1",
        "claim": "Member limit disables invite button.",
        "citation": "[invitations:2]",
        "supporting_ids": ["invitations:2"],
    },
    {
        "id": "C2",
        "claim": "Member limits depend on plan.",
        "citation": "[plans:3]",
        "supporting_ids": ["plans:3"],
    },
    {
        "id": "C3",
        "claim": "Free plan supports maximum 5 members.",
        "citation": "[plans:3]",
        "supporting_ids": ["plans:1"],
    },
    {
        "id": "C4",
        "claim": "Only workspace admins can invite.",
        "citation": "[invitations:1]",
        "supporting_ids": ["invitations:1"],
    },
    {
        "id": "C5",
        "claim": "Remove a member or consider upgrading.",
        "citation": "[invitations:3, plans:3]",
        "supporting_ids": [
            "invitations:3",
            "plans:3",
        ],
    },
    {
        "id": "C6",
        "claim": "Pro plan supports 20 members.",
        "citation": "[plans:2]",
        "supporting_ids": ["plans:2"],
    },
]


def evaluate_claims(cases, retrieved_ids):
    retrieved_hits = [
        {"chunk_id": chunk_id}
        for chunk_id in retrieved_ids
    ]

    trusted_ids = {
        chunk["chunk_id"]
        for chunk in load_chunks()
    }

    results = []

    for case in cases:
        expected_ids = set(case["supporting_ids"])

        if not expected_ids.issubset(trusted_ids):
            raise ValueError(
                f"Invalid annotation: {case['id']}"
            )

        audit = validate_report_references(
            case["citation"],
            retrieved_hits
        )

        cited_ids = set(audit["cited_ids"])

        # Source alignment against human annotations.
        aligned = (
            audit["references_valid"]
            and bool(cited_ids)
            and cited_ids.issubset(expected_ids)
        )

        results.append({
            "id": case["id"],
            "claim": case["claim"],
            "citation_valid": audit["references_valid"],
            "source_aligned": aligned,
            "cited_ids": sorted(cited_ids),
            "expected_ids": sorted(expected_ids),
        })

    return results


def main():
    results = evaluate_claims(
        CLAIM_CASES,
        RETRIEVED_IDS
    )

    print("=== GROUNDING EVALUATION ===")

    for result in results:
        print(f"\nClaim: {result['id']}")
        print(f"Text: {result['claim']}")
        print(f"Cited: {result['cited_ids']}")
        print(f"Expected: {result['expected_ids']}")
        print(
            "Citation valid:",
            result["citation_valid"]
        )
        print(
            "Source aligned:",
            result["source_aligned"]
        )

    aligned_count = sum(
        result["source_aligned"]
        for result in results
    )

    print("\n=== SUMMARY ===")
    print(f"Claims evaluated: {len(results)}")
    print(f"Source aligned: {aligned_count}")
    print(
        "Source alignment rate:",
        f"{aligned_count / len(results):.2f}"
    )

    print(
        "NOTE: Evidence labels are manually assigned."
    )


if __name__ == "__main__":
    main()
