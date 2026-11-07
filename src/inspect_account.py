
import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json(filename: str):
    file_path = DATA_DIR / filename

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_account(tenant_id: str):
    accounts = load_json("accounts.json")

    for account in accounts:
        if account["tenant_id"] == tenant_id:
            return account

    return None


def get_plan(plan_id: str):
    plans = load_json("plans.json")

    for plan in plans:
        if plan["plan_id"] == plan_id:
            return plan

    return None


if __name__ == "__main__":
    account = get_account("tenant-001")

    if account is None:
        print("Account not found.")
    else:
        plan = get_plan(account["plan_id"])

        if plan is None:
            print("Plan not found.")
        else:
            print("=== ACCOUNT INSPECTION ===")
            print(f"Workspace: {account['workspace_name']}")
            print(f"Plan: {plan['name']}")
            print(f"Members: {account['member_count']}")
            print(f"Max members: {plan['max_members']}")

            limit_reached = (
                account["member_count"] >= plan["max_members"]
            )

            print(f"Member limit reached: {limit_reached}")
