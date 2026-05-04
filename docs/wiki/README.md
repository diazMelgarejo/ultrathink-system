# orama-system — Knowledge Wiki

> **TL;DR for agents:** Read `docs/LESSONS.md` for the session log. Read pages here for deep dives.
> For quick behavioral rules: **[SKILL.md →](../../SKILL.md)**

This wiki organizes hard-won lessons by topic. Each page contains root cause, exact fix, verification commands, and prevention rules. It is derived from the session log in [docs/LESSONS.md](../LESSONS.md) and the companion [Perplexity-Tools wiki](https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/docs/wiki/README.md).

---

## Index

| # | Page | TL;DR |
| --- | --- | --- |
| 01 | [CI Dependencies](01-ci-deps.md) | Never swap `pip install pkg...` for `.[extras]` without auditing every dropped package |
| 02 | [Idempotent Installs](02-idempotent-installs.md) | `npm install -g` does not guarantee execute bits; `capture_output=True` hides install failures |
| 03 | [Device Identity & GPU Recovery](03-device-identity.md) | One role per physical device; 30s crash recovery cooldown mandatory |
| 04 | [Gateway Discovery](04-gateway-discovery.md) | Probe before install; commandeer a running gateway rather than starting a duplicate |
| 05 | [Bulk Sed Safety](05-bulk-sed-safety.md) | `grep -rn` every pattern before running bulk `sed`; scope import renames to `.py` only |
| 06 | [Multi-Agent Collaboration](06-multi-agent-collab.md) | Version registry, scope claims, orphan branch recovery, no LAN IPs in source defaults |
| 07 | [Startup & IP Detection](07-startup-ip-detection.md) | stdin deadlock root cause, `load_dotenv()` placement, concurrent asyncio probing |
| 08 | [Git Hygiene & Branching](08-git-hygiene-and-branching.md) | Clean-lineage commit identity guardrails and branch safety protocol |
| 09 | [Policy Fail-Closed + Checklist](09-policy-fail-closed-and-checklist.md) | Enforce hardware policy fail-closed behavior and run consolidated verification after each priority block |

---

## How to Add a Lesson

1. Append the session entry to `docs/LESSONS.md` (short, dated, agent-tagged)
2. If the lesson is important enough for a wiki page, create `docs/wiki/NN-topic.md` following this template:

```markdown
# NN. Topic Title

**TL;DR:** One sentence.

---

## Root Cause
...

## Fix
...

## Verification
...

## Rules
...

## Related
- [Session log entry](../LESSONS.md#anchor)
- [Companion repo lesson](https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/docs/wiki/README.md)
```

3. Add a row to the index table above
4. Add a `→ [wiki/NN-topic.md](wiki/NN-topic.md)` link at the bottom of the LESSONS.md entry

---

## Cross-Repo Lessons

Some lessons span both repos. The canonical entry lives in the repo where the bug was fixed; a cross-reference note appears in the companion repo's LESSONS.md.

| Session | UTS Lesson | PT Lesson |
| --- | --- | --- |
| 2026-04-07 | [Idempotent Installs](02-idempotent-installs.md) | [same — shared commits](https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/docs/wiki/02-idempotent-installs.md) |
| 2026-04-13 | [Startup IP Detection](07-startup-ip-detection.md) | [same topic, PT side](https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/docs/wiki/06-startup-ip-detection.md) |
