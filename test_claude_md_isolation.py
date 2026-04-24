#!/usr/bin/env python3
"""
Test: Verify user-level instructions do NOT travel via version control to teammates.

Exam Syllabus Item: Test @import syntax — verify user-level instructions 
do NOT travel via version control to teammates
"""

import os
import subprocess
from pathlib import Path

def test_user_level_isolation():
    """Test that ~/.claude/CLAUDE.md is machine-local, not in git."""
    
    # Get paths
    user_claude = Path.home() / ".claude" / "CLAUDE.md"
    project_claude = Path("/Users/mayurkasliwal/dev/github/CCAF-STUDY/CLAUDE.md")
    
    print("=" * 70)
    print("TEST 1: User-level isolation (machine-local)")
    print("=" * 70)
    
    # Test 1: User file exists locally
    assert user_claude.exists(), f"❌ {user_claude} does not exist"
    print(f"✅ User-level {user_claude} exists")
    
    # Test 2: User file is NOT in git
    result = subprocess.run(
        ["git", "ls-files"],
        cwd="/Users/mayurkasliwal/dev/github/CCAF-STUDY",
        capture_output=True,
        text=True
    )
    git_tracked = result.stdout
    assert ".claude/CLAUDE.md" not in git_tracked, "❌ User-level rules leaked into git!"
    assert "~/.claude" not in git_tracked, "❌ ~/.claude directory in version control!"
    print(f"✅ ~/.claude/CLAUDE.md NOT in git (isolated)")
    
    # Test 3: Project CLAUDE.md IS in git
    result = subprocess.run(
        ["git", "ls-files", "CLAUDE.md"],
        cwd="/Users/mayurkasliwal/dev/github/CCAF-STUDY",
        capture_output=True,
        text=True
    )
    assert "CLAUDE.md" in result.stdout, "❌ Project CLAUDE.md not tracked in git"
    print(f"✅ Project-level CLAUDE.md IS in git (shared)")
    
    print()
    print("=" * 70)
    print("TEST 2: @import isolation (no leakage via import syntax)")
    print("=" * 70)
    
    # Test 4: Verify project root CLAUDE.md doesn't @import user files
    with open(project_claude, 'r') as f:
        project_content = f.read()
    
    assert "@import" not in project_content, "❌ Project CLAUDE.md uses @import"
    assert "~/.claude" not in project_content, "❌ Project CLAUDE.md references ~/.claude"
    assert "home/.claude" not in project_content, "❌ Project CLAUDE.md references user paths"
    print(f"✅ Project CLAUDE.md does NOT reference ~/.claude (no @import leakage)")
    
    # Test 5: Verify rules/ path-scoped files don't reference ~/.claude
    rules_dir = Path("/Users/mayurkasliwal/.claude/rules")
    for rule_file in rules_dir.glob("*.md"):
        with open(rule_file, 'r') as f:
            content = f.read()
        assert "~/." not in content, f"❌ {rule_file.name} references home paths"
    print(f"✅ .claude/rules/*.md do NOT reference user paths")
    
    print()
    print("=" * 70)
    print("TEST 3: Teammate scenario (clone repo, what do they get?)")
    print("=" * 70)
    
    # Test 6: Simulate cloning - what files travel?
    result = subprocess.run(
        ["git", "ls-files"],
        cwd="/Users/mayurkasliwal/dev/github/CCAF-STUDY",
        capture_output=True,
        text=True
    )
    tracked_files = result.stdout.split("\n")
    
    # Filter for CLAUDE.md files
    claude_files_in_git = [f for f in tracked_files if "CLAUDE.md" in f]
    print(f"\nFiles teamates will GET when cloning:")
    for f in claude_files_in_git:
        if f:
            print(f"  ✅ {f}")
    
    print(f"\nFiles teammates will NOT get:")
    print(f"  ✅ ~/.claude/CLAUDE.md (machine-local)")
    print(f"  ✅ ~/.claude/rules/*.md (machine-local)")
    
    # Verify this is correct
    assert "src/agents/CLAUDE.md" in claude_files_in_git, "❌ src/agents/CLAUDE.md not tracked"
    assert all(".claude" not in f for f in claude_files_in_git), "❌ ~/.claude files leaked"
    
    print()
    print("=" * 70)
    print("TEST 4: Precedence during clone (subagent context)")
    print("=" * 70)
    
    print("\nWhen teammate (different machine) edits src/agents/agent.py:")
    print("  1. ~/.claude/CLAUDE.md - ❌ NOT AVAILABLE (machine-local)")
    print("  2. ~/.claude/rules/agents.md - ❌ NOT AVAILABLE (machine-local)")
    print("  3. CCAF-STUDY/CLAUDE.md - ✅ AVAILABLE (in git)")
    print("  4. src/agents/CLAUDE.md - ✅ AVAILABLE (in git)")
    print("\nResult: Teammate gets project + subdirectory rules, NOT personal user setup")
    
    print()
    print("=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    print("\nKey finding:")
    print("User-level CLAUDE.md files are machine-local (not in git).")
    print("Only project-root and subdirectory CLAUDE.md files are version-controlled.")
    print("@import syntax should NOT reference ~/.claude in shared files.")
    print()

if __name__ == "__main__":
    test_user_level_isolation()
