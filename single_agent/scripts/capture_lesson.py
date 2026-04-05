#!/usr/bin/env python3
"""
capture_lesson.py
=================
ultrathink System — Directive #3: Self-Improvement Loop

Appends a structured lesson entry to tasks/lessons.md.
Run this after ANY correction from the user or discovery of a recurring mistake.

Usage:
    python capture_lesson.py
    python capture_lesson.py --pattern "Premature Optimization" --quick
    python capture_lesson.py --review          # Review existing lessons
    python capture_lesson.py --stats           # Show mistake category stats

Philosophy:
    Mistakes aren't failures—they're learning opportunities.
    But only if you actually learn from them.
    Write rules that prevent the same mistake. Iterate until rate drops.
"""

import os
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Optional

# ─── Colour output ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# ─── Common mistake categories (for quick selection) ─────────────────────────
CATEGORIES = [
    "Premature Optimization",
    "Insufficient Error Handling",
    "Visual Verification (trusted appearance over code)",
    "Missing Edge Case",
    "Incorrect Assumption About Requirements",
    "Over-Engineering (added complexity without justification)",
    "Under-Engineering (too simple for the problem)",
    "Skipped Planning Phase",
    "Test Coverage Gap",
    "API Contract Misunderstanding",
    "Naming Clarity Issue",
    "Context Window Mismanagement",
    "Subagent Delegation Failure",
    "Verification Skipped",
    "Custom",
]

LESSON_TEMPLATE = """
## {date} — {pattern}

### What Went Wrong
{what_went_wrong}

### Root Cause
{root_cause}

### Prevention Rule
{prevention_rule}

### Verification Trigger
{verification_trigger}

### Applied To
{applied_to}

### Examples
✅ **Good**: {good_example}
❌ **Bad**: {bad_example}

---
"""

# ─── Helpers ─────────────────────────────────────────────────────────────────

def find_lessons_file(start_dir: Path) -> Path:
    """Walk up the directory tree to find tasks/lessons.md."""
    current = start_dir
    for _ in range(5):
        candidate = current / "tasks" / "lessons.md"
        if candidate.exists():
            return candidate
        current = current.parent
    # Default: create in cwd
    target = start_dir / "tasks" / "lessons.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text(_lessons_header())
    return target


def _lessons_header() -> str:
    return """# Lessons Learned — Self-Improvement Log
**ultrathink System — Directive #3**

This file is the institutional memory of this project.
Every lesson written here prevents the same mistake from recurring.
Review at the start of each session.

---

"""


def prompt(label: str, hint: str = "", required: bool = True) -> str:
    """Interactive prompt with optional hint."""
    if hint:
        print(f"  {CYAN}Hint{RESET}: {hint}")
    while True:
        value = input(f"  {BLUE}{label}{RESET}: ").strip()
        if value or not required:
            return value
        print(f"  {YELLOW}(required — please enter a value){RESET}")


def select_category() -> str:
    """Interactive category selection."""
    print(f"\n  {BOLD}Select mistake category:{RESET}")
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"  {BLUE}{i:2d}{RESET}. {cat}")
    while True:
        choice = input(f"\n  Enter number (1–{len(CATEGORIES)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(CATEGORIES):
                selected = CATEGORIES[idx]
                if selected == "Custom":
                    return prompt("Custom category name")
                return selected
        except ValueError:
            pass
        print(f"  {YELLOW}Invalid choice{RESET}")


def get_lesson_stats(lessons_path: Path) -> dict:
    """Parse lessons file and return statistics."""
    if not lessons_path.exists():
        return {"total": 0, "categories": Counter()}

    content = lessons_path.read_text(encoding="utf-8")
    entries = re.findall(r"^## \d{4}-\d{2}-\d{2} — (.+)$", content, re.MULTILINE)

    # Extract categories (simplified)
    cats = Counter()
    for entry in entries:
        for cat in CATEGORIES[:-1]:  # exclude "Custom"
            if cat.lower() in entry.lower():
                cats[cat] += 1
                break
        else:
            cats["Other / Custom"] += 1

    return {"total": len(entries), "categories": cats}


# ─── Main logic ──────────────────────────────────────────────────────────────

def capture_interactive(pattern: Optional[str], lessons_path: Path) -> None:
    """Walk the user through creating a lesson entry interactively."""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  ultrathink Self-Improvement Loop — Capture Lesson{RESET}")
    print(f"  File: {lessons_path}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    # Pattern / category
    if pattern:
        print(f"  {GREEN}Pattern{RESET}: {pattern}")
    else:
        pattern = select_category()

    # Gather fields
    print()
    what = prompt(
        "What went wrong",
        hint="Specific description of the mistake — what exactly happened?"
    )
    cause = prompt(
        "Root cause",
        hint="WHY did this happen? What was misunderstood or skipped?"
    )
    rule = prompt(
        "Prevention rule",
        hint="How to avoid this in future? Write as an actionable rule."
    )
    trigger = prompt(
        "Verification trigger",
        hint="What question to ask yourself BEFORE making this mistake again?"
    )
    scope = prompt(
        "Applied to (scenarios)",
        hint="Future scenarios where this lesson applies (comma-separated)",
        required=False
    ) or "All similar tasks"
    good = prompt(
        "Good example (✅)",
        hint="What SHOULD be done instead? One sentence is fine.",
        required=False
    ) or "(add example later)"
    bad = prompt(
        "Bad example (❌)",
        hint="What was done wrong? Mirror of the good example.",
        required=False
    ) or "(add example later)"

    # Render lesson
    lesson = LESSON_TEMPLATE.format(
        date=datetime.now().strftime("%Y-%m-%d"),
        pattern=pattern,
        what_went_wrong=what,
        root_cause=cause,
        prevention_rule=rule,
        verification_trigger=trigger,
        applied_to=scope,
        good_example=good,
        bad_example=bad,
    )

    # Append to lessons file
    with lessons_path.open("a", encoding="utf-8") as f:
        f.write(lesson)

    print(f"\n  {GREEN}✓ Lesson captured:{RESET} {pattern}")
    print(f"  {GREEN}✓ Saved to:{RESET}        {lessons_path}")
    print(f"\n  {CYAN}Tip{RESET}: Review `tasks/lessons.md` at the start of your next session.")


def review_lessons(lessons_path: Path) -> None:
    """Print all lessons for review."""
    if not lessons_path.exists():
        print(f"  {YELLOW}No lessons file found at {lessons_path}{RESET}")
        return

    content = lessons_path.read_text(encoding="utf-8")
    entries = re.split(r"\n(?=## \d{4}-\d{2}-\d{2})", content)

    print(f"\n{BOLD}📚 Lessons Learned — {lessons_path}{RESET}")
    print(f"   {len([e for e in entries if e.strip().startswith('##')])} lesson(s) on record\n")

    for entry in entries:
        if entry.strip().startswith("##"):
            print(f"{BLUE}{entry[:200]}...{RESET}\n" if len(entry) > 200 else f"{entry}\n")


def show_stats(lessons_path: Path) -> None:
    """Show lesson statistics and trends."""
    stats = get_lesson_stats(lessons_path)
    print(f"\n{BOLD}📊 Self-Improvement Stats{RESET}")
    print(f"   Total lessons: {stats['total']}")
    if stats["categories"]:
        print(f"\n   By category:")
        for cat, count in stats["categories"].most_common():
            bar = "█" * count
            print(f"   {count:3d} {bar} {cat}")
    print()


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ultrathink Self-Improvement Loop — capture a lesson after a mistake"
    )
    parser.add_argument("--pattern", help="Mistake pattern name (skips category selection)")
    parser.add_argument("--quick",   action="store_true", help="Minimal prompts (pattern + rule only)")
    parser.add_argument("--review",  action="store_true", help="Review existing lessons")
    parser.add_argument("--stats",   action="store_true", help="Show lesson statistics")
    parser.add_argument("--dir",     default=".",         help="Project directory")
    args = parser.parse_args()

    project_dir  = Path(args.dir).resolve()
    lessons_path = find_lessons_file(project_dir)

    if args.review:
        review_lessons(lessons_path)
        return

    if args.stats:
        show_stats(lessons_path)
        return

    capture_interactive(pattern=args.pattern, lessons_path=lessons_path)


if __name__ == "__main__":
    main()
