---
name: ecc-sync
description: Mandatory post-merge workflow — run after any ECC Tools PR is merged into this repo.
---

# /ecc-sync — ECC Post-Merge Sync

Run this immediately after merging any ECC Tools PR.

## Steps

```bash
git pull origin main
```

Then in Claude Code:

```
/instinct-import .claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml
/instinct-status
```

Then commit:

```bash
git add -A
git commit -m "chore(ecc): post-merge instinct import sync $(date +%Y-%m-%d)"
git push origin main
```

## Related

- Lessons file: `.claude/lessons/LESSONS.md`
- Instincts YAML: `.claude/homunculus/instincts/inherited/ultrathink-system-instincts.yaml`
- Mother skill: `single_agent/SKILL.md` (load this before and after any major merge)
- Companion repo sync: run the same command in Perplexity-Tools after merging PT ECC PRs
