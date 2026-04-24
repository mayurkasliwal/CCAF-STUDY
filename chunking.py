import re
import anthropic
from dotenv import load_dotenv
load_dotenv()

client = anthropic.Anthropic()

# ─── Sample long text to chunk ────────────────────────────────────────────
# Using a realistic document — like what you'd see in exam scenarios

TEXT = """
# Customer Support Guidelines

## Introduction
Welcome to our customer support handbook. This document outlines the procedures 
and best practices for handling customer inquiries. Every support agent must read 
and understand these guidelines before starting their role.

## Handling Refunds
Refunds must be processed within 48 hours of a customer request. Agents should 
verify the order ID before initiating any refund. Refunds above $500 require 
manager approval. Always send a confirmation email after processing. Document 
every refund in the ticketing system.

## Escalation Policy
If a customer is unsatisfied after two attempts to resolve the issue, escalate 
to a senior agent. Senior agents have authority to offer discounts up to 20%. 
If the senior agent cannot resolve it, escalate to the manager. Managers can 
approve full refunds and account credits. Always inform the customer about 
escalation timelines.

## Communication Standards
Always greet customers by name. Use professional language at all times. 
Avoid technical jargon unless the customer is technically proficient. 
Response time must be under 2 minutes for chat, 4 hours for email. 
Always close tickets only after customer confirmation.

## Tools and Systems
Agents use three primary tools: CRM, ticketing system, and live chat platform. 
CRM holds all customer history and purchase records. The ticketing system tracks 
all open and resolved issues. Live chat platform handles real-time conversations. 
All tools must be logged into at the start of every shift.
"""

# ─── 3 Chunking strategies from your notebook ─────────────────────────────

# STRATEGY 1: Character chunking
# Splits by fixed character count with overlap
# PROS: simple, predictable size
# CONS: can cut mid-sentence, mid-word

def chunk_by_char(text, chunk_size=300, chunk_overlap=50):
    chunks = []
    start_idx = 0
    while start_idx < len(text):
        end_idx = min(start_idx + chunk_size, len(text))
        chunks.append(text[start_idx:end_idx])
        start_idx = end_idx - chunk_overlap if end_idx < len(text) else len(text)
    return chunks


# STRATEGY 2: Sentence chunking
# Splits by sentence boundaries
# PROS: preserves meaning, no mid-sentence cuts
# CONS: chunk sizes vary wildly

def chunk_by_sentence(text, max_sentences=3, overlap=1):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks = []
    start_idx = 0
    while start_idx < len(sentences):
        end_idx = min(start_idx + max_sentences, len(sentences))
        chunks.append(" ".join(sentences[start_idx:end_idx]))
        start_idx += max_sentences - overlap
        if start_idx < 0:
            start_idx = 0
    return chunks


# STRATEGY 3: Section chunking
# Splits by markdown headers (## )
# PROS: preserves full context per topic
# CONS: sections can be very large

def chunk_by_section(text):
    parts = re.split(r"\n## ", text)
    # Re-add the ## header that was removed by split
    return [parts[0]] + ["## " + p for p in parts[1:]]


# ─── Ask Claude a question using each chunking strategy ───────────────────
# This shows HOW chunking affects what Claude sees and answers

def ask_claude_with_chunks(question: str, chunks: list, strategy_name: str):
    print(f"\n{'='*60}")
    print(f"STRATEGY: {strategy_name}")
    print(f"Chunks created: {len(chunks)}")
    print(f"Avg chunk size: {sum(len(c) for c in chunks) // len(chunks)} chars")
    print(f"{'='*60}")

    # Show chunk boundaries
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ({len(chunk)} chars) ---")
        print(chunk[:100] + "..." if len(chunk) > 100 else chunk)

    # Find most relevant chunk (simple keyword match — in production use embeddings)
    question_words = set(question.lower().split())
    best_chunk = max(
        chunks,
        key=lambda c: sum(1 for w in question_words if w in c.lower())
    )

    print(f"\n>>> Most relevant chunk selected ({len(best_chunk)} chars)")
    print(f">>> Sending to Claude...")

    # Send best chunk to Claude with the question
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system="Answer questions using ONLY the provided context. Be concise.",
        messages=[{
            "role": "user",
            "content": f"Context:\n{best_chunk}\n\nQuestion: {question}"
        }]
    )

    answer = response.content[0].text
    print(f"\nClaude Answer:\n{answer}")
    return answer


# ─── Compare all 3 strategies on same question ────────────────────────────

def compare_strategies(question: str):
    print(f"\n{'#'*60}")
    print(f"QUESTION: {question}")
    print(f"{'#'*60}")

    strategies = [
        ("Character (300 chars)",  chunk_by_char(TEXT, chunk_size=300, chunk_overlap=50)),
        ("Sentence (3 sentences)", chunk_by_sentence(TEXT, max_sentences=3, overlap=1)),
        ("Section (by ## header)", chunk_by_section(TEXT)),
    ]

    results = {}
    for name, chunks in strategies:
        answer = ask_claude_with_chunks(question, chunks, name)
        results[name] = answer

    # Summary comparison
    print(f"\n{'='*60}")
    print("SUMMARY — Same question, 3 strategies:")
    print(f"{'='*60}")
    for name, answer in results.items():
        print(f"\n[{name}]")
        print(answer[:150] + "..." if len(answer) > 150 else answer)


# ─── Run it ───────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Test 1: Question that lives in one section
    compare_strategies("What is the refund policy?")

    # Test 2: Question that spans multiple sections
    compare_strategies("What tools do agents use?")
# ```

# ---

# **Expected output:**
# ```
# ############################################################
# QUESTION: What is the refund policy?
# ############################################################

# STRATEGY: Character (300 chars)
# Chunks created: 8
# Avg chunk size: 287 chars
# --- Chunk 1 (300 chars) ---
# # Customer Support Guidelines...
# --- Chunk 2 (300 chars) ---
# ...Refunds must be processed within 48 hours...

# >>> Most relevant chunk selected
# >>> Sending to Claude...
# Claude Answer: Refunds must be processed within 48 hours...

# STRATEGY: Sentence (3 sentences)
# Chunks created: 12
# Avg chunk size: 156 chars
# ...

# STRATEGY: Section (by ## header)
# Chunks created: 5
# Avg chunk size: 380 chars
# ...
# ```

# ---

# **What each strategy does to Claude's context:**

# | Strategy | Chunk size | Cuts mid-sentence? | Best for |
# |---|---|---|---|
# | Character | Fixed 300 chars | ✅ Yes — risky | Unknown docs |
# | Sentence | 3 sentences | ❌ Never | Conversational text |
# | Section | Full `##` block | ❌ Never | Structured markdown |

# ---

# **EXAM — D5 chunking rules to remember:**
# ```
# Too small chunks → Claude loses context → bad answers
# Too large chunks → wastes tokens → expensive + slow
# Overlap → prevents information loss at boundaries
# Section chunking → best when document has clear structure