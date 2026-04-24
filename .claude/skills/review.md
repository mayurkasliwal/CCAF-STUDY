# Skill: Code Review

When reviewing code, always check in this order:

1. **Correctness** — logic errors, off-by-one, unhandled edge cases
2. **Security** — injection risks, hardcoded secrets, unsafe deserialization
3. **Agent rules compliance** — check `.claude/rules/` (stop_reason checks, max_tokens set, explicit context passing to subagents)
4. **Test coverage** — are critical paths tested? flag untested branches
5. **Style** — type hints present, no bare `except:`, no `print()` for debug

Output as a numbered list grouped by severity: BLOCKER → WARNING → SUGGESTION.
