
from keyword_search import keyword_search
from semantic_search import semantic_search


EVALUATION_CASES = [
    {
        "name": "turkish_invitation",
        "query": (
            "Yeni bir çalışan eklemek istiyorum "
            "ama davet butonu pasif görünüyor."
        ),
        "relevant_chunks": [
            "invitations:2",
            "invitations:1"
        ]
    },
    {
        "name": "english_member_limit",
        "query": (
            "The invitation button is disabled "
            "because of the member limit."
        ),
        "relevant_chunks": [
            "invitations:2",
            "invitations:3",
            "plans:3"
        ]
    }
]


def recall_at_k(results, relevant_chunks):
    relevant = set(relevant_chunks)

    if not relevant:
        raise ValueError(
            "Relevant chunks cannot be empty."
        )

    retrieved = {
        result["chunk_id"]
        for result in results
    }

    found = retrieved.intersection(relevant)

    return len(found) / len(relevant)


def evaluate():
    print("=== RETRIEVAL EVALUATION ===")

    for case in EVALUATION_CASES:
        print(f"\nScenario: {case['name']}")
        print(f"Query: {case['query']}")

        relevant = case["relevant_chunks"]

        keyword_results = keyword_search(
            case["query"],
            top_k=3
        )

        semantic_results, tokens = semantic_search(
            case["query"],
            top_k=3
        )

        keyword_recall = recall_at_k(
            keyword_results,
            relevant
        )

        semantic_recall = recall_at_k(
            semantic_results,
            relevant
        )

        print(f"Relevant chunks: {relevant}")

        print("\nKeyword results:")
        for result in keyword_results:
            print(f"  {result['chunk_id']}")

        print(f"Keyword Recall@3: {keyword_recall:.2f}")

        print("\nSemantic results:")
        for result in semantic_results:
            print(
                f"  {result['chunk_id']} "
                f"(similarity={result['score']:.4f})"
            )

        print(f"Semantic Recall@3: {semantic_recall:.2f}")
        print(f"Embedding tokens: {tokens}")


if __name__ == "__main__":
    evaluate()
