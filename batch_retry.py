import time
import anthropic
from dotenv import load_dotenv
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

load_dotenv()

# ══════════════════════════════════════════════════════
# BATCH API — 10 docs, poll, resubmit failed by custom_id
# ══════════════════════════════════════════════════════

client = anthropic.Anthropic()

MODEL = "claude-haiku-4-5"

# 10 documents — mix of valid and intentionally broken requests
# custom_id is your key for tracking which item succeeded/failed
DOCUMENTS: list[dict] = [
    {"id": "doc-01", "text": "Summarise: The Eiffel Tower was built in 1889 in Paris."},
    {"id": "doc-02", "text": "Summarise: Python was created by Guido van Rossum in 1991."},
    {"id": "doc-03", "text": "Summarise: The Great Wall of China stretches over 13,000 miles."},
    {"id": "doc-04", "text": "Summarise: DNA was first described by Watson and Crick in 1953."},
    {"id": "doc-05", "text": "Summarise: The speed of light is approximately 299,792 km/s."},
    {"id": "doc-06", "text": "Summarise: Shakespeare wrote Hamlet around 1600 AD."},
    {"id": "doc-07", "text": "Summarise: The Amazon River is the largest river by discharge."},
    {"id": "doc-08", "text": "Summarise: Marie Curie won two Nobel Prizes, in Physics and Chemistry."},
    {"id": "doc-09", "text": "Summarise: The moon is about 384,400 km from Earth on average."},
    {"id": "doc-10", "text": "Summarise: Jupiter is the largest planet in the solar system."},
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def build_requests(docs: list[dict]) -> list[Request]:
    return [
        Request(
            custom_id=doc["id"],
            params=MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=128,
                messages=[{"role": "user", "content": doc["text"]}],
            ),
        )
        for doc in docs
    ]


def submit_batch(requests: list[Request]) -> str:
    batch = client.messages.batches.create(requests=requests)
    print(f"\n{'='*60}")
    print(f"BATCH SUBMITTED  id={batch.id}  count={len(requests)}")
    print(f"{'='*60}")
    return batch.id


def poll_until_done(batch_id: str, interval: int = 5) -> None:
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        c = batch.request_counts
        print(
            f"  [{batch.processing_status}] "
            f"processing={c.processing} succeeded={c.succeeded} "
            f"errored={c.errored} canceled={c.canceled} expired={c.expired}"
        )
        if batch.processing_status == "ended":
            break
        time.sleep(interval)


def collect_results(batch_id: str) -> tuple[dict[str, str], list[str]]:
    """
    Returns:
        successes  — {custom_id: answer_text}
        to_retry   — [custom_id, ...] for server_error results (safe to retry)
    """
    successes: dict[str, str] = {}
    to_retry: list[str] = []

    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id

        if result.result.type == "succeeded":
            msg = result.result.message
            text = next((b.text for b in msg.content if b.type == "text"), "")
            successes[cid] = text.strip()

        elif result.result.type == "errored":
            error_type = result.result.error.type
            if error_type == "server_error":
                # safe to retry
                to_retry.append(cid)
                print(f"  [RETRY-QUEUED]  {cid} — server_error")
            else:
                # invalid_request → fix the doc before retrying
                print(f"  [SKIP]          {cid} — invalid_request (fix doc first)")

        elif result.result.type == "expired":
            to_retry.append(cid)
            print(f"  [RETRY-QUEUED]  {cid} — expired")

        elif result.result.type == "canceled":
            print(f"  [CANCELED]      {cid}")

    return successes, to_retry


def print_successes(successes: dict[str, str]) -> None:
    print(f"\n{'='*60}")
    print(f"RESULTS ({len(successes)} succeeded)")
    print(f"{'='*60}")
    for cid, text in sorted(successes.items()):
        print(f"  [{cid}] {text}")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    all_successes: dict[str, str] = {}
    remaining_docs = DOCUMENTS.copy()
    attempt = 0
    max_attempts = 3  # guard against infinite retry loop

    while remaining_docs and attempt < max_attempts:
        attempt += 1
        print(f"\n>>> Attempt {attempt} — submitting {len(remaining_docs)} docs")

        requests = build_requests(remaining_docs)
        batch_id = submit_batch(requests)
        poll_until_done(batch_id, interval=5)

        successes, to_retry = collect_results(batch_id)
        all_successes.update(successes)

        if not to_retry:
            break

        # Build next round from only the failed custom_ids
        # EXAM: look up original doc by custom_id, not by index
        id_to_doc = {doc["id"]: doc for doc in remaining_docs}
        remaining_docs = [id_to_doc[cid] for cid in to_retry if cid in id_to_doc]
        print(f"\n  {len(remaining_docs)} docs queued for retry")

    print_successes(all_successes)

    if remaining_docs:
        print(f"\n  WARNING: {len(remaining_docs)} docs still failed after {max_attempts} attempts")
        for doc in remaining_docs:
            print(f"    {doc['id']}")

    print(f"\n{'='*60}")
    print("EXAM NOTES — retry pattern")
    print(f"{'='*60}")
    print("""
Key pattern:
  1. Track custom_id → original doc in a dict
  2. On errored results:
       server_error   → queue for retry (transient)
       invalid_request → skip, fix the doc first
       expired        → queue for retry (resubmit)
  3. Build next batch from ONLY the failed custom_ids
  4. Always cap retries (max_attempts) to avoid infinite loops
""")
