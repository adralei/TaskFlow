
from openai import OpenAIError

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from hybrid_search import hybrid_search
from keyword_search import load_chunks


class KnowledgeSearchRequest(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    query: str = Field(
        min_length=1,
        max_length=500
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=5
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Query cannot be empty."
            )

        return value


class KnowledgeSearchHit(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    chunk_id: str
    source: str
    content: str
    rrf_score: float = Field(ge=0)
    ranks: dict[str, int]


class KnowledgeSearchData(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    results: list[KnowledgeSearchHit]
    embedding_tokens: int = Field(ge=0)


class KnowledgeSearchResponse(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    success: bool
    data: KnowledgeSearchData | None = None
    error: str | None = None

    @model_validator(mode="after")
    def validate_response(self):

        if self.success:
            if self.data is None or self.error is not None:
                raise ValueError(
                    "Successful response requires data."
                )

        else:
            if self.data is not None or not self.error:
                raise ValueError(
                    "Failed response requires only an error."
                )

        return self


def safe_search_knowledge(request_data: dict):

    # 1. Validate incoming request.
    try:
        request = KnowledgeSearchRequest.model_validate(
            request_data
        )

    except ValidationError:
        return KnowledgeSearchResponse(
            success=False,
            error="INVALID_INPUT"
        )

    # 2. Execute retrieval.
    try:
        results, tokens = hybrid_search(
            query=request.query,
            top_k=request.top_k
        )

        # Build trusted source index from local docs.
        trusted_chunks = {
            chunk["chunk_id"]: chunk
            for chunk in load_chunks()
        }

        if len(results) > request.top_k:
            raise ValueError(
                "Too many search results."
            )

        validated_hits = []
        seen_ids = set()

        for result in results:
            chunk_id = result["chunk_id"]
            trusted = trusted_chunks.get(chunk_id)

            # Reject unknown or duplicated references.
            if trusted is None or chunk_id in seen_ids:
                raise ValueError(
                    "Invalid search source."
                )

            # Verify the returned source and content.
            if (
                result["source"] != trusted["source"]
                or result["content"] != trusted["content"]
            ):
                raise ValueError(
                    "Search source mismatch."
                )

            seen_ids.add(chunk_id)

            validated_hits.append(
                KnowledgeSearchHit(
                    chunk_id=chunk_id,
                    source=trusted["source"],
                    content=trusted["content"],
                    rrf_score=result["rrf_score"],
                    ranks=result["ranks"]
                )
            )

        data = KnowledgeSearchData(
            results=validated_hits,
            embedding_tokens=tokens
        )

        return KnowledgeSearchResponse(
            success=True,
            data=data
        )

    except (OSError, UnicodeError):
        return KnowledgeSearchResponse(
            success=False,
            error="DATA_ACCESS_ERROR"
        )

    except OpenAIError:
        return KnowledgeSearchResponse(
            success=False,
            error="EMBEDDING_SERVICE_ERROR"
        )

    except (
        ValidationError,
        ValueError,
        KeyError,
        TypeError
    ):
        return KnowledgeSearchResponse(
            success=False,
            error="INVALID_SEARCH_OUTPUT"
        )

    except Exception:
        return KnowledgeSearchResponse(
            success=False,
            error="INTERNAL_ERROR"
        )


if __name__ == "__main__":

    print("=== VALID KNOWLEDGE SEARCH ===")

    result = safe_search_knowledge({
        "query": (
            "Yeni bir çalışan eklemek istiyorum "
            "ama davet butonu pasif görünüyor."
        ),
        "top_k": 3
    })

    print(f"Success: {result.success}")

    if result.success:
        for hit in result.data.results:
            print()
            print(f"Chunk: {hit.chunk_id}")
            print(f"Source: {hit.source}")
            print(f"RRF Score: {hit.rrf_score:.5f}")
            print(f"Ranks: {hit.ranks}")

        print(
            "\nEmbedding tokens:",
            result.data.embedding_tokens
        )

    else:
        print(f"Error: {result.error}")

    print("\n=== INVALID INPUT ===")

    invalid = safe_search_knowledge({
        "query": "invitation disabled",
        "top_k": -1
    })

    print(
        invalid.model_dump(exclude_none=True)
    )

    print("\n=== UNEXPECTED FIELD ===")

    unexpected = safe_search_knowledge({
        "query": "invitation disabled",
        "tenant_id": "tenant-002"
    })

    print(
        unexpected.model_dump(exclude_none=True)
    )
