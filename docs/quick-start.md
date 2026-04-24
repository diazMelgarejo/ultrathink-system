# Quick Start

## 5 Minutes to Your First ultrathink Task

### 1. Install

```bash
./install.sh
```

### 2. Activate in Claude

```
ultrathink this
```

or

```
Apply The ὅραμα System to: [your task]
Optimize for: reliability
```

### 3. Create a Task Plan

```bash
./bin/orama-system/scripts/create_task_plan.sh "Build my feature"
```

### 4. Build It

Work through the 5 stages. Claude will guide you.

### 5. Verify Before Done

```bash
python bin/orama-system/scripts/verify_before_done.py --task "Build my feature"
```

### 6. Capture Lessons

```bash
python bin/orama-system/scripts/capture_lesson.py
```

---

## Common Commands

| What you want | Command |
|--------------|---------|
| Create task plan | `./scripts/create_task_plan.sh "Task name"` |
| Verify completion | `python scripts/verify_before_done.py` |
| Capture a lesson | `python scripts/capture_lesson.py` |
| Review lessons | `python scripts/capture_lesson.py --review` |
| Stats on mistakes | `python scripts/capture_lesson.py --stats` |

---

## Trigger Phrases

These phrases automatically activate The ὅραμα System:

| Phrase | What happens |
|--------|-------------|
| `ultrathink this` | Full 5-stage process |
| `apply the system` | Full 5-stage process |
| `architect [X]` | Stage 2 focus |
| `elegant solution for [X]` | Stages 3+5 emphasis |
| `verify before done` | Stage 4 verification |
| `production-ready [X]` | All stages, high standards |
