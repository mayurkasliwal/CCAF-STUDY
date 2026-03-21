import anthropic

client = anthropic.Anthropic()

tools = [
    {
        "name": "get_weather",
        "description": "Gets current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_temperature",
        "description": "Gets exact temperature in celsius for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"}
            },
            "required": ["city"]
        }
    }
]


def print_result(label, response):
    print(f"\n{'='*55}")
    print(f"tool_choice : {label}")
    print(f"stop_reason : {response.stop_reason}")
    for block in response.content:
        if block.type == "tool_use":
            print(f"tool called : {block.name}")
            print(f"tool input  : {block.input}")
        elif block.type == "text":
            print(f"text reply  : {block.text}")
    print(f"input tokens : {response.usage.input_tokens}")
    print(f"output tokens: {response.usage.output_tokens}")


question = "What is the weather in Mumbai?"


# ══════════════════════════════════════════════════════
# TEST 1 — auto
# Claude decides whether to use a tool or answer directly
# ══════════════════════════════════════════════════════
print("\n>>> TEST 1: tool_choice = auto")
print("    Claude decides — may or may not call a tool")

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    tools=tools,
    tool_choice={"type": "auto"},   # ← Claude decides
    messages=[{"role": "user", "content": question}]
)
print_result("auto", response)


# ══════════════════════════════════════════════════════
# TEST 2 — any
# Claude MUST call a tool but picks which one
# ══════════════════════════════════════════════════════
print("\n>>> TEST 2: tool_choice = any")
print("    Claude MUST call a tool — picks which one itself")

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    tools=tools,
    tool_choice={"type": "any"},    # ← must call a tool
    messages=[{"role": "user", "content": question}]
)
print_result("any", response)


# ══════════════════════════════════════════════════════
# TEST 3 — forced (specific tool)
# Claude MUST call get_temperature regardless of question
# ══════════════════════════════════════════════════════
print("\n>>> TEST 3: tool_choice = forced (get_temperature)")
print("    Claude MUST call get_temperature — no choice")

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    tools=tools,
    tool_choice={"type": "tool", "name": "get_temperature"},  # ← forced
    messages=[{"role": "user", "content": question}]
)
print_result("forced → get_temperature", response)


# ══════════════════════════════════════════════════════
# TEST 4 — auto with a question that needs NO tool
# Shows that auto can return plain text
# ══════════════════════════════════════════════════════
print("\n>>> TEST 4: tool_choice = auto — question needs no tool")
print("    Claude answers directly without calling any tool")

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    tools=tools,
    tool_choice={"type": "auto"},
    messages=[{"role": "user", "content": "What is 2 + 2?"}]
)
print_result("auto (no tool needed)", response)
print(response.stop_reason)


# ══════════════════════════════════════════════════════
# SUMMARY
# ════
print(f"\n\n{'='*55}")
print("EXAM CHEAT SHEET — tool_choice")
print(f"{'='*55}")
print("""
auto   → Claude decides. May call a tool or answer in text.
         Use when: most situations, let Claude reason freely.

any    → Claude MUST call a tool. Picks which one itself.
         Use when: you need structured output guaranteed,
         don't care which tool as long as one is called.
         EXAM: guarantees stop_reason == "tool_use"

forced → Claude MUST call THIS specific tool by name.
         Use when: you need a specific tool to run first
         e.g. extract_metadata before enrichment tools.
         EXAM: {"type": "tool", "name": "tool_name_here"}

TRAP:  "auto" can return plain text — stop_reason will be
        "end_turn" not "tool_use". Never assume auto always
        calls a tool. Always check stop_reason.
""")

# **Run it:**
# ```
# python tool_choice_test.py
# ```

# **Expected output pattern:**
# ```
# TEST 1 — auto
# stop_reason : tool_use        ← Claude chose to use a tool
# tool called : get_weather

# TEST 2 — any
# stop_reason : tool_use        ← forced to use a tool
# tool called : get_weather     ← Claude picked this one

# TEST 3 — forced
# stop_reason : tool_use        ← forced to use specific tool
# tool called : get_temperature ← exactly this one, no choice

# TEST 4 — auto (2+2)
# stop_reason : end_turn        ← no tool needed, answered directly
# text reply  : 2 + 2 = 4