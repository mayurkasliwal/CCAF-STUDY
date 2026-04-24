# Project: CCAF Study Agent

## Stack
Python 3.11 | Anthropic SDK | No frameworks

## Commands
- Run: `python main.py`
- Test: `pytest tests/`
- Lint: `ruff check .`

## Rules
- Max 4-5 tools per agent (exam rule)
- Always check stop_reason before looping
- Subagents must receive context explicitly — never assume inheritance

## Architecture
- src/agents/ — orchestrator + subagents
- src/tools/ — tool definitions
- src/prompts/ — system prompts
