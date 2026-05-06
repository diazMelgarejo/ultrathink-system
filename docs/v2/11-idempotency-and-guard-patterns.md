# 11 — Idempotency, Guard Patterns, and Single-Source Policy

> **Status**: Active | Added 2026-05-06
> **Source**: Promoted from `docs/LESSONS.md` 2026-05-06 entry — three Codex P1/P2
> findings on PR #32 distilled into reusable design rules.
> **Scope**: Applies to `perpetua-core/` kernel + `oramasys/` orchestration + every
> non-kernel module that touches the filesystem, environment, or shared policy.

These patterns are post-hoc fixes from v1.x that we are **re-implementing as
first-class design decisions in v2** rather than re-discovering them under
production crashes again.

---

## 1. Why this file exists

Three findings from Codex review of `check-recovery-gemini` (PR #32) collapsed
to two latent footguns and one cross-validator drift:

| v1 incident | Production cost (would have been) | v2 design rule |
|-------------|-----------------------------------|----------------|
| `_ensure_symlink` crashed under `set -e` when destination was a regular file | Every Mac startup aborts before any service launches | **Pattern A — 4-state guard for every fs helper** |
| `repo_hygiene.py` momentarily required `cyre`-only while `check_identity.sh` accepted `cyre`+`Codex` | Codex agent commits silently fail hygiene gate | **Pattern B — single-source policy, multi-validator consumption** |
| `ln -s` ran from caller's CWD instead of `$SCRIPT_DIR` | Symlink lands in wrong directory when script invoked by absolute path | **Pattern C — anchor every CWD-sensitive call** |

All three were caught by **Codex review**, not by local pytest, not by manual
spot-test. Single-pass single-agent review is not enough for kernel-level code.

---

## 2. Pattern A — The 4-state guard

### Rule

Every helper that mutates the filesystem (`ln -s`, `mkdir`, `mv`, `rm`, `chmod`,
`chown`, `touch`, `cp`) must **explicitly enumerate every possible state of the
target path** and return 0 from every branch. No state may fall through to
`set -e` death.

### Canonical four states for symlink-style helpers

| # | Predicate | Action | Why |
|---|-----------|--------|-----|
| 1 | `-L $link && -e $link` | `return 0` | Valid symlink already correct — true no-op |
| 2 | `-L $link && ! -e $link` | `rm + ln -s` (if target exists) else warn | Broken symlink — repair |
| 3 | `-e $link` | warn + skip (do NOT clobber) | Regular file/dir — preserve user data |
| 4 | else | `ln -s` | Empty path — safe to create |

### Reference implementation (Bash)

```bash
_ensure_symlink() {
  local link="$1" target="$2"
  if [ -L "$link" ] && [ -e "$link" ]; then
    return 0
  elif [ -L "$link" ] && [ ! -e "$link" ]; then
    if [ -e "$target" ]; then
      rm "$link"
      ln -s "$target" "$link"
    fi
  elif [ -e "$link" ]; then
    echo "WARN: $link exists as regular file/dir; skipping symlink" >&2
  else
    ln -s "$target" "$link"
  fi
}
```

### Reference implementation (Python — for `perpetua-core` plugins)

```python
from pathlib import Path

def ensure_symlink(link: Path, target: Path) -> str:
    """Idempotent symlink. Returns one of: 'noop', 'relinked', 'skipped', 'created'."""
    if link.is_symlink() and link.exists():
        return "noop"
    if link.is_symlink() and not link.exists():
        if target.exists():
            link.unlink()
            link.symlink_to(target)
            return "relinked"
        return "skipped"
    if link.exists():
        # Regular file or directory — preserve.
        return "skipped"
    link.symlink_to(target)
    return "created"
```

### Acceptance test (mandatory CI gate for any fs helper)

```python
def test_ensure_symlink_all_four_states_idempotent(tmp_path):
    target = tmp_path / "target"
    target.write_text("payload")

    # State 4 → state 1
    link = tmp_path / "fresh"
    assert ensure_symlink(link, target) == "created"
    assert ensure_symlink(link, target) == "noop"   # idempotency

    # State 3 — regular file
    regular = tmp_path / "regular"
    regular.write_text("user data")
    assert ensure_symlink(regular, target) == "skipped"
    assert regular.read_text() == "user data"       # data preserved

    # State 2 — broken symlink
    broken = tmp_path / "broken"
    broken.symlink_to(tmp_path / "nonexistent")
    assert ensure_symlink(broken, target) == "relinked"
```

Every fs helper in `perpetua-core` ships with this test pattern. **No exceptions.**

---

## 3. Pattern B — Single-source policy, multi-validator consumption

### Rule

When two or more scripts/modules both enforce the same allowlist or denylist —
identities, hardware tiers, port assignments, allowed file extensions, MCP
server names, etc. — they must read from **one canonical config file**. No
constant lists duplicated across bash and python.

### v1 example (broken)

```bash
# scripts/git/check_identity.sh
ALLOWED_IDENTITIES=(
  "cyre|Lawrence@cyre.me"
  "Codex|codex@openai.com"
)
```

```python
# scripts/review/repo_hygiene.py
APPROVED_IDENTITIES = {
    ("cyre", "Lawrence@cyre.me"),
    ("Codex", "codex@openai.com"),
}
```

These drifted under independent edits. Codex sessions silently failed hygiene
even though the gate script said OK.

### v2 design (canonical)

```yaml
# perpetua-core/config/identities.yaml
approved:
  - name: cyre
    email: Lawrence@cyre.me
    role: human-owner
  - name: Codex
    email: codex@openai.com
    role: agent
forbidden_tokens:
  - "Lawrence Melgarejo"
  - "Lawrence@bettermind.ph"
```

```python
# perpetua_core/policy/identities.py — single loader
import yaml
from pathlib import Path
from functools import lru_cache

@lru_cache
def load_approved_identities() -> set[tuple[str, str]]:
    path = Path(__file__).parent.parent.parent / "config" / "identities.yaml"
    with path.open() as f:
        cfg = yaml.safe_load(f)
    return {(e["name"], e["email"]) for e in cfg["approved"]}
```

Bash side reads the same file via `yq` or a tiny shim:

```bash
# scripts/_lib/identities.sh
load_approved_identities() {
  python3 -c "
import yaml
with open('${REPO_ROOT}/config/identities.yaml') as f:
    for e in yaml.safe_load(f)['approved']:
        print(f\"{e['name']}|{e['email']}\")
"
}
```

### Acceptance test (mandatory CI gate)

```python
def test_validators_agree_on_identity_set():
    """Bash + Python validators must read the same allowed set."""
    py_set = load_approved_identities()
    bash_out = subprocess.check_output(["bash", "scripts/_lib/identities.sh"], text=True)
    bash_set = {tuple(line.split("|")) for line in bash_out.strip().splitlines()}
    assert py_set == bash_set, "validator drift detected"
```

### Generalizes to

- Hardware policies (already in `model_hardware_policy.yml` — extend the pattern)
- Port assignments (centralize in `config/ports.yaml`)
- MCP server allowlist (`config/mcp_servers.yaml`)
- Allowed environment variable names (`config/env_schema.yaml`)
- Forbidden file patterns

**Invariant**: every constant list referenced from more than one script
must live in a config file under `perpetua-core/config/`.

---

## 4. Pattern C — CWD anchoring

### Rule

Every operation that resolves paths from `pwd` must either:
1. Use an absolute path explicitly, or
2. Run inside `(cd "$ANCHOR" && ...)` (bash) / `cwd=` keyword (Python)

Defaulting to the caller's CWD is a footgun that hides until the script is
invoked by absolute path.

### v1 example (broken)

```bash
[ -n "$_REL_NET_CONFIG" ] && _ensure_symlink "network_autoconfig.py" "$_REL_NET_CONFIG"
```

When `start.sh` was invoked as `/path/to/start.sh`, `ln -s` wrote
`network_autoconfig.py` into `$PWD`, not the repo directory. Worked in dev
because we always `cd`'d first.

### v2 design

```bash
[ -n "$_REL_NET_CONFIG" ] && (cd "$SCRIPT_DIR" && _ensure_symlink "network_autoconfig.py" "$_REL_NET_CONFIG")
```

Every `_ensure_symlink` / `mkdir` / `cp` / `mv` call wrapped in `(cd "$ANCHOR" && ...)`
or rewritten with absolute paths. No exceptions.

### Acceptance test (mandatory CI gate)

```python
def test_start_sh_works_from_unrelated_cwd(tmp_path, repo_path):
    """start.sh must produce identical filesystem effect regardless of caller CWD."""
    result = subprocess.run(
        ["bash", str(repo_path / "start.sh"), "--dry-run"],
        cwd=tmp_path,                  # invoke from elsewhere
        env={**os.environ, "DRY_RUN": "1"},
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    # Symlinks land in repo, not in tmp_path
    assert (repo_path / "network_autoconfig.py").exists()
    assert not (tmp_path / "network_autoconfig.py").exists()
```

---

## 5. How these patterns flow into v2 module specs

| Module / file | Required adoption |
|---------------|-------------------|
| `perpetua-core/perpetua_core/graph/plugins/` | Every plugin that touches fs uses Pattern A; helpers ship with the 4-state test |
| `perpetua-core/config/` | Every shared allowlist/denylist consolidated here per Pattern B |
| `oramasys/scripts/start.sh` (kernel boot) | Every fs operation wrapped per Pattern C; `--dry-run` mode for the CI test |
| `02-modules/lessons-and-skill-authoring.md` | Lessons-write helper is the canonical "Pattern A in Python" example |
| `02-modules/multi-agent-network.md` | Agent state directories use Pattern A; allowed agent IDs use Pattern B |
| `10-v1-hacks-automation-orbit.md` (Link Watcher) | The "Self-healing symlink repair during pre-flight" Satellite **MUST** use the 4-state guard from day one — see the table row in §10 §1 |

---

## 6. Multi-agent review as a first-class CI gate

### Lesson from this session

Each of the three Codex findings was reproducible only in production-ish
conditions. Local pytest did not exercise the regular-file branch. Manual
spot-test ran from inside the repo root so CWD masked the bug.

The findings came from a **second model reading the same diff with a different
prompt**. That is cheap, fast, and consistently catches things one reviewer
misses.

### v2 design rule

`oramasys` CI pipeline runs three review passes on any PR touching kernel:

1. **Self-pass** (Claude or whoever raised the PR) — explain intent, run tests
2. **Cross-model pass** (Codex or Gemini) — fresh read of diff, no shared context
3. **Synthesis pass** (Claude again or human) — reconcile findings, accept or
   reject each

Findings from pass 2 that pass 1 missed are **logged to LESSONS.md** with a
permanent entry. Patterns that appear ≥ 2 times across logs are promoted to
this file (`11-idempotency-and-guard-patterns.md`) as a new rule.

---

## 7. Acceptance criteria (post-v1.0 RC, pre-v2.0 kernel start)

Before v2.0 kernel construction begins:

- [ ] `perpetua-core/config/identities.yaml` schema agreed
- [ ] `perpetua-core/perpetua_core/policy/identities.py` shared loader designed
- [ ] Bash shim `scripts/_lib/identities.sh` design agreed
- [ ] 4-state-guard test template added to `01-kernel-spec.md` test list
- [ ] CI gate `test_validators_agree_on_*` added to `04-build-order.md` Phase 4
- [ ] CI gate `test_*_works_from_unrelated_cwd` added to `04-build-order.md` Phase 4
- [ ] Multi-agent review pipeline drafted in `04-build-order.md` Phase 4
- [ ] `10-v1-hacks-automation-orbit.md` Link Watcher row updated to reference
      Pattern A explicitly

---

## 8. Cross-references

- `docs/LESSONS.md` (2026-05-06 entry) — source incident
- PR #32 — three Codex findings (commit b7733f1)
- `docs/v2/01-kernel-spec.md` — kernel surface that adopts these patterns
- `docs/v2/04-build-order.md` — Phase 4 parity tests gate
- `docs/v2/10-v1-hacks-automation-orbit.md` — Link Watcher Satellite, Pattern A
