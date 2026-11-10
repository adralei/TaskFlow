
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hybrid_search import reciprocal_rank_fusion


def make_chunk(chunk_id):
    return {
        "chunk_id": chunk_id,
        "source": "test.md",
        "content": f"Content for {chunk_id}"
    }


class TestHybridSearch(unittest.TestCase):

    def test_document_found_by_both_methods(self):
        keyword_results = [
            make_chunk("A"),
            make_chunk("B")
        ]

        semantic_results = [
            make_chunk("C"),
            make_chunk("A")
        ]

        results = reciprocal_rank_fusion(
            keyword_results,
            semantic_results,
            top_k=3
        )

        self.assertEqual(
            results[0]["chunk_id"],
            "A"
        )

        self.assertEqual(
            results[0]["ranks"],
            {"keyword": 1, "semantic": 2}
        )

        self.assertEqual(len(results), 3)

    def test_semantic_only_results(self):
        semantic_results = [
            make_chunk("A"),
            make_chunk("B")
        ]

        results = reciprocal_rank_fusion(
            keyword_results=[],
            semantic_results=semantic_results,
            top_k=2
        )

        self.assertEqual(
            [item["chunk_id"] for item in results],
            ["A", "B"]
        )

        self.assertEqual(
            results[0]["ranks"],
            {"semantic": 1}
        )


if __name__ == "__main__":
    unittest.main()
