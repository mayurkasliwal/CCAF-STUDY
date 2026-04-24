import anthropic
from datetime import datetime

client = anthropic.Anthropic()

# ══════════════════════════════════════════════════════
# FAKE DATABASE — simulates real data in your system
# ══════════════════════════════════════════════════════

accounts = {
    "ACC001": {"name": "Rahul Sharma", "balance": 45000, "currency": "INR"},
    "ACC002": {"name": "Priya Patel",  "balance": 12500, "currency": "INR"},
}

transactions = {
    "ACC001": [
        {"date": "2026-03-18", "description": "Swiggy",        "amount": -450},
        {"date": "2026-03-17", "description": "Salary",        "amount": 85000},
        {"date": "2026-03-16", "description": "Uber",          "amount": -230},
        {"date": "2026-03-15", "description": "Netflix",       "amount": -649},
        {"date": "2026-03-14", "description": "BigBasket",     "amount": -1200},
    ],
    "ACC002": [
        {"date": "2026-03-19", "description": "Freelance",     "amount": 5000},
        {"date": "2026-03-17", "description": "Zomato",        "amount": -380},
        {"date": "2026-03-15", "description": "Electricity",   "amount": -1800},
    ]
}

upi_limits = {
    "ACC001": {"daily_limit": 100000, "used_today": 2300},
    "ACC002": {"daily_limit": 50000,  "used_today": 380},
}


# ══════════════════════════════════════════════════════
# TOOL DEFINITIONS — what Claude knows about your tools
# ══════════════════════════════════════════════════════

tools = [
    {
        "name": "get_account_balance",
        "description": "Gets current account balance and account holder name. Use this when user asks about their balance, account info, or how much money they have.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "The account ID e.g. ACC001"
                }
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "get_recent_transactions",
        "description": "Gets list of recent transactions for an account. Use when user asks about spending, recent activity, or transaction history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "The account ID"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of recent transactions to fetch. Default 5.",
                    "default": 5
                }
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "transfer_money",
        "description": "Transfers money from one account to another. Use ONLY when user explicitly asks to send or transfer money. Always confirm amount and destination before calling.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_account": {
                    "type": "string",
                    "description": "Source account ID"
                },
                "to_account": {
                    "type": "string",
                    "description": "Destination account ID"
                },
                "amount": {
                    "type": "number",
                    "description": "Amount to transfer in INR"
                },
                "note": {
                    "type": "string",
                    "description": "Payment note or description"
                }
            },
            "required": ["from_account", "to_account", "amount"]
        }
    },
    {
        "name": "check_upi_limit",
        "description": "Checks remaining UPI transfer limit for today. Use this before processing a transfer to ensure the limit is not exceeded.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "The account ID to check limits for"
                }
            },
            "required": ["account_id"]
        }
    }
]


# ══════════════════════════════════════════════════════
# REAL TOOL FUNCTIONS — your actual business logic
# ══════════════════════════════════════════════════════

def get_account_balance(account_id):
    if account_id not in accounts:
        return {"error": f"Account {account_id} not found"}
    acc = accounts[account_id]
    return {
        "account_id": account_id,
        "holder":     acc["name"],
        "balance":    acc["balance"],
        "currency":   acc["currency"]
    }


def get_recent_transactions(account_id, limit=5):
    if account_id not in transactions:
        return {"error": f"No transactions found for {account_id}"}
    txns = transactions[account_id][:limit]
    total_spent   = sum(t["amount"] for t in txns if t["amount"] < 0)
    total_received = sum(t["amount"] for t in txns if t["amount"] > 0)
    return {
        "account_id":     account_id,
        "transactions":   txns,
        "total_spent":    abs(total_spent),
        "total_received": total_received,
        "period":         f"{txns[-1]['date']} to {txns[0]['date']}"
    }


def transfer_money(from_account, to_account, amount, note=""):
    # check accounts exist
    if from_account not in accounts:
        return {"success": False, "error": f"Source account {from_account} not found"}
    if to_account not in accounts:
        return {"success": False, "error": f"Destination account {to_account} not found"}

    # check balance
    if accounts[from_account]["balance"] < amount:
        return {
            "success": False,
            "error": f"Insufficient balance. Available: {accounts[from_account]['balance']} INR"
        }

    # process transfer
    accounts[from_account]["balance"] -= amount
    accounts[to_account]["balance"]   += amount

    ref = f"TXN{datetime.now().strftime('%H%M%S')}"
    return {
        "success":          True,
        "reference":        ref,
        "from":             accounts[from_account]["name"],
        "to":               accounts[to_account]["name"],
        "amount":           amount,
        "note":             note,
        "new_balance":      accounts[from_account]["balance"]
    }


def check_upi_limit(account_id):
    if account_id not in upi_limits:
        return {"error": f"No UPI limit info for {account_id}"}
    info = upi_limits[account_id]
    remaining = info["daily_limit"] - info["used_today"]
    return {
        "account_id":  account_id,
        "daily_limit": info["daily_limit"],
        "used_today":  info["used_today"],
        "remaining":   remaining,
        "can_transfer": remaining > 0
    }


# ══════════════════════════════════════════════════════
# TOOL ROUTER — maps Claude's tool calls to functions
# ══════════════════════════════════════════════════════

def execute_tool(tool_name, tool_input):
    print(f"\n    [TOOL] {tool_name}({tool_input})")

    if tool_name == "get_account_balance":
        result = get_account_balance(tool_input["account_id"])

    elif tool_name == "get_recent_transactions":
        result = get_recent_transactions(
            tool_input["account_id"],
            tool_input.get("limit", 5)
        )

    elif tool_name == "transfer_money":
        result = transfer_money(
            tool_input["from_account"],
            tool_input["to_account"],
            tool_input["amount"],
            tool_input.get("note", "")
        )

    elif tool_name == "check_upi_limit":
        result = check_upi_limit(tool_input["account_id"])

    else:
        result = {"error": f"Unknown tool: {tool_name}"}

    print(f"    [RESULT] {result}")
    return str(result)


# ══════════════════════════════════════════════════════
# THE AGENTIC LOOP — same pattern, works for any tools
# ══════════════════════════════════════════════════════

def run_agent(user_question):
    print(f"\n{'='*60}")
    print(f"USER: {user_question}")
    print(f"{'='*60}")

    messages = [{"role": "user", "content": user_question}]

    iteration = 0

    while True:
        iteration += 1
        print(f"\n  [LOOP ITERATION {iteration}]")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )

        print(f"  stop_reason: {response.stop_reason}")

        # ── Claude is done ───────────────────────────────
        if response.stop_reason == "end_turn":
            answer = next(
                (b.text for b in response.content if hasattr(b, "text")),
                "No response"
            )
            print(f"\nCLAUDE: {answer}")
            print(f"\n  tokens used — input: {response.usage.input_tokens} "
                  f"output: {response.usage.output_tokens}")
            return answer

        # ── Claude wants tools ───────────────────────────
        elif response.stop_reason == "tool_use":

            # add Claude's response to history
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # execute every tool Claude asked for
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result
                    })

            # send all results back in one message
            messages.append({
                "role":    "user",
                "content": tool_results
            })


# ══════════════════════════════════════════════════════
# RUN 4 DIFFERENT SCENARIOS
# Watch which tools Claude picks for each question
# ══════════════════════════════════════════════════════

if __name__ == "__main__":

    # Scenario A — single tool call
    # Claude only needs get_account_balance
    run_agent(
        "What is the current balance on account ACC001?"
    )

    # Scenario B — two tool calls in sequence
    # Claude calls get_account_balance then get_recent_transactions
    run_agent(
        "Show me the balance and recent spending for account ACC002."
    )

    # Scenario C — three tool calls (safety check before transfer)
    # Claude calls check_upi_limit, get_account_balance, then transfer_money
    # Notice Claude automatically checks limits before transferring
    run_agent(
        "Transfer 5000 rupees from ACC001 to ACC002 for rent payment."
    )

    # Scenario D — Claude uses transactions to answer analytical question
    # Claude fetches data then reasons over it to give insight
    run_agent(
        "Looking at ACC001 transactions, how much did they spend on food "
        "and what percentage of their recent spending is it?"
    )
