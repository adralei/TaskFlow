
import json

from agent import (
    client,
    MODEL,
    TOOLS,
    INSTRUCTIONS,
    SESSION_TENANT_ID,
)

from tool_runner import safe_run_investigation


MAX_TOOL_CALLS = 3


def execute_tool(tool_call):
    print(f"[TOOL CALL] {tool_call.name}")

    if tool_call.name != "investigate_support_ticket":
        return {
            "success": False,
            "error": "UNKNOWN_TOOL"
        }

    try:
        arguments = json.loads(tool_call.arguments)
    except (json.JSONDecodeError, TypeError):
        arguments = {}

    result = safe_run_investigation(
        request_data=arguments,
        session_tenant_id=SESSION_TENANT_ID
    )

    output = result.model_dump(exclude_none=True)

    print(f"[TOOL RESULT] {output}")

    return output


def chat():
    previous_response_id = None

    instructions = INSTRUCTIONS + """
    Additional conversation rules:
    - If a ticket ID is missing, ask for it.
    - Use tools only when needed.
    - Do not guess missing ticket IDs.
    - Remember the current conversation context.
    - Do not repeat tool calls unnecessarily.
    - If a tool fails, do not invent its result.
    """

    print("=== TASKFLOW SUPPORT AGENT ===")
    print("Commands: /yeni, /cikis")

    while True:
        user_message = input("\nYou: ").strip()

        if user_message.lower() == "/cikis":
            print("Conversation ended.")
            break

        if user_message.lower() == "/yeni":
            previous_response_id = None
            print("New conversation started.")
            continue

        if not user_message:
            continue

        request = {
            "model": MODEL,
            "instructions": instructions,
            "input": user_message,
            "tools": TOOLS,
            "tool_choice": "auto",
            "parallel_tool_calls": False,
            "max_output_tokens": 500
        }

        if previous_response_id is not None:
            request["previous_response_id"] = (
                previous_response_id
            )

        response = client.responses.create(**request)

        tool_count = 0
        limit_reached = False

        while True:
            tool_calls = [
                item for item in response.output
                if item.type == "function_call"
            ]

            if not tool_calls:
                print("\nAgent:", response.output_text)
                previous_response_id = response.id
                break

            if tool_count + len(tool_calls) > MAX_TOOL_CALLS:
                print(
                    "\nAgent: Araç çağrısı sınırına ulaşıldı. "
                    "İnceleme güvenli şekilde durduruldu."
                )
                previous_response_id = None
                limit_reached = True
                break

            tool_outputs = []

            for tool_call in tool_calls:
                tool_count += 1

                output = execute_tool(tool_call)

                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": json.dumps(
                        output,
                        ensure_ascii=False
                    )
                })

            response = client.responses.create(
                model=MODEL,
                instructions=instructions,
                previous_response_id=response.id,
                input=tool_outputs,
                tools=TOOLS,
                tool_choice="auto",
                parallel_tool_calls=False,
                max_output_tokens=500
            )

        if limit_reached:
            print("Yeni bir istek gönderebilirsiniz.")


if __name__ == "__main__":
    chat()
