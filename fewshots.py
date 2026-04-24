import anthropic
import json

client = anthropic.Anthropic()

# ─── Tools — intentionally similar to create ambiguity ────────────────────

tools = [
    {
        "name": "search_knowledge_base",
        "description": "Search internal company documentation, policies, procedures, and FAQs",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for internal docs"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the live internet for external, market, or general information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for web"
                }
            },
            "required": ["query"]
        }
    }
]

# ─── System prompt with 4 few-shot examples ───────────────────────────────
# EXAM: Few-shot examples live in system prompt, NOT messages array
# EXAM: Each example shows reasoning BEFORE tool choice — this is chain-of-thought

SYSTEM_PROMPT = """You are a customer support agent with access to two tools:
- search_knowledge_base: for internal company policies, procedures, product info
- web_search: for external market data, competitor info, general internet knowledge

Before choosing a tool, reason through WHY one tool is better than the other.

--- FEW-SHOT EXAMPLES ---

Example 1 (internal policy question):
User: "What is your refund policy?"
Reasoning: The user is asking about OUR refund policy — this is internal company 
information. web_search would return generic refund policies from other companies, 
not ours. search_knowledge_base is correct.
Tool: search_knowledge_base, query: "refund policy"

Example 2 (external market question):
User: "What are competitors charging for shipping?"
Reasoning: Competitor pricing is external market data — it does not exist in our 
internal docs. web_search is correct. search_knowledge_base would find nothing useful.
Tool: web_search, query: "competitor shipping pricing ecommerce 2025"

Example 3 (ambiguous — but internal wins):
User: "How long does shipping take?"
Reasoning: This could mean our shipping times OR general industry standards. 
Since the user is talking to our support agent, they want OUR shipping times. 
search_knowledge_base is correct.
Tool: search_knowledge_base, query: "shipping delivery time"

Example 4 (ambiguous — but web wins):
User: "Is 30-day returns considered standard in ecommerce?"
Reasoning: The user is asking about INDUSTRY standards, not our policy specifically.
This is external benchmarking data. web_search is correct.
Tool: web_search, query: "ecommerce standard return policy days industry"

--- END EXAMPLES ---

Always show your reasoning before selecting a tool. Follow the pattern above."""


# ─── Fake tool executors ───────────────────────────────────────────────────

def search_knowledge_base(query: str) -> str:
    # In production: query your vector DB, Confluence, Notion, etc.
    return json.dumps({
        "source": "internal_kb",
        "query": query,
        "result": f"[Internal KB result for: '{query}'] Our policy states: 30-day returns, free shipping over $50, delivery in 3-5 business days."
    })

def web_search(query: str) -> str:
    # In production: call Tavily, Brave, Serper, etc.
    return json.dumps({
        "source": "web",
        "query": query,
        "result": f"[Web result for: '{query}'] Industry data shows most ecommerce companies offer 30-day returns and $35-50 free shipping thresholds."
    })

# ─── Agentic loop ─────────────────────────────────────────────────────────
# EXAM: stop_reason == "tool_use" → execute → continue
#       stop_reason == "end_turn"  → done → break

def run_agent(user_question: str):
    print(f"\n{'='*60}")
    print(f"User: {user_question}")
    print(f"{'='*60}")

    messages = [{"role": "user", "content": user_question}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,           # few-shot examples live here
            tools=tools,
            # EXAM: tool_choice is "auto" — Claude decides based on few-shot reasoning
            tool_choice={"type": "auto"},
            messages=messages
        )

        print(f"\n[stop_reason: {response.stop_reason}]")

        # Print Claude's reasoning text (before tool call)
        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"\nClaude reasoning:\n{block.text}")

        # Done — no tool needed
        if response.stop_reason == "end_turn":
            break

        # Tool selected — execute it
        if response.stop_reason == "tool_use":
            tool_block = next(
                b for b in response.content if b.type == "tool_use"
            )

            tool_name  = tool_block.name
            tool_input = tool_block.input
            tool_id    = tool_block.id

            print(f"\n>>> Tool selected: {tool_name}")
            print(f">>> Query: {tool_input['query']}")

            # Execute the correct tool
            if tool_name == "search_knowledge_base":
                result = search_knowledge_base(tool_input["query"])
            elif tool_name == "web_search":
                result = web_search(tool_input["query"])

            print(f">>> Result: {result}")

            # Feed result back — EXAM: role must be "user", type must be "tool_result"
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result
                }]
            })

# ─── Test with ambiguous questions ────────────────────────────────────────

if __name__ == "__main__":
    
    # Should pick search_knowledge_base (internal policy)
    run_agent("What is your refund policy?")

    # Should pick web_search (external market data)
    run_agent("What are competitors charging for shipping?")

    # Ambiguous — should pick search_knowledge_base (support context = internal)
    run_agent("How long does shipping take?")

    # Ambiguous — should pick web_search (benchmarking = external)
    run_agent("Is 30-day returns considered standard in ecommerce?")
# ```

# ---

# **Expected output:**
# ```
# ============================================================
# User: What is your refund policy?
# ============================================================
# [stop_reason: tool_use]

# Claude reasoning:
# The user is asking about OUR refund policy — internal information.
# search_knowledge_base is correct, not web_search.

# >>> Tool selected: search_knowledge_base
# >>> Query: refund policy
# >>> Result: {"source": "internal_kb", "result": "30-day returns..."}

# [stop_reason: end_turn]

# Claude reasoning:
# Based on our internal documentation, our refund policy is...