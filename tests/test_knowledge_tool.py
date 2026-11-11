
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from openai import OpenAIError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from knowledge_tool import safe_search_knowledge


# Synthetic trusted document for isolated testing.
TRUSTED_CHUNKS = [
    {
        "chunk_id": "invitations:2",
        "source": "invitations.md",
        "content": "Invitation button is disabled at member limit."
    }
]

VALID_HIT = {
    **TRUSTED_CHUNKS[0],
    "rrf_score": 0.01639,
    "ranks": {"semantic": 1}
}


class TestKnowledgeTool(unittest.TestCase):

    def run_mocked_search(self, hits, top_k=3):
        with patch(
            "knowledge_tool.hybrid_search",
            return_value=(hits, 12)
        ), patch(
            "knowledge_tool.load_chunks",
            return_value=TRUSTED_CHUNKS
        ):
            return safe_search_knowledge({
                "query": "invitation disabled",
                "top_k": top_k
            })

    def test_valid_search(self):
        result = self.run_mocked_search([VALID_HIT])

        self.assertTrue(result.success)
        self.assertIsNone(result.error)

        self.assertEqual(
            result.data.results[0].chunk_id,
            "invitations:2"
        )

        self.assertEqual(
            result.data.embedding_tokens,
            12
        )

    def test_invalid_input_skips_search(self):
        invalid_requests = [
            {"query": "invitation", "top_k": -1},
            {"query": "   ", "top_k": 3},
            {
                "query": "invitation",
                "tenant_id": "tenant-002"
            }
        ]

        with patch(
            "knowledge_tool.hybrid_search"
        ) as mock_search:

            for request in invalid_requests:
                with self.subTest(request=request):
                    result = safe_search_knowledge(
                        request
                    )

                    self.assertFalse(result.success)
                    self.assertEqual(
                        result.error,
                        "INVALID_INPUT"
                    )

            mock_search.assert_not_called()

    def test_unknown_source_rejected(self):
        forged_hit = {
            **VALID_HIT,
            "chunk_id": "invitations:999"
        }

        result = self.run_mocked_search([forged_hit])

        self.assertFalse(result.success)
        self.assertEqual(
            result.error,
            "INVALID_SEARCH_OUTPUT"
        )
        self.assertIsNone(result.data)

    def test_modified_content_rejected(self):
        modified_hit = {
            **VALID_HIT,
            "content": "Unverified replacement content."
        }

        result = self.run_mocked_search([modified_hit])

        self.assertFalse(result.success)
        self.assertEqual(
            result.error,
            "INVALID_SEARCH_OUTPUT"
        )

    def test_duplicate_source_rejected(self):
        result = self.run_mocked_search(
            [VALID_HIT, VALID_HIT],
            top_k=2
        )

        self.assertFalse(result.success)
        self.assertEqual(
            result.error,
            "INVALID_SEARCH_OUTPUT"
        )

    def test_malformed_search_result_rejected(self):
        malformed_hit = {
            **VALID_HIT,
            "rrf_score": -1.0
        }

        result = self.run_mocked_search(
            [malformed_hit]
        )

        self.assertFalse(result.success)
        self.assertEqual(
            result.error,
            "INVALID_SEARCH_OUTPUT"
        )

    def test_embedding_service_error(self):
        with patch(
            "knowledge_tool.hybrid_search",
            side_effect=OpenAIError(
                "Simulated embedding failure"
            )
        ):
            result = safe_search_knowledge({
                "query": "invitation"
            })

        self.assertFalse(result.success)
        self.assertEqual(
            result.error,
            "EMBEDDING_SERVICE_ERROR"
        )

    def test_document_access_error(self):
        with patch(
            "knowledge_tool.hybrid_search",
            return_value=([VALID_HIT], 12)
        ), patch(
            "knowledge_tool.load_chunks",
            side_effect=OSError(
                "Document unavailable"
            )
        ):
            result = safe_search_knowledge({
                "query": "invitation"
            })

        self.assertFalse(result.success)
        self.assertEqual(
            result.error,
            "DATA_ACCESS_ERROR"
        )

    def test_unexpected_error(self):
        with patch(
            "knowledge_tool.hybrid_search",
            side_effect=RuntimeError(
                "Unexpected failure"
            )
        ):
            result = safe_search_knowledge({
                "query": "invitation"
            })

        self.assertFalse(result.success)
        self.assertEqual(
            result.error,
            "INTERNAL_ERROR"
        )


if __name__ == "__main__":
    unittest.main()
