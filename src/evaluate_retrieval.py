
from keyword_search import keyword_search
from semantic_search import semantic_search
from hybrid_search import reciprocal_rank_fusion


TOP_K = 3


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


def recall_at_k(results, relevant_chunks, k=3):
    relevant = set(relevant_chunks)

    if not relevant:
        raise ValueError(
            "Relevant chunks cannot be empty."
        )

    retrieved = {
        item["chunk_id"]
        for item in results[:k]
    }

    found = retrieved.intersection(relevant)

    return len(found) / len(relevant)


def precision_at_k(results, relevant_chunks, k=3):
    if k < 1:
        raise ValueError("k must be positive.")

    relevant = set(relevant_chunks)

    retrieved = {
        item["chunk_id"]
        for item in results[:k]
    }

    found = retrieved.intersection(relevant)

    return len(found) / k


def evaluate():
    print("=== RETRIEVAL COMPARISON ===")

    total_embedding_tokens = 0

    for case in EVALUATION_CASES:
        print(f"\nScenario: {case['name']}")
        print(f"Query: {case['query']}")

        relevant = case["relevant_chunks"]

        # 1. Keyword Search
        keyword_results = keyword_search(
            case["query"],
            top_k=TOP_K
        )

        # 2. Semantic Search
        semantic_results, tokens = semantic_search(
            case["query"],
            top_k=TOP_K
        )

        total_embedding_tokens += tokens

        # 3. Hybrid Search using existing results
        hybrid_results = reciprocal_rank_fusion(
            keyword_results,
            semantic_results,
            top_k=TOP_K
        )

        methods = {
            "Keyword": keyword_results,
            "Semantic": semantic_results,
            "Hybrid": hybrid_results
        }

        print(f"Relevant chunks: {relevant}")

        for method_name, results in methods.items():
            recall = recall_at_k(
                results,
                relevant,
                TOP_K
            )

            precision = precision_at_k(
                results,
                relevant,
                TOP_K
            )

            chunk_ids = [
                item["chunk_id"]
                for item in results
            ]

            print(f"\n{method_name} Search:")
            print(f"  Results: {chunk_ids}")
            print(f"  Recall@3: {recall:.2f}")
            print(f"  Precision@3: {precision:.2f}")

        print(f"\nEmbedding tokens: {tokens}")

    print("\n=== TOTAL USAGE ===")
    print(
        f"Embedding tokens: {total_embedding_tokens}"
    )


if __name__ == "__main__":
    evaluate()
