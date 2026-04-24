import anthropic
import json

# Initialize client
client = anthropic.Anthropic()

# Define the web search tool using JSON schema
tools = [
    {
        "name": "web_search",
        "description": "Search the web for current information on a topic",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up"
                }
            },
            "required": ["query"]
        }
    }
]

def fake_web_search(query: str) -> str:
    """
    Simulated search result — in production, replace this with
    real search API (Brave, Serper, Google Custom Search, etc.)
    """
    return json.dumps({
        "query": query,
        "results": [
            {
                "title": f"Result for: {query}",
                "snippet": f"This is a simulated search result for '{query}'. In production, use a real search API.",
                "url": "https://example.com"
            }
        ]
    })

def run_search_agent(user_question: str):
    """
    Agentic loop:
    - If Claude wants to search → execute search → feed result back
    - If Claude is done → print final answer
    """
    print(f"\nUser: {user_question}")
    print("-" * 50)

    messages = [{"role": "user", "content": user_question}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        print(f"[stop_reason: {response.stop_reason}]")

        # EXAM: stop_reason == "end_turn" → Claude is done, no tool needed
        if response.stop_reason == "end_turn":
            final_text = next(
                block.text for block in response.content
                if hasattr(block, "text")
            )
            print(f"\nClaude: {final_text}")
            break

        # EXAM: stop_reason == "tool_use" → execute the tool, continue loop
        if response.stop_reason == "tool_use":

            # Find the tool_use block
            tool_use_block = next(
                block for block in response.content
                if block.type == "tool_use"
            )

            tool_name = tool_use_block.name
            tool_input = tool_use_block.input
            tool_use_id = tool_use_block.id

            print(f"[tool called: {tool_name}({tool_input})]")

            # Execute the tool
            if tool_name == "web_search":
                result = fake_web_search(tool_input["query"])

            # Append assistant response + tool result back to messages
            # EXAM: this is how you feed tool results back to Claude
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,  # must match tool_use block id
                        "content": result
                    }
                ]
            })

# ─── Run it ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_search_agent("What is the latest version of Python?")
# ```

# ---

# **Expected output:**
# ```
# User: What is the latest version of Python?
# --------------------------------------------------
# [stop_reason: tool_use]
# [tool called: web_search({'query': 'latest Python version 2024'})]
# [stop_reason: end_turn]

# Claude: Based on the search results, the latest version of Python is...
# ```

# ---

# **The agentic loop — memorize this pattern:**
# ```
# send message
#     ↓
# stop_reason == "tool_use"  → execute tool → append result → loop again
# stop_reason == "end_turn"  → print answer → break