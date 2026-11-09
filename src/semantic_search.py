
import math
from openai import OpenAI
from dotenv import load_dotenv

from keyword_search import load_chunks, keyword_search


load_dotenv()

client = OpenAI()

EMBEDDING_MODEL = "text-embedding-3-small"


def cosine_similarity(vector_a, vector_b):
    dot_product = sum(
        a * b for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def semantic_search(query: str, top_k: int = 3):
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be positive.")

    chunks = load_chunks()

    if not chunks:
        return [], 0

    texts = [query] + [
        chunk["content"] for chunk in chunks
    ]

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )

    vectors = [
        item.embedding
        for item in sorted(
            response.data,
            key=lambda item: item.index
        )
    ]

    query_vector = vectors[0]
    document_vectors = vectors[1:]

    results = []

    for chunk, vector in zip(
        chunks, document_vectors
    ):
        score = cosine_similarity(
            query_vector,
            vector
        )

        results.append({
            **chunk,
            "score": round(score, 4)
        })

    results.sort(
        key=lambda item: -item["score"]
    )

    return results[:top_k], response.usage.total_tokens


if __name__ == "__main__":

    query = (
        "Yeni bir çalışan eklemek istiyorum "
        "ama davet butonu pasif görünüyor."
    )

    print("=== SEMANTIC SEARCH ===")
    print(f"Query: {query}")

    keyword_results = keyword_search(query)

    print("\n=== KEYWORD RESULTS ===")
    print(f"Matches: {len(keyword_results)}")

    for result in keyword_results:
        print(
            result["chunk_id"],
            "Score:",
            result["score"]
        )

    semantic_results, tokens = semantic_search(query)

    print("\n=== SEMANTIC RESULTS ===")
    print(f"Matches: {len(semantic_results)}")

    for result in semantic_results:
        print()
        print(f"Chunk: {result['chunk_id']}")
        print(f"Source: {result['source']}")
        print(f"Similarity: {result['score']}")
        print(result["content"])

    print("\n=== USAGE ===")
    print(f"Embedding tokens: {tokens}")
