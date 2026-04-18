# 05. Bulk sed Safety — grep-First, Scope to .py Only

**TL;DR:** Always `grep -rn` a pattern and review every match before running bulk `sed`. Never apply import-rename regexes to `.md`, `.sh`, `.yaml` files — they will corrupt filename references in docs and CI scripts.

---

## Root Cause (2026-04-07)

Pattern `s|multi_agent\.\([a-z]\)|bin.\1|g` was designed for Python import statements but was applied across all text files. It matched filename strings inside READMEs and shell scripts:
- `pytest tests/test_multi_agent.py` → `pytest tests/test_bin.py` (file doesn't exist)
- CI failed: `chk_f tests/test_bin.py` — file not found

---

## Fix Pattern

```bash
# Step 1 — preview ALL matches before running sed
grep -rn "multi_agent\." --include="*.py" --include="*.md" --include="*.sh"

# Step 2 — scope to .py only
find . -name "*.py" -not -path "*/node_modules/*" -exec sed -i 's/from multi_agent\./from bin./g' {} +

# Step 3 — verify no filename strings were corrupted
find . -name "test_bin.py" 2>/dev/null  # should be empty if test file is actually test_multi_agent.py
```

---

## Rules

1. **`grep -rn` before any bulk `sed`** — preview every match; abort if any match is a filename or path to an existing file
2. **Scope module-import patterns to `.py` files only** — never apply import-rename regexes to `.md`, `.sh`, `.yaml`, `.txt`
3. **Verify files exist** after any substitution that changes a filename-like string
4. **Keep filename strings and import module names disjoint in patterns** — use anchors like `from multi_agent\.` to avoid matching bare filename components
5. **CI catches broken references** but catching pre-commit is cheaper

---

## Related

- [Session log 2026-04-07](../LESSONS.md#2026-04-07--claude--bulk-sed-safety-check-before-editing--look-for-missing-files)
- Commit: `0364098` (UTS) — fix(tests): restore test filenames broken by over-eager multi_agent sed
