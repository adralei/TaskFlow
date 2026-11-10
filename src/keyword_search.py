
from pathlib import Path
import re


DOCS_DIR = (
    Path(__file__).resolve().parent.parent / "docs"
)


def normalize_text(text: str):
    return text.lower().strip()


def chunk_document(content: str):
    sections = re.split(
        r"(?=^## )",
        content,
        flags=re.MULTILINE
    )

    return [
        section.strip()
        for section in sections
        if section.strip()
    ]



def load_chunks():
    chunks = []

    for file_path in sorted(DOCS_DIR.glob("*.md")):
        content = file_path.read_text(
            encoding="utf-8"
        )

        sections = chunk_document(content)

        for index, section in enumerate(sections):

            lines = [
                line.strip()
                for line in section.splitlines()
                if line.strip()
            ]

            # Skip sections containing only headings.
            heading_only = all(
                line.startswith("#")
                for line in lines
            )

            if heading_only:
                continue

            chunks.append({
                "chunk_id": f"{file_path.stem}:{index}",
                "source": file_path.name,
                "content": section
            })

    return chunks



def keyword_search(query: str, top_k: int = 3):
    chunks = load_chunks()

    query_words = set(
        re.findall(r"\w+", normalize_text(query))
    )

    results = []

    for chunk in chunks:
        content = normalize_text(chunk["content"])

        content_words = set(
            re.findall(r"\w+", content)
        )

        score = len(
            query_words.intersection(content_words)
        )

        if score > 0:
            results.append({
                **chunk,
                "score": score
            })

    results.sort(
        key=lambda item: (
            -item["score"],
            item["chunk_id"]
        )
    )

    return results[:top_k]


if __name__ == "__main__":

    query = "invitation button disabled member limit"

    print("=== KEYWORD SEARCH ===")
    print(f"Query: {query}")

    chunks = load_chunks()

    print(f"Total chunks: {len(chunks)}")

    results = keyword_search(query)

    print(f"Matching results: {len(results)}")

    for result in results:
        print()
        print(f"Chunk: {result['chunk_id']}")
        print(f"Source: {result['source']}")
        print(f"Score: {result['score']}")
        print(result["content"])
