# Agent Subdirectory Rules

## When editing files here:
- Every agent file must define: system_prompt, tools[], max_tokens
- stop_reason == "tool_use" → continue loop
- stop_reason == "end_turn" → terminate (NEVER use iteration cap as primary stop)
- Coordinator must pass full context in subagent prompt — no implicit inheritance
