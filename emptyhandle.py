import anthropic

client = anthropic.Anthropic()

def print_response(label, response):
    print(f"\n{'='*55}")
    print(f"TEST: {label}")
    print(f"{'='*55}")
    print(f"stop_reason  : {response.stop_reason}")
    if response.content:
        for block in response.content:
            if hasattr(block, "text"):
                print(f"text         : {block.text}")
            elif hasattr(block, "type") and block.type == "tool_use":
                print(f"tool_use     : {block.name}({block.input})")
    else:
        print("content      : !! EMPTY !!")
    print(f"input tokens : {response.usage.input_tokens}")
    print(f"output tokens: {response.usage.output_tokens}")


tools = [
    {
        "name": "calculator",
        "description": "Performs basic arithmetic",
        "input_schema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"]
                },
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["operation", "a", "b"]
        }
    }
]


# ══════════════════════════════════════════════════════
# TEST 1 — stop_reason: "tool_use" (loop must CONTINUE)
# This is the key D1 exam concept — NOT end_turn
# ══════════════════════════════════════════════════════
print("\n>>> TEST 1: First turn — Claude decides to USE a tool")

turn1_messages = [
    {"role": "user", "content": "What is 1234 + 5678? Use the calculator tool."}
]

response1 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=turn1_messages
)
print_response("Turn 1 — initial request", response1)

print(f"\n  EXAM RULE CHECK:")
print(f"  stop_reason is '{response1.stop_reason}'")
if response1.stop_reason == "tool_use":
    print(f"  → CORRECT: agentic loop must CONTINUE — execute the tool")
elif response1.stop_reason == "end_turn":
    print(f"  → loop would TERMINATE here — Claude answered without tool")


# ══════════════════════════════════════════════════════
# TEST 2 — extract tool call details from response
# ══════════════════════════════════════════════════════
print("\n>>> TEST 2: Extract tool call and simulate execution")

tool_use_block = None
for block in response1.content:
    if block.type == "tool_use":
        tool_use_block = block
        break

if tool_use_block:
    print(f"\n  Tool requested : {tool_use_block.name}")
    print(f"  Tool input     : {tool_use_block.input}")
    print(f"  Tool use ID    : {tool_use_block.id}")

    # simulate actually running the calculator
    a = tool_use_block.input["a"]
    b = tool_use_block.input["b"]
    op = tool_use_block.input["operation"]
    result = str(int(a) + int(b)) if op == "add" else "unsupported"
    print(f"  Simulated result: {a} + {b} = {result}")


# ══════════════════════════════════════════════════════
# TEST 3 — CORRECT agentic loop: append tool result
# and get final answer (stop_reason: end_turn)
# ══════════════════════════════════════════════════════
print("\n>>> TEST 3: CORRECT — return tool result, get final answer")

turn2_messages = [
    {"role": "user", "content": "What is 1234 + 5678? Use the calculator tool."},
    # append Claude's full response as assistant turn
    {"role": "assistant", "content": response1.content},
    # return the tool result — only tool_result, nothing else
    {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_use_block.id,  # must match exactly
                "content": result
            }
        ]
    }
]

response2 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=turn2_messages
)
print_response("Turn 2 — after tool result", response2)

print(f"\n  EXAM RULE CHECK:")
print(f"  stop_reason is '{response2.stop_reason}'")
if response2.stop_reason == "end_turn":
    print(f"  → CORRECT: loop TERMINATES here — Claude gave final answer")


# ══════════════════════════════════════════════════════
# TEST 4 — WRONG loop termination: checking text content
# instead of stop_reason (common exam anti-pattern)
# ══════════════════════════════════════════════════════
print("\n>>> TEST 4: ANTI-PATTERN — wrong loop termination check")

print(f"\n  WRONG way to check if loop is done:")
print(f"  if response.content[0].text:  ← checking for text")
has_text = bool(response1.content and 
                any(hasattr(b,"text") for b in response1.content))
print(f"  result = {has_text} — MISLEADING, stop_reason was '{response1.stop_reason}'")
print(f"  Loop would STOP here but tool was never executed!")

print(f"\n  CORRECT way to check:")
print(f"  if response.stop_reason == 'tool_use': continue loop")
print(f"  if response.stop_reason == 'end_turn': terminate loop")


# ══════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════
print(f"\n\n{'='*55}")
print("WHAT YOU ACTUALLY LEARNED")
print(f"{'='*55}")
print("""
1. stop_reason == "tool_use"  → tool was requested, CONTINUE loop
   stop_reason == "end_turn"  → final answer given, STOP loop

2. After getting stop_reason "tool_use":
   - Extract tool_use block from response.content
   - Execute the tool yourself
   - Append assistant response + tool_result to messages
   - Call API again — this is the agentic loop

3. tool_use_id must match EXACTLY between
   assistant tool_use block and your tool_result block

4. NEVER check response.content[0].text to decide
   if loop is done — always check stop_reason

EXAM DOMAIN: D1 Task 1.1 — Agentic loop lifecycle
""")