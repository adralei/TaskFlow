
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    model_validator,
)

from investigate_ticket import investigate_ticket


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    ticket_id: str



class InvestigationResult(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    success: bool
    error: str | None = None

    ticket_id: str | None = None
    subject: str | None = None
    status: str | None = None
    priority: str | None = None
    workspace: str | None = None
    plan: str | None = None
    member_count: int | None = None
    max_members: int | None = None
    member_limit_reached: bool | None = None

    @model_validator(mode="after")
    def validate_result(self):

        data_fields = [
            "ticket_id",
            "subject",
            "status",
            "priority",
            "workspace",
            "plan",
            "member_count",
            "max_members",
            "member_limit_reached"
        ]

        if self.success:
            if self.error is not None:
                raise ValueError(
                    "Successful results cannot contain an error."
                )

            missing_fields = [
                field
                for field in data_fields
                if getattr(self, field) is None
            ]

            if missing_fields:
                raise ValueError(
                    f"Missing result fields: {missing_fields}"
                )

            if self.member_count < 0:
                raise ValueError(
                    "Member count cannot be negative."
                )

            if self.max_members <= 0:
                raise ValueError(
                    "Max members must be positive."
                )

            expected_limit = (
                self.member_count >= self.max_members
            )

            if self.member_limit_reached != expected_limit:
                raise ValueError(
                    "Member limit result is inconsistent."
                )

        else:
            if not self.error:
                raise ValueError(
                    "Failed results must contain an error."
                )

            exposed_fields = [
                field
                for field in data_fields
                if getattr(self, field) is not None
            ]

            if exposed_fields:
                raise ValueError(
                    "Failed results cannot contain account or ticket data."
                )

        return self



def run_investigation(
    request_data: dict,
    session_tenant_id: str
):
    request = InvestigationRequest.model_validate(
        request_data
    )

    raw_result = investigate_ticket(
        ticket_id=request.ticket_id,
        session_tenant_id=session_tenant_id
    )

    return InvestigationResult.model_validate(
        raw_result
    )


if __name__ == "__main__":

    print("=== VALID REQUEST ===")

    result = run_investigation(
        request_data={"ticket_id": "TCK-001"},
        session_tenant_id="tenant-001"
    )

    print(result.model_dump(exclude_none=True))

    print("\n=== UNAUTHORIZED REQUEST ===")

    result = run_investigation(
        request_data={"ticket_id": "TCK-001"},
        session_tenant_id="tenant-002"
    )

    print(result.model_dump(exclude_none=True))

    print("\n=== INVALID INPUT ===")

    try:
        run_investigation(
            request_data={"ticket_id": 123},
            session_tenant_id="tenant-001"
        )
    except ValidationError as error:
        print("Input validation failed.")
        print(error.errors()[0]["type"])

    print("\n=== INVALID OUTPUT ===")

    try:
        InvestigationResult.model_validate({
            "success": "yes",
            "error": None
        })
    except ValidationError as error:
        print("Output validation failed.")
        print(error.errors()[0]["type"])
