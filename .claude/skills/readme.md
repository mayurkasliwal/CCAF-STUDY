# Skill: Repo Analysis & README Generator

When generating a README, always:

## Step 1 — Discover repo structure

- List all top-level directories and files
- Identify language/framework from: package.json, pyproject.toml, requirements.txt, go.mod, Cargo.toml, etc.
- Find the entry point(s): main.py, index.ts, app.py, cmd/, etc.
- Check for existing docs: README*, docs/, CHANGELOG*, CONTRIBUTING*

## Step 2 — Analyze the codebase

- Read the entry point and primary source directories
- Identify: purpose of the project, key modules/packages, public API surface
- Find all environment variables (scan for os.environ, process.env, dotenv)
- Find CLI commands or scripts (Makefile, scripts/ in package.json, etc.)
- Identify test framework and how to run tests

## Step 3 — Generate README.md

Write a README.md to the repo root with these sections (omit any that don't apply):

```
# <Project Name>

> One-line description of what this project does and who it's for.

## Overview
## Architecture
## Prerequisites
## Installation
## Configuration  ← table: name | required | default | description
## Usage
## Running Tests
## Key Modules
## Contributing
## License
```

## Rules

- Do NOT invent features not evidenced in the code
- Omit sections with no evidence rather than guessing
- Use fenced code blocks for all shell commands
- If README.md already exists, update only stale sections — preserve human-written content
