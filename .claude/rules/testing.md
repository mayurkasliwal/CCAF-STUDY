---
paths: ["**/*.test.tsx"]
---

# Testing Rules
- Use pytest fixtures for common setup
- Mock all external API calls (no live Anthropic API in tests)
- Test coverage minimum: 80% for utilities, 60% for integration
- Use descriptive test names: test_<function>_<scenario>_<expected>
