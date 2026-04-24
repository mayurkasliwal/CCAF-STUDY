# CCAF Study — Anthropic SDK Practicals

> A hands-on study repo for the Claude Code AI Foundations (CCAF) exam. Each script isolates one SDK concept with inline exam notes.

## Overview

Each Python file is a self-contained lesson covering a specific Anthropic SDK pattern — from basic multi-turn chat to full agentic loops with tool use. The code is annotated with `# EXAM:` comments that call out common traps and correct API behavior.

## Architecture

```
.
├── chatbot.py              # Multi-turn conversation with history
├── streaming.py            # Streaming responses via messages.stream()
├── tools_use.py            # Agentic loop with 4 tools (banking scenario)
├── fewshots.py             # Few-shot prompting to steer tool choice
├── multiturn_msg.py        # Multi-turn message construction patterns
├── fake_websearch.py       # Tool use with a web search mock
├── chunking.py             # Fixed-size text chunking
├── semantic_chunk.py       # Semantic chunking strategy
├── max_tokens.py           # max_tokens behaviour and stop_reason handling
├── emptyhandle.py          # Handling empty/null responses
├── tool_choice.py          # tool_choice: auto / any / forced modes
├── test_claude_md_isolation.py  # CLAUDE.md scoping and git isolation tests
├── src/agents/             # Orchestrator + subagent patterns (WIP)
├── docs/
│   └── ccaf_study_tracker.html   # Study progress tracker
├── 001_prompt_evals_grader.ipynb # Prompt evaluation notebook
└── .claude/
    ├── skills/             # Custom Claude Code skills (/readme, /review)
    └── rules/              # Scoped coding rules (testing, agents, tools)
```

## Prerequisites

- Python 3.11+
- Anthropic API key

## Installation

```bash
git clone <repo-url>
cd CCAF-STUDY

python -m venv venv
source venv/bin/activate

pip install anthropic python-dotenv
```

## Configuration

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key — get it from console.anthropic.com |

Create a `.env` file in the repo root:

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

Each script runs independently:

```bash
# Basic multi-turn chatbot
python chatbot.py

# Agentic loop with tool use (banking scenario)
python tools_use.py

# Streaming responses
python streaming.py

# Few-shot prompting with tool choice steering
python fewshots.py
```

## Running Tests

```bash
# Run all test files
pytest test.py test_claude_md_isolation.py test_codeast.py -v

# Or run a specific test
python test_claude_md_isolation.py
```

## Lint

```bash
ruff check .
```

## Key Modules

| File | Concept |
|---|---|
| `chatbot.py` | `messages.create()`, conversation history, `stop_reason` |
| `tools_use.py` | Tool definitions, agentic loop, `tool_use` / `tool_result` message flow |
| `streaming.py` | `messages.stream()`, `text_stream`, `get_final_message()` |
| `fewshots.py` | Few-shot examples in system prompt, chain-of-thought before tool selection |
| `chunking.py` | Fixed-size chunking for long documents |
| `semantic_chunk.py` | Semantic boundary detection for chunking |
| `tool_choice.py` | `tool_choice` parameter: `auto`, `any`, `{"type":"tool","name":"..."}` |
| `test_claude_md_isolation.py` | CLAUDE.md scoping rules — what travels via git vs. stays machine-local |
