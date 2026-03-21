import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Say hello and confirm you are Claude."}
    ]
)

print(message.content[0].text)
print("\nstop_reason:", message.stop_reason)
print("\n--- Token Usage ---")
print("Input tokens: ", message.usage.input_tokens)
print("Output tokens:", message.usage.output_tokens)
print("Total tokens: ", message.usage.input_tokens + message.usage.output_tokens)