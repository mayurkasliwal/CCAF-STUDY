import time
import anthropic
from dotenv import load_dotenv

load_dotenv()
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

# ══════════════════════════════════════════════════════
# BATCH API TEST
# Sends multiple requests in one batch — 50% cheaper,
# async processing (up to 1 hour, max 24 hours).
#
# EXAM: Batch API is for latency-tolerant overnight jobs.
#       Use synchronous API for pre-merge / real-time checks.
# ══════════════════════════════════════════════════════

client = anthropic.Anthropic()

MODEL = "claude-haiku-4-5"

QUESTIONS: list[tuple[str, str]] = [
    ("q-capital",   "What is the capital of France?"),
    ("q-language",  "What programming language is known for 'batteries included'?"),
    ("q-sdk",       "In one sentence: what does stop_reason='tool_use' mean in the Anthropic SDK?"),
]


# ── Step 1: Build requests ───────────────────────────────────────────────────

def build_requests(questions: list[tuple[str, str]]) -> list[Request]:
    return [
        Request(
            custom_id=custom_id,
            params=MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=256,
                messages=[{"role": "user", "content": question}],
            ),
        )
        for custom_id, question in questions
    ]


# ── Step 2: Create batch ─────────────────────────────────────────────────────

def create_batch(requests: list[Request]) -> str:
    batch = client.messages.batches.create(requests=requests)
    print(f"\n{'='*60}")
    print(f"BATCH CREATED")
    print(f"{'='*60}")
    print(f"  Batch ID  : {batch.id}")
    print(f"  Status    : {batch.processing_status}")
    print(f"  Requests  : {len(requests)}")
    return batch.id


# ── Step 3: Poll until done ──────────────────────────────────────────────────

def wait_for_batch(batch_id: str, poll_interval_seconds: int = 5) -> None:
    print(f"\nPolling every {poll_interval_seconds}s...")
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        print(
            f"  status={batch.processing_status} | "
            f"processing={counts.processing} | "
            f"succeeded={counts.succeeded} | "
            f"errored={counts.errored}"
        )
        if batch.processing_status == "ended":
            break
        time.sleep(poll_interval_seconds)


# ── Step 4: Retrieve and print results ───────────────────────────────────────

def print_results(batch_id: str) -> None:
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")

    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            msg = result.result.message
            text = next((b.text for b in msg.content if b.type == "text"), "")
            print(f"\n[{result.custom_id}]")
            print(f"  stop_reason : {msg.stop_reason}")
            print(f"  tokens      : in={msg.usage.input_tokens} out={msg.usage.output_tokens}")
            print(f"  answer      : {text.strip()}")

        elif result.result.type == "errored":
            error = result.result.error
            print(f"\n[{result.custom_id}] ERROR: {error.type}")
            # EXAM: invalid_request → fix and resubmit; server_error → safe to retry
            if error.type == "invalid_request":
                print("  → invalid_request: fix the request before resubmitting")
            else:
                print("  → server_error: safe to retry")

        elif result.result.type == "expired":
            print(f"\n[{result.custom_id}] EXPIRED — batch ran > 24h, resubmit")

        elif result.result.type == "canceled":
            print(f"\n[{result.custom_id}] CANCELED")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    requests = build_requests(QUESTIONS)
    batch_id = create_batch(requests)
    wait_for_batch(batch_id, poll_interval_seconds=5)
    print_results(batch_id)

    print(f"\n{'='*60}")
    print("EXAM CHEAT SHEET — Batch API")
    print(f"{'='*60}")
    print("""
When to use:
  Batch API  → latency-tolerant, overnight jobs, 50% cheaper
  Sync API   → pre-merge checks, real-time, user-facing

Key facts:
  - Up to 100,000 requests or 256 MB per batch
  - Most complete within 1 hour; max 24 hours
  - Results available for 29 days after creation

Result types:
  succeeded  → result.result.message (normal Message object)
  errored    → result.result.error.type
               "invalid_request" → fix and resubmit
               "server_error"    → safe to retry
  canceled   → batch was manually canceled
  expired    → batch ran > 24h, resubmit

TRAP: Batch API is async — do NOT poll every second.
      Use a reasonable interval (30-60s for real workloads).
      Here we use 5s to demo quickly.
""")
