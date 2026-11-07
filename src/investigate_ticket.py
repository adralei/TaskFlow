
from read_ticket import get_ticket
from inspect_account import get_account, get_plan


def investigate_ticket(
    ticket_id: str,
    session_tenant_id: str
):
    ticket = get_ticket(ticket_id)

    if ticket is None:
        return {
            "success": False,
            "error": "TICKET_NOT_FOUND"
        }

    # Trusted session ile ticket tenant kontrolü
    if ticket["tenant_id"] != session_tenant_id:
        return {
            "success": False,
            "error": "ACCESS_DENIED"
        }

    # Hesap sadece izin verilen tenant üzerinden okunur
    account = get_account(session_tenant_id)

    if account is None:
        return {
            "success": False,
            "error": "ACCOUNT_NOT_FOUND"
        }

    plan = get_plan(account["plan_id"])

    if plan is None:
        return {
            "success": False,
            "error": "PLAN_NOT_FOUND"
        }

    limit_reached = (
        account["member_count"] >= plan["max_members"]
    )

    return {
        "success": True,
        "ticket_id": ticket["ticket_id"],
        "subject": ticket["subject"],
        "status": ticket["status"],
        "priority": ticket["priority"],
        "workspace": account["workspace_name"],
        "plan": plan["name"],
        "member_count": account["member_count"],
        "max_members": plan["max_members"],
        "member_limit_reached": limit_reached
    }


if __name__ == "__main__":
    print("=== AUTHORIZED REQUEST ===")

    result = investigate_ticket(
        ticket_id="TCK-001",
        session_tenant_id="tenant-001"
    )

    for key, value in result.items():
        print(f"{key}: {value}")

    print("\n=== UNAUTHORIZED REQUEST ===")

    result = investigate_ticket(
        ticket_id="TCK-001",
        session_tenant_id="tenant-002"
    )

    for key, value in result.items():
        print(f"{key}: {value}")
