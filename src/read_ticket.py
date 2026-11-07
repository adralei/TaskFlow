
import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "tickets.json"
)


def get_ticket(ticket_id: str):
    with DATA_FILE.open("r", encoding="utf-8") as file:
        tickets = json.load(file)

    for ticket in tickets:
        if ticket["ticket_id"] == ticket_id:
            return ticket

    return None


if __name__ == "__main__":
    ticket = get_ticket("TCK-001")

    if ticket is None:
        print("Ticket bulunamadı.")
    else:
        print("=== TICKET DETAILS ===")
        print(f"ID: {ticket['ticket_id']}")
        print(f"Subject: {ticket['subject']}")
        print(f"Description: {ticket['description']}")
        print(f"Status: {ticket['status']}")
        print(f"Priority: {ticket['priority']}")
