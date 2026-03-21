
import anthropic

client = anthropic.Anthropic()
# # Request with limited tokens
# response = client.messages.create(
#     model="claude-opus-4-6",
#     max_tokens=10,
#     messages=[{"role": "user", "content": "Explain quantum physics"}],
# )

# if response.stop_reason == "max_tokens":
#     # Response was truncated
#     print("Response was cut off at token limit")
#     # Consider making another request to continue
#     print("stop_reason:", response.stop_reason)



response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    stop_sequences=["END", "STOP"],
    messages=[{"role": "user", "content": "Generate text until you say END"}],
)

if response.stop_reason == "stop_sequence":
    print(response.content)
    print(f"Stopped at sequence: {response.stop_sequence}")    