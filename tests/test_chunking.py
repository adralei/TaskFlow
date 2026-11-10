
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from keyword_search import load_chunks


class TestChunkQuality(unittest.TestCase):

    def test_heading_only_chunks_removed(self):
        chunks = load_chunks()

        chunk_ids = {
            chunk["chunk_id"]
            for chunk in chunks
        }

        self.assertNotIn(
            "invitations:0",
            chunk_ids
        )

        self.assertNotIn(
            "plans:0",
            chunk_ids
        )

    def test_important_chunks_preserved(self):
        chunks = load_chunks()

        chunk_ids = {
            chunk["chunk_id"]
            for chunk in chunks
        }

        self.assertIn(
            "invitations:2",
            chunk_ids
        )

        self.assertIn(
            "invitations:1",
            chunk_ids
        )

        self.assertIn(
            "plans:3",
            chunk_ids
        )


if __name__ == "__main__":
    unittest.main()
