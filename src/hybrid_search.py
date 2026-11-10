
from keyword_search import keyword_search
from semantic_search import semantic_search


RRF_K = 60


def reciprocal_rank_fusion(
    keyword_results,
    semantic_results,
    top_k=3
):
    combined = {}

    search_methods = [
        ("keyword", keyword_results),
        ("semantic", semantic_results)
    ]

    for method_name, results in search_methods:

        for rank, chunk in enumerate(results, start=1):
            chunk_id = chunk["chunk_id"]

            if chunk_id not in combined:
                combined[chunk_id] = {
                    "chunk_id": chunk_id,
                    "source": chunk["source"],
                    "content": chunk["content"],
                    "rrf_score": 0.0,
                    "ranks": {}
                }

            contribution = 1 / (RRF_K + rank)

            combined[chunk_id]["rrf_score"] += contribution

            combined[chunk_id]["ranks"][method_name] = rank

    ranked_results = sorted(
        combined.values(),
        key=lambda item: (
            -item["rrf_score"],
            item["chunk_id"]
        )
    )

    return ranked_results[:top_k]


def hybrid_search(query: str, top_k: int = 3):

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    if (
        not isinstance(top_k, int)
        or isinstance(top_k, bool)
        or top_k < 1
    ):
        raise ValueError("top_k must be a positive integer.")

    # Retrieve candidates from both methods.
    keyword_results = keyword_search(
        query,
        top_k=top_k
    )

    semantic_results, tokens = semantic_search(
        query,
        top_k=top_k
    )

    # Combine rankings with RRF.
    hybrid_results = reciprocal_rank_fusion(
        keyword_results,
        semantic_results,
        top_k=top_k
    )

    return hybrid_results, tokens


if __name__ == "__main__":

    queries = [
        (
            "TURKISH QUERY",
            "Yeni bir çalışan eklemek istiyorum "
            "ama davet butonu pasif görünüyor."
        ),
        (
            "ENGLISH QUERY",
            "The invitation button is disabled "
            "because of the member limit."
        )
    ]

    for name, query in queries:
        print(f"\n=== {name} ===")
        print(f"Query: {query}")

        results, tokens = hybrid_search(query)

        print("\n=== HYBRID RESULTS ===")

        for index, result in enumerate(results, start=1):
            print()
            print(f"Rank: {index}")
            print(f"Chunk: {result['chunk_id']}")
            print(f"Source: {result['source']}")
            print(f"RRF Score: {result['rrf_score']:.5f}")
            print(f"Method Ranks: {result['ranks']}")

        print(f"\nEmbedding tokens: {tokens}")
