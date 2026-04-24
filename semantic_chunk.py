import re
import sys
import time
import numpy as np
from sentence_transformers import SentenceTransformer
import anthropic
from dotenv import load_dotenv
load_dotenv()
client = anthropic.Anthropic()

# ─── Config ───────────────────────────────────────────────────────────────

TOP_K     = 2    # max chunks to retrieve
THRESHOLD = 0.6  # minimum similarity score — below this = irrelevant
MAX_SENTENCES_PER_CHUNK = 3
OVERLAP_SENTENCES = 1

# ─── Logger — prints every step clearly ───────────────────────────────────

def log(step: str, detail: str = "", symbol: str = "►"):
    print(f"\n{symbol} [{step}] {detail}")

def log_divider(title: str = ""):
    print(f"\n{'='*60}")
    if title:
        print(f"  {title}")
        print(f"{'='*60}")


# ─── STEP 1: Load embedding model ─────────────────────────────────────────

log_divider("STEP 1: Load Embedding Model")
log("MODEL", "Loading sentence-transformers/all-MiniLM-L6-v2")
log("INFO", "First run = download ~90MB | After = loads from local cache")
log("INFO", "Runs 100% locally on your CPU — no API calls")

start = time.time()
embedder = SentenceTransformer("all-MiniLM-L6-v2")
elapsed = round(time.time() - start, 2)

log("MODEL", f"Loaded in {elapsed}s ✅", "✓")


# ─── STEP 2: Load document ────────────────────────────────────────────────

def load_document(filepath: str) -> str:
    log_divider("STEP 2: Load Document")
    log("FILE", f"Reading: {filepath}")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        log("ERROR", f"File '{filepath}' not found", "✗")
        sys.exit(1)
    except UnicodeDecodeError:
        log("WARN", "utf-8 failed — retrying with latin-1")
        with open(filepath, "r", encoding="latin-1") as f:
            text = f.read()

    lines     = text.splitlines()
    words     = text.split()
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    log("FILE", f"Characters : {len(text)}")
    log("FILE", f"Lines      : {len(lines)}")
    log("FILE", f"Words      : {len(words)}")
    log("FILE", f"Sentences  : {len(sentences)}")
    log("FILE", "Document loaded ✅", "✓")

    return text


# ─── STEP 3: Chunk the document ───────────────────────────────────────────

def chunk_document(text: str) -> list[str]:
    log_divider("STEP 3: Chunking Document")
    log("CHUNK", f"Strategy   : sentence-based chunking")
    log("CHUNK", f"Chunk size : {MAX_SENTENCES_PER_CHUNK} sentences per chunk")
    log("CHUNK", f"Overlap    : {OVERLAP_SENTENCES} sentence(s) shared between chunks")
    log("CHUNK", "WHY overlap: prevents information loss at chunk boundaries")

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    log("CHUNK", f"Total sentences found: {len(sentences)}")

    chunks    = []
    start_idx = 0

    while start_idx < len(sentences):
        end_idx = min(start_idx + MAX_SENTENCES_PER_CHUNK, len(sentences))
        chunk   = " ".join(sentences[start_idx:end_idx])
        if chunk.strip():
            chunks.append(chunk)
        start_idx += MAX_SENTENCES_PER_CHUNK - OVERLAP_SENTENCES

    log("CHUNK", f"Total chunks created: {len(chunks)}")

    # Show first 3 chunks so user can see what they look like
    log("CHUNK", "Sample chunks (first 3):")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n    Chunk {i+1} ({len(chunk)} chars):")
        print(f"    '{chunk[:120]}{'...' if len(chunk) > 120 else ''}'")

    log("CHUNK", "Chunking complete ✅", "✓")
    return chunks


# ─── STEP 4: Embed all chunks ─────────────────────────────────────────────

def embed_document_chunks(chunks: list) -> np.ndarray:
    log_divider("STEP 4: Embedding Chunks → Vectors")
    log("EMBED", f"Converting {len(chunks)} chunks into vectors")
    log("EMBED", "Each chunk → 384 numbers representing its meaning")
    log("EMBED", "Similar meanings → similar vectors (close in space)")

    start      = time.time()
    embeddings = embedder.encode(chunks, show_progress_bar=True)
    elapsed    = round(time.time() - start, 2)

    log("EMBED", f"Embedding shape : {embeddings.shape}  ← ({len(chunks)} chunks × 384 dimensions)")
    log("EMBED", f"Time taken      : {elapsed}s")
    log("EMBED", f"Memory used     : ~{embeddings.nbytes // 1024}KB")

    # Show sample vector for first chunk
    sample = embeddings[0][:6]
    log("EMBED", f"Sample vector (first 6 of 384): {np.round(sample, 4).tolist()}")
    log("EMBED", "Embedding complete ✅", "✓")

    return embeddings


# ─── Cosine similarity ────────────────────────────────────────────────────

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom != 0 else 0.0


# ─── STEP 5: Retrieve relevant chunks ────────────────────────────────────

def retrieve(
    question:   str,
    chunks:     list,
    embeddings: np.ndarray
) -> list[dict]:

    log_divider("STEP 5: Semantic Retrieval")
    log("QUERY", f"Question: '{question}'")

    # Embed the question using same model
    log("EMBED", "Embedding question → vector...")
    q_vec = embedder.encode([question])[0]
    log("EMBED", f"Question vector (first 6 of 384): {np.round(q_vec[:6], 4).tolist()}")

    # Score every chunk
    log("SCORE", f"Comparing question vector vs {len(chunks)} chunk vectors...")
    scores = []
    for i, chunk_vec in enumerate(embeddings):
        score = cosine_similarity(q_vec, chunk_vec)
        scores.append({
            "idx":   i,
            "chunk": chunks[i],
            "score": round(score, 4)
        })

    # Sort by score
    scores.sort(key=lambda x: x["score"], reverse=True)

    # Show ALL scores so user sees the full ranking
    log("SCORE", "All chunks ranked by similarity score:")
    for i, s in enumerate(scores):
        bar    = "█" * int(s["score"] * 20)
        marker = " ← ABOVE THRESHOLD ✅" if s["score"] >= THRESHOLD else " ← BELOW THRESHOLD ❌"
        print(f"    [{i+1}] score={s['score']} {bar}{marker}")
        print(f"         '{s['chunk'][:80]}...'")

    # Apply threshold filter
    log("FILTER", f"Threshold : {THRESHOLD} — dropping chunks below this score")
    filtered = [s for s in scores if s["score"] >= THRESHOLD]
    dropped  = len(scores) - len(filtered)

    log("FILTER", f"Kept    : {len(filtered)} chunks above threshold")
    log("FILTER", f"Dropped : {dropped} chunks below threshold")

    if not filtered:
        log("FILTER", "⚠️  No chunks above threshold — question may be out of scope", "⚠")
        return []

    # Apply top_k
    result = filtered[:TOP_K]
    log("RESULT", f"Top {TOP_K} chunks selected for Claude:")
    for i, r in enumerate(result):
        print(f"\n    [{i+1}] score={r['score']}")
        print(f"         '{r['chunk'][:120]}...'")

    log("RETRIEVAL", "Retrieval complete ✅", "✓")
    return result


# ─── STEP 6: Ask Claude ───────────────────────────────────────────────────

def ask_claude(question: str, top_chunks: list) -> str:
    log_divider("STEP 6: Ask Claude")

    if not top_chunks:
        answer = "I could not find relevant information in the document for that question."
        log("CLAUDE", f"Skipping API call — no relevant chunks found")
        print(f"\n  Claude: {answer}")
        return answer

    context = "\n\n".join(r["chunk"] for r in top_chunks)
    total_chars = len(context)

    log("CONTEXT", f"Sending {len(top_chunks)} chunks to Claude ({total_chars} chars)")
    log("CONTEXT", "WHY not full doc: saves tokens, reduces noise, stays within limits")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system="Answer using ONLY the context provided. Be concise and direct. If the answer is not in the context, say so.",
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}"
        }]
    )

    answer      = response.content[0].text
    stop_reason = response.stop_reason
    in_tokens   = response.usage.input_tokens
    out_tokens  = response.usage.output_tokens

    log("CLAUDE", f"stop_reason  : {stop_reason}")
    log("CLAUDE", f"Tokens used  : {in_tokens} in / {out_tokens} out")
    log("CLAUDE", f"Answer:")
    print(f"\n  {answer}")
    log("CLAUDE", "Claude response complete ✅", "✓")

    return answer


# ─── Generate suggested questions ────────────────────────────────────────

def generate_suggestions(text: str, num: int = 5) -> list[str]:
    log_divider("Generating Suggested Questions")
    log("SUGGEST", f"Sending document sample to Claude to generate {num} questions")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system="Generate questions a user might ask about the document. Return ONLY a numbered list. No preamble.",
        messages=[{
            "role": "user",
            "content": f"Generate {num} questions about this document:\n\n{text[:2000]}"
        }]
    )

    raw       = response.content[0].text.strip()
    questions = []
    for line in raw.splitlines():
        line = line.strip()
        if line and line[0].isdigit():
            q = re.sub(r"^\d+[\.\)]\s*", "", line)
            if q:
                questions.append(q)

    log("SUGGEST", f"Generated {len(questions)} questions ✅", "✓")
    return questions


# ─── Full pipeline ────────────────────────────────────────────────────────

def run_query(question, chunks, embeddings):
    top_chunks = retrieve(question, chunks, embeddings)
    ask_claude(question, top_chunks)


# ─── Interactive loop ─────────────────────────────────────────────────────

def interactive_loop(text, chunks, embeddings):
    suggestions = generate_suggestions(text)

    print("\n" + "─"*60)
    print("SUGGESTED QUESTIONS:")
    print("─"*60)
    for i, q in enumerate(suggestions, 1):
        print(f"  {i}. {q}")
    print("─"*60)
    print("  Type a number to use a suggestion")
    print("  Type your own question")
    print("  Type 'suggest' to regenerate")
    print("  Type 'quit' to exit")
    print("─"*60)

    while True:
        user_input = input("\nYour question: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if user_input.lower() == "suggest":
            suggestions = generate_suggestions(text)
            for i, q in enumerate(suggestions, 1):
                print(f"  {i}. {q}")
            continue

        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(suggestions):
                question = suggestions[idx]
                print(f"Using: {question}")
            else:
                print(f"Enter 1–{len(suggestions)}")
                continue
        else:
            question = user_input

        run_query(question, chunks, embeddings)


# ─── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = input("Enter path to your text file: ").strip()

    text       = load_document(filepath)
    chunks     = chunk_document(text)
    embeddings = embed_document_chunks(chunks)

    interactive_loop(text, chunks, embeddings)
# ```

# ---

# **What you'll see for every question:**
# ```
# ============================================================
#   STEP 5: Semantic Retrieval
# ============================================================
# ► [QUERY] Question: 'What is the refund policy?'
# ► [EMBED] Embedding question → vector...
# ► [EMBED] Question vector (first 6 of 384): [0.023, -0.187, ...]
# ► [SCORE] Comparing question vector vs 18 chunk vectors...
# ► [SCORE] All chunks ranked by similarity score:
#     [1] score=0.7823 ████████████████ ← ABOVE THRESHOLD ✅
#          'Refunds must be processed within 48 hours...'
#     [2] score=0.6341 ████████████ ← ABOVE THRESHOLD ✅
#          'Refunds above $500 require manager approval...'
#     [3] score=0.2100 ████ ← BELOW THRESHOLD ❌
#          'Always greet customers by name...'
# ► [FILTER] Threshold : 0.3
# ► [FILTER] Kept    : 2 chunks above threshold
# ► [FILTER] Dropped : 16 chunks below threshold
# ► [RESULT] Top 2 chunks selected for Claude

# ============================================================
#   STEP 6: Ask Claude
# ============================================================
# ► [CONTEXT] Sending 2 chunks to Claude (312 chars)
# ► [CLAUDE] stop_reason  : end_turn
# ► [CLAUDE] Tokens used  : 187 in / 52 out
# ► [CLAUDE] Answer:
#   Refunds must be processed within 48 hours...