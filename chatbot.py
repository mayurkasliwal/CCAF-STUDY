import os
from anthropic import Anthropic

# Initialize the client
# EXAM: SDK auto-reads ANTHROPIC_API_KEY from environment — no need to pass it explicitly
client = Anthropic()

# This list holds the conversation history
# EXAM: Claude has no memory — you MUST pass full history every turn
conversation_history = []

# System prompt is a TOP-LEVEL parameter, NOT inside messages array
# TRAP: role:"system" does NOT exist in Claude API
SYSTEM_PROMPT = "You are a helpful assistant. Be concise."

def chat(user_message):
    """Send a message and get a response, maintaining conversation history."""
    
    # Step 1: Append the new user message to history
    conversation_history.append({
        "role": "user",          # EXAM: only "user" and "assistant" are valid roles
        "content": user_message
    })
    
    # Step 2: Make the API call with full history
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",  # cheapest model — saves your $10 credits
        max_tokens=1024,
        system=SYSTEM_PROMPT,               # top-level parameter
        messages=conversation_history       # full history every time
    )
    
    # Step 3: Check stop_reason
    # EXAM: "end_turn" = done. "max_tokens" = truncated, continue. "tool_use" = run tool.
    stop_reason = response.stop_reason
    print(f"[stop_reason: {stop_reason}]")
    
    # Step 4: Extract the assistant's reply
    assistant_message = response.content[0].text
    
    # Step 5: Append assistant reply to history for next turn
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })
    
    return assistant_message

def main():
    """Simple chat loop — runs until user types 'quit'."""
    print("Chat started. Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == "quit":
            print("Ending chat.")
            break
            
        if not user_input:
            continue
        
        response = chat(user_input)
        print(f"Claude: {response}\n")

if __name__ == "__main__":
    main()