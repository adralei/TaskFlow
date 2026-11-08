
import json

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    model_validator,
)

from tool_contract import (
    InvestigationRequest,
    run_investigation,
)



class ToolResponse(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    success: bool
    data: dict | None = None
    error: str | None = None

    @model_validator(mode="after")
    def validate_response(self):

        if self.success:
            if self.data is None:
                raise ValueError(
                    "Successful tool response requires data."
                )

            if self.error is not None:
                raise ValueError(
                    "Successful tool response cannot have an error."
                )

        else:
            if self.data is not None:
                raise ValueError(
                    "Failed tool response cannot contain data."
                )

            if not self.error:
                raise ValueError(
                    "Failed tool response requires an error code."
                )

        return self



def safe_run_investigation(
    request_data: dict,
    session_tenant_id: str
) -> ToolResponse:

    # 1. Validate incoming arguments
    try:
        request = InvestigationRequest.model_validate(
            request_data
        )
    except ValidationError:
        return ToolResponse(
            success=False,
            error="INVALID_INPUT"
        )

    # 2. Execute the investigation
    try:
        result = run_investigation(
            request_data=request.model_dump(),
            session_tenant_id=session_tenant_id
        )

    except ValidationError:
        return ToolResponse(
            success=False,
            error="INVALID_TOOL_OUTPUT"
        )

    except (OSError, json.JSONDecodeError):
        return ToolResponse(
            success=False,
            error="DATA_ACCESS_ERROR"
        )

    except Exception:
        return ToolResponse(
            success=False,
            error="INTERNAL_ERROR"
        )

    # 3. Handle expected business errors
    if not result.success:
        return ToolResponse(
            success=False,
            error=result.error
        )

    # 4. Return validated data
    return ToolResponse(
        success=True,
        data=result.model_dump(exclude_none=True)
    )


if __name__ == "__main__":

    scenarios = [
        (
            "VALID REQUEST",
            {"ticket_id": "TCK-001"},
            "tenant-001"
        ),
        (
            "UNAUTHORIZED REQUEST",
            {"ticket_id": "TCK-001"},
            "tenant-002"
        ),
        (
            "INVALID INPUT",
            {"ticket_id": 123},
            "tenant-001"
        ),
        (
            "EXTRA FIELD",
            {
                "ticket_id": "TCK-001",
                "tenant_id": "tenant-002"
            },
            "tenant-001"
        )
    ]

    for name, request_data, session_tenant_id in scenarios:
        print(f"\n=== {name} ===")

        response = safe_run_investigation(
            request_data=request_data,
            session_tenant_id=session_tenant_id
        )

        print(response.model_dump(exclude_none=True))