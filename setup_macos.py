#!/usr/bin/env python3
"""
setup_macos.py
--------------
Idempotent macOS pre-flight setup for orama-system.
Safe to call on every start.sh run — every step skips itself when already done.

What it does:
  1. Create ~/.local/bin  (user-writable binary dir in PATH)
  2. Add ~/.local/bin to PATH in ~/.zshrc (if not already present)
  3. Validate and repair ~/.openclaw/openclaw.json (models arrays)
  5. Install ~/.openclaw/scripts/discover.py (LM Studio auto-discovery hub)
  6. Guard /self-discovery skill against version downgrade; announce on startup
  4. Patch ~/.alphaclaw/.../alphaclaw.js — 6 macOS compatibility fixes:
       a) git auth shim dest  → ~/.local/bin/git      (not /usr/local/bin/git)
       b) git auth shim mkdir → add mkdirSync guard
       c) git-sync shimPath   → ~/.local/bin/git      (line ~277)
       d) gog install         → ~/.local/bin/gog      (not /usr/local/bin/gog)
       e) cron setup          → macOS user crontab    (not /etc/cron.d)
       f) systemctl shim      → skip on macOS entirely

Usage:
    python setup_macos.py              # full output
    python setup_macos.py --dry-run    # show what would change, apply nothing
    python setup_macos.py --quiet      # only print fixes and warnings (not skips)
"""
from __future__ import annotations

import json, os, sys
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

# ── constants ─────────────────────────────────────────────────────────────────

HOME          = Path.home()
LOCAL_BIN     = HOME / ".local" / "bin"
ALPHACLAW_JS  = HOME / ".alphaclaw/node_modules/@chrysb/alphaclaw/bin/alphaclaw.js"
OPENCLAW_JSON = HOME / ".openclaw/openclaw.json"
MARKER_FILE   = HOME / ".alphaclaw" / ".macos_patches.json"

# alphaclaw package version this script was written for.
# If the installed version differs, patches are re-checked regardless of marker.
KNOWN_ALPHACLAW_VERSION = "0.9.3"

DRY_RUN = "--dry-run" in sys.argv
QUIET   = "--quiet"   in sys.argv

_fixes    : list[str] = []
_warnings : list[str] = []

# ── logging ───────────────────────────────────────────────────────────────────

def _log(sym: str, msg: str) -> None:
    # In quiet mode only print fixes (✓) and warnings (⚠), not skips (·)
    if QUIET and sym == "·":
        return
    print(f"  [{sym}] {msg}", flush=True)

def _skip(tag: str, detail: str = "") -> None:
    _log("·", f"skip  {tag}" + (f" — {detail}" if detail else ""))

def _applied(tag: str, detail: str = "") -> None:
    _fixes.append(tag)
    _log("✓", f"fixed {tag}" + (f" — {detail}" if detail else ""))
def _warn(tag: str, detail: str = "") -> None:
    _warnings.append(f"{tag}: {detail}" if detail else tag)
    _log("⚠", f"warn  {tag}" + (f" — {detail}" if detail else ""))

# ── helpers ───────────────────────────────────────────────────────────────────

def _write_text(path: Path, text: str) -> None:
    if not DRY_RUN:
        path.write_text(text, encoding="utf-8")

def _fetch_ollama_models(base_url: str = "http://127.0.0.1:11434") -> list[dict]:
    """Query local Ollama for currently-pulled models. Returns [] on any error."""
    try:
        with urlopen(f"{base_url}/api/tags", timeout=3) as r:
            raw = json.load(r).get("models", [])
            return [
                {
                    "id":            m["name"],
                    "name":          f"Mac Ollama — {m['name']}",
                    "contextWindow": 32768,
                    "maxTokens":     8192,
                    "cost":          {"input": 0, "output": 0},
                }
                for m in raw
            ]
    except Exception:
        return []

_DEFAULT_OLLAMA_MAC_MODELS = [
    {"id": "qwen3.5-local:latest",    "name": "Mac Ollama — qwen3.5-local",
     "contextWindow": 32768, "maxTokens": 8192, "cost": {"input": 0, "output": 0}},
    {"id": "qwen2.5-coder:7b",        "name": "Mac Ollama — qwen2.5-coder:7b",
     "contextWindow": 32768, "maxTokens": 8192, "cost": {"input": 0, "output": 0}},
    {"id": "nomic-embed-text:latest", "name": "Mac Ollama — nomic-embed-text",
     "contextWindow": 8192,  "maxTokens": 512,  "cost": {"input": 0, "output": 0}},
]
_DEFAULT_OLLAMA_WIN_MODELS = [
    {"id": "placeholder",
     "name": "Win Ollama — placeholder (update when Win Ollama is running)",
     "contextWindow": 32768, "maxTokens": 8192, "cost": {"input": 0, "output": 0}},
]

# ── step 1: ~/.local/bin ──────────────────────────────────────────────────────

def step_local_bin() -> None:
    if LOCAL_BIN.is_dir():
        _skip("~/.local/bin")
        return
    if not DRY_RUN:
        LOCAL_BIN.mkdir(parents=True, exist_ok=True)
    _applied("~/.local/bin", "created user-writable bin dir")

# ── step 2: PATH entry ────────────────────────────────────────────────────────

def step_path_entry() -> None:
    ENTRY   = 'export PATH="$HOME/.local/bin:$PATH"'
    COMMENT = "# ultrathink/openclaw — user-writable binaries (added by setup_macos.py)"
    if str(LOCAL_BIN) in os.environ.get("PATH", ""):
        _skip("~/.local/bin in active PATH")
        return
    for rc in [HOME / ".zshrc", HOME / ".zprofile", HOME / ".bashrc"]:
        if rc.exists() and ENTRY in rc.read_text(encoding="utf-8"):
            _skip(f"~/.local/bin PATH entry ({rc.name})")
            return
    target   = HOME / ".zshrc"
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    _write_text(target, existing + f"\n{COMMENT}\n{ENTRY}\n")
    _applied("PATH entry", "added ~/.local/bin to ~/.zshrc — run: source ~/.zshrc")

# ── step 3: openclaw.json ─────────────────────────────────────────────────────

def step_openclaw_json() -> None:
    if not OPENCLAW_JSON.exists():
        _warn("openclaw.json", f"not found at {OPENCLAW_JSON}")
        return
    try:
        cfg = json.loads(OPENCLAW_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _warn("openclaw.json", f"JSON parse error: {exc}")
        return

    providers = cfg.get("models", {}).get("providers", {})
    changed   = False

    for key, fallback_models, ollama_url in [
        ("ollama-mac", _DEFAULT_OLLAMA_MAC_MODELS, "http://127.0.0.1:11434"),
        ("ollama-win", _DEFAULT_OLLAMA_WIN_MODELS, None),
    ]:
        p = providers.get(key)
        if p is None:
            _warn(f"openclaw.json {key}", "provider entry missing — skipping")
            continue
        if isinstance(p.get("models"), list) and len(p["models"]) > 0:
            _skip(f"openclaw.json {key}.models")
            continue
        # Determine models: query live Ollama or fall back to defaults
        models = []
        if ollama_url:
            models = _fetch_ollama_models(ollama_url)
        if not models:
            models = fallback_models
        if not DRY_RUN:
            providers[key]["models"] = models
            cfg.setdefault("models", {}).setdefault("providers", {})[key] = providers[key]
        changed = True
        source = "from live Ollama" if (ollama_url and models != fallback_models) else "defaults"
        _applied(f"openclaw.json {key}.models", f"added {len(models)} model(s) {source}")

    if changed and not DRY_RUN:
        _write_text(OPENCLAW_JSON, json.dumps(cfg, indent=2) + "\n")

# ── step 4: alphaclaw.js patches ──────────────────────────────────────────────
#
# Each patch is a dict with:
#   name    — human-readable identifier (used in marker file)
#   detect  — substring present ONLY in the already-patched version (idempotency check)
#   old     — substring present ONLY in the original (unpatched) npm version
#   new     — replacement for old  (exact text from the current patched file)
#
# Workflow per patch:
#   detect in content  →  skip (already patched)
#   old    in content  →  replace old→new, mark fixed
#   neither            →  warn (unknown npm version or re-formatted source)

# ─── Patch A: git auth shim destination ──────────────────────────────────────
_P_GIT_DEST = {
    "name":   "git-shim-dest",
    "detect": 'const gitShimDest = path.join(os.homedir(), ".local", "bin", "git");',
    "old":    '  const gitShimDest = "/usr/local/bin/git";',
    "new":    (
        '  // Use ~/.local/bin/git (user-writable, already precedes /usr/local/bin in PATH)\n'
        '  const gitShimDest = path.join(os.homedir(), ".local", "bin", "git");'
    ),
}

# ─── Patch B: git auth shim — add mkdirSync before writeFileSync ─────────────
_P_GIT_MKDIR = {
    "name":   "git-shim-mkdirSync",
    "detect": 'fs.mkdirSync(path.dirname(gitShimDest), { recursive: true });',
    "old":    '    fs.writeFileSync(gitShimDest, gitShimContent, { mode: 0o755 });',
    "new":    (
        '    fs.mkdirSync(path.dirname(gitShimDest), { recursive: true });\n'
        '    fs.writeFileSync(gitShimDest, gitShimContent, { mode: 0o755 });'
    ),
}

# ─── Patch C: git-sync shimPath (line ~277) ───────────────────────────────────
_P_GIT_SHIMPATH = {
    "name":   "git-sync-shimpath",
    "detect": 'shimPath: path.join(os.homedir(), ".local", "bin", "git"),',
    "old":    '    shimPath: "/usr/local/bin/git",',
    "new":    '    shimPath: path.join(os.homedir(), ".local", "bin", "git"),',
}

# ─── Patch D: gog install destination ────────────────────────────────────────
_P_GOG = {
    "name":   "gog-install-dest",
    "detect": 'const gogLocalBin = path.join(os.homedir(), ".local", "bin");',
    "old": (
        '    execSync(\n'
        '      `curl -fsSL "${url}" -o /tmp/gog.tar.gz && tar -xzf /tmp/gog.tar.gz -C /tmp/'
        ' && mv /tmp/gog /usr/local/bin/gog && chmod +x /usr/local/bin/gog'
        ' && rm -f /tmp/gog.tar.gz`,\n'
        '      { stdio: "inherit" },\n'
        '    );'
    ),
    "new": (
        '    const gogLocalBin = path.join(os.homedir(), ".local", "bin");\n'
        '    execSync(\n'
        '      `curl -fsSL "${url}" -o /tmp/gog.tar.gz && tar -xzf /tmp/gog.tar.gz -C /tmp/'
        ' && mkdir -p "${gogLocalBin}" && mv /tmp/gog "${gogLocalBin}/gog"'
        ' && chmod +x "${gogLocalBin}/gog" && rm -f /tmp/gog.tar.gz`,\n'
        '      { stdio: "inherit" },\n'
        '    );'
    ),
}

# ─── Patch E: cron setup — macOS user crontab ────────────────────────────────
# old = the original Linux-only block (inferred from the else branch in the current file)
# new = the darwin/else block in the current patched file
_P_CRON = {
    "name":   "cron-macos",
    "detect": "// macOS: /etc/cron.d/ doesn't exist; use user crontab instead",
    "old": (
        '    const cronFilePath = "/etc/cron.d/openclaw-hourly-sync";\n'
        '    if (cronEnabled) {\n'
        '      const cronContent = [\n'
        '        "SHELL=/bin/bash",\n'
        '        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",\n'
        "        `${cronSchedule} root bash \"${hourlyGitSyncPath}\""
        ' >> /var/log/openclaw-hourly-sync.log 2>&1`,\n'
        '        "",\n'
        '      ].join("\\n");\n'
        '      fs.writeFileSync(cronFilePath, cronContent, { mode: 0o644 });\n'
        '      console.log("[alphaclaw] System cron entry installed");\n'
        '    } else {\n'
        '      try {\n'
        '        fs.unlinkSync(cronFilePath);\n'
        '      } catch {}\n'
        '      console.log("[alphaclaw] System cron entry disabled");\n'
        '    }'
    ),
    "new": (
        '    if (os.platform() === "darwin") {\n'
        '      // macOS: /etc/cron.d/ doesn\'t exist; use user crontab instead\n'
        '      const cronMarker = "# openclaw-hourly-sync";\n'
        "      const newEntry = `${cronSchedule} bash \"${hourlyGitSyncPath}\""
        ' >> /tmp/openclaw-hourly-sync.log 2>&1 ${cronMarker}`;\n'
        '      let existing = "";\n'
        '      try { existing = execSync("crontab -l 2>/dev/null", { encoding: "utf8" }); } catch {}\n'
        '      const lines = existing.split("\\n").filter(l => !l.includes(cronMarker) && l.trim() !== "");\n'
        '      if (cronEnabled) lines.push(newEntry);\n'
        '      const tmpCron = `/tmp/openclaw-crontab-${process.pid}.txt`;\n'
        '      fs.writeFileSync(tmpCron, lines.join("\\n") + "\\n");\n'
        '      execSync(`crontab "${tmpCron}"`);\n'
        '      fs.unlinkSync(tmpCron);\n'
        '      console.log("[alphaclaw] System cron entry installed (macOS user crontab)");\n'
        '    } else {\n'
        '      const cronFilePath = "/etc/cron.d/openclaw-hourly-sync";\n'
        '      if (cronEnabled) {\n'
        '        const cronContent = [\n'
        '          "SHELL=/bin/bash",\n'
        '          "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",\n'
        "          `${cronSchedule} root bash \"${hourlyGitSyncPath}\""
        ' >> /var/log/openclaw-hourly-sync.log 2>&1`,\n'
        '          "",\n'
        '        ].join("\\n");\n'
        '        fs.writeFileSync(cronFilePath, cronContent, { mode: 0o644 });\n'
        '        console.log("[alphaclaw] System cron entry installed");\n'
        '      } else {\n'
        '        try {\n'
        '          fs.unlinkSync(cronFilePath);\n'
        '        } catch {}\n'
        '        console.log("[alphaclaw] System cron entry disabled");\n'
        '      }\n'
        '    }'
    ),
}

# ─── Patch F: systemctl shim — skip on macOS ─────────────────────────────────
# old = the original Linux block without platform guard
# new = the platform-guarded block in the current patched file
_P_SYSTEMCTL = {
    "name":   "systemctl-skip-macos",
    "detect": "// systemctl shim is only needed on Linux (Docker); macOS uses launchd",
    "old": (
        "// ---------------------------------------------------------------------------\n"
        "// 12. Install systemctl shim if in Docker (no real systemd)\n"
        "// ---------------------------------------------------------------------------\n"
        "\ntry {\n"
        '  execSync("command -v systemctl", { stdio: "ignore" });\n'
        "} catch {\n"
        "  const shimSrc = path.join(__dirname, \"..\", \"lib\", \"scripts\", \"systemctl\");\n"
        '  const shimDest = "/usr/local/bin/systemctl";\n'
        "  try {\n"
        "    fs.copyFileSync(shimSrc, shimDest);\n"
        "    fs.chmodSync(shimDest, 0o755);\n"
        '    console.log("[alphaclaw] systemctl shim installed");\n'
        "  } catch (e) {\n"
        "    console.log(`[alphaclaw] systemctl shim skipped: ${e.message}`);\n"
        "  }\n"
        "}"
    ),
    "new": (
        "// ---------------------------------------------------------------------------\n"
        "// 12. Install systemctl shim if in Docker (no real systemd)\n"
        "// ---------------------------------------------------------------------------\n"
        '\nif (os.platform() !== "darwin") {\n'
        "  // systemctl shim is only needed on Linux (Docker); macOS uses launchd\n"
        "  try {\n"
        '    execSync("command -v systemctl", { stdio: "ignore" });\n'
        "  } catch {\n"
        "    const shimSrc = path.join(__dirname, \"..\", \"lib\", \"scripts\", \"systemctl\");\n"
        '    const shimDest = path.join(os.homedir(), ".local", "bin", "systemctl");\n'
        "    try {\n"
        "      fs.mkdirSync(path.dirname(shimDest), { recursive: true });\n"
        "      fs.copyFileSync(shimSrc, shimDest);\n"
        "      fs.chmodSync(shimDest, 0o755);\n"
        '      console.log("[alphaclaw] systemctl shim installed");\n'
        "    } catch (e) {\n"
        "      console.log(`[alphaclaw] systemctl shim skipped: ${e.message}`);\n"
        "    }\n"
        "  }\n"
        "}"
    ),
}

ALL_PATCHES = [_P_GIT_DEST, _P_GIT_MKDIR, _P_GIT_SHIMPATH, _P_GOG, _P_CRON, _P_SYSTEMCTL]


def _alphaclaw_version() -> str:
    pkg = ALPHACLAW_JS.parent.parent.parent / "package.json"
    try:
        return json.loads(pkg.read_text()).get("version", "unknown")
    except Exception:
        return "unknown"


def step_patch_alphaclaw() -> None:
    if not ALPHACLAW_JS.exists():
        _warn("alphaclaw.js", f"not found at {ALPHACLAW_JS}")
        return

    version = _alphaclaw_version()
    if version != KNOWN_ALPHACLAW_VERSION:
        _warn(
            "alphaclaw.js version",
            f"installed={version}  known={KNOWN_ALPHACLAW_VERSION} — "
            "patches may not apply cleanly; check manually if errors appear",
        )

    content = ALPHACLAW_JS.read_text(encoding="utf-8")
    original = content
    patch_results: dict[str, str] = {}

    for p in ALL_PATCHES:
        name, detect, old, new = p["name"], p["detect"], p["old"], p["new"]
        if detect in content:
            _skip(f"alphaclaw.js/{name}")
            patch_results[name] = "skip"
        elif old in content:
            content = content.replace(old, new, 1)
            _applied(f"alphaclaw.js/{name}")
            patch_results[name] = "fixed"
        else:
            _warn(
                f"alphaclaw.js/{name}",
                "neither patched nor original string found — npm version mismatch?",
            )
            patch_results[name] = "unknown"

    if content != original and not DRY_RUN:
        ALPHACLAW_JS.write_text(content, encoding="utf-8")

    # Write marker so future runs can quickly confirm state
    if not DRY_RUN:
        MARKER_FILE.parent.mkdir(parents=True, exist_ok=True)
        MARKER_FILE.write_text(
            json.dumps(
                {
                    "alphaclaw_version": version,
                    "script_version":    KNOWN_ALPHACLAW_VERSION,
                    "patches":           patch_results,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )



# ── step 5: install discover.py hub ──────────────────────────────────────────

OPENCLAW_SCRIPTS = HOME / ".openclaw" / "scripts"
DISCOVER_HUB_SRC = Path(__file__).parent / "scripts" / "discover.py"
DISCOVER_HUB_DST = OPENCLAW_SCRIPTS / "discover.py"

def step_install_discover_hub() -> None:
    """Copy scripts/discover.py to ~/.openclaw/scripts/discover.py (idempotent)."""
    if not DISCOVER_HUB_SRC.exists():
        _warn("discover hub", f"source not found at {DISCOVER_HUB_SRC} — skipping install")
        return
    OPENCLAW_SCRIPTS.mkdir(parents=True, exist_ok=True)
    src_content = DISCOVER_HUB_SRC.read_bytes()
    if DISCOVER_HUB_DST.exists() and DISCOVER_HUB_DST.read_bytes() == src_content:
        _skip("discover hub", f"already up-to-date at {DISCOVER_HUB_DST}")
        return
    if DRY_RUN:
        print(f"  [dry-run] would install {DISCOVER_HUB_SRC} → {DISCOVER_HUB_DST}", flush=True)
        return
    import shutil
    shutil.copy2(DISCOVER_HUB_SRC, DISCOVER_HUB_DST)
    DISCOVER_HUB_DST.chmod(0o755)
    _applied("discover hub", f"installed to {DISCOVER_HUB_DST}")


# ── step 6: self-discovery skill version guard ────────────────────────────────

SELF_DISC_SKILL = Path(__file__).parent / ".claude" / "skills" / "self-discovery" / "SKILL.md"
SELF_DISC_VERSION = "0.9.9.7"

def _skill_version(path: Path) -> tuple:
    """Parse `version: X.Y.Z` from SKILL.md frontmatter. Returns (0,0,0) if absent."""
    try:
        for line in path.read_text().splitlines():
            s = line.strip()
            if s.startswith("version:"):
                v = s.split(":", 1)[1].strip().strip('"\' ')
                return tuple(int(x) for x in v.split("."))
    except Exception:
        pass
    return (0, 0, 0)

def step_self_discovery_skill() -> None:
    """Announce /self-discovery and guard against version downgrade."""
    bundled = tuple(int(x) for x in SELF_DISC_VERSION.split("."))
    if SELF_DISC_SKILL.exists():
        installed = _skill_version(SELF_DISC_SKILL)
        v_str = ".".join(str(x) for x in installed)
        if installed >= bundled:
            _skip("self-discovery skill", f"installed v{v_str} >= bundled v{SELF_DISC_VERSION}")
            return
        _warn("self-discovery skill",
              f"installed v{v_str} < bundled v{SELF_DISC_VERSION} — update SKILL.md from GitHub")
        return
    _warn("self-discovery skill",
          f"not found at {SELF_DISC_SKILL} — clone the full repo or restore from GitHub")

# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    if not QUIET:
        print("  setup_macos.py — pre-flight checks", flush=True)

    step_local_bin()
    step_path_entry()
    step_openclaw_json()
    step_patch_alphaclaw()
    step_install_discover_hub()
    step_self_discovery_skill()

    if _fixes:
        print(f"  setup_macos: applied {len(_fixes)} fix(es): {', '.join(_fixes)}", flush=True)
    if _warnings:
        print(f"  setup_macos: {len(_warnings)} warning(s):", flush=True)
        for w in _warnings:
            print(f"    ⚠  {w}", flush=True)

    return 1 if _warnings else 0


if __name__ == "__main__":
    sys.exit(main())

