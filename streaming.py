import os
from anthropic import Anthropic

# EXAM: Same client, same auth — streaming is just a different method call
client = Anthropic()

def stream_chat(user_message):
    """Stream a response token by token."""
    
    # stream=True equivalent — use stream_message context manager
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",  # cheapest model
        max_tokens=1024,
        system="You are a helpful assistant. Be concise.",
        messages=[
            {"role": "user", "content": user_message}
        ]
    ) as stream:
        
        # Tokens arrive one by one — print without newline
        for text in stream.text_stream:
            print(text, end="", flush=True)
        
        # Stream is done — get the final complete message object
        final_message = stream.get_final_message()
        
        # EXAM: stop_reason still applies — same rules
        print(f"\n[stop_reason: {final_message.stop_reason}]")
        print(f"[tokens used: {final_message.usage.input_tokens} in / {final_message.usage.output_tokens} out]")

if __name__ == "__main__":
    stream_chat("Explain what an API is in 2 sentences.")
