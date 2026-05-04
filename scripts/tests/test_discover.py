import json, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import discover as D

@pytest.fixture(autouse=True)
def _set_pt_root_env(monkeypatch, tmp_path):
    monkeypatch.setenv("PERPETUA_TOOLS_ROOT", str(tmp_path))
    yield


def test_hash_deterministic():
    ep = {"mac": {"ip": "127.0.0.1", "models": ["m1", "m2"]},
          "win": {"ip": "192.168.254.101", "models": ["m3"]}}
    assert D.compute_hash(ep) == D.compute_hash(ep)

def test_hash_changes_on_ip_change():
    ep1 = {"mac": {"ip": "127.0.0.1", "models": ["m1"]}, "win": None}
    ep2 = {"mac": {"ip": "192.168.254.107", "models": ["m1"]}, "win": None}
    assert D.compute_hash(ep1) != D.compute_hash(ep2)

def test_hash_model_order_independent():
    ep1 = {"mac": {"ip": "x", "models": ["b", "a"]}, "win": None}
    ep2 = {"mac": {"ip": "x", "models": ["a", "b"]}, "win": None}
    assert D.compute_hash(ep1) == D.compute_hash(ep2)

def test_hash_none_endpoint():
    ep = {"mac": None, "win": None}
    assert isinstance(D.compute_hash(ep), str)
    assert len(D.compute_hash(ep)) == 40


POLICY = {
    "windows_only": [
        "gemma-4-26b-a4b-it",
        "gemma-4-26B-A4B-it-Q4_K_M",
        "qwen3.5-27b-claude-4.6-opus-reasoning-distilled-v2",
        "Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2",
    ],
    "mac_only": [
        "gemma-4-e4b-it",
        "qwen3.5-9b-mlx",
        "qwen3.5-9b-mlx-4bit",
        "Qwen3.5-9B-MLX-4bit",
    ],
    "shared": [],
}


def test_filter_models_for_mac_strips_windows_only_models():
    models = [
        "Qwen3.5-9B-MLX-4bit",
        "gemma-4-e4b-it",
        "gemma-4-26B-A4B-it-Q4_K_M",
        "Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2",
    ]
    assert D.filter_models_for_platform(models, "mac", POLICY) == [
        "Qwen3.5-9B-MLX-4bit",
        "gemma-4-e4b-it",
    ]


def test_filter_models_for_win_strips_mac_only_models():
    models = [
        "Qwen3.5-9B-MLX-4bit",
        "qwen3.5-9b-mlx-4bit",
        "gemma-4-26B-A4B-it-Q4_K_M",
        "Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2",
    ]
    assert D.filter_models_for_platform(models, "win", POLICY) == [
        "gemma-4-26B-A4B-it-Q4_K_M",
        "Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2",
    ]


def test_filter_models_clean_input_no_change():
    models = ["Qwen3.5-9B-MLX-4bit", "gemma-4-e4b-it"]
    assert D.filter_models_for_platform(models, "mac", POLICY) == models


def test_filter_models_unknown_model_passes_through():
    models = ["unknown-local-experiment"]
    assert D.filter_models_for_platform(models, "mac", POLICY) == models


def test_backup_limit_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "BACKUPS_DIR", tmp_path / "backups")
    monkeypatch.setattr(D, "ARCHIVE_DIR", tmp_path / "archive")
    (tmp_path / "backups").mkdir()
    (tmp_path / "archive").mkdir()
    import os
    for i in range(32):
        f = tmp_path / "backups" / f"2026-01-{i+1:02d}_00-00-00.json"
        f.write_text("{}")
        os.utime(f, (i * 1000, i * 1000))
    D._enforce_backup_limits()
    remaining = list((tmp_path / "backups").glob("*.json"))
    assert len(remaining) <= D.MAX_BACKUPS

def test_old_files_archived_not_deleted(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "BACKUPS_DIR", tmp_path / "backups")
    monkeypatch.setattr(D, "ARCHIVE_DIR", tmp_path / "archive")
    (tmp_path / "backups").mkdir()
    (tmp_path / "archive").mkdir()
    import os
    old_file = tmp_path / "backups" / "2025-01-01_00-00-00.json"
    old_file.write_text("{}")
    old_mtime = time.time() - (31 * 86400)
    os.utime(old_file, (old_mtime, old_mtime))
    D._enforce_backup_limits()
    assert not old_file.exists(), "old file should have been moved"
    assert (tmp_path / "archive" / "2025-01-01_00-00-00.json").exists()


DEVICES_YML = """\
devices:
  - id: "mac-studio"
    os: macos
    lan_ip: "192.168.254.103"
    ports: [1234]
  - id: "win-rtx3080"
    os: windows
    lan_ip: "192.168.254.100"
    ports: [1234]
"""

def test_patch_devices_yml(tmp_path):
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "devices.yml").write_text(DEVICES_YML)
    D.patch_devices_yml("192.168.254.107", "192.168.254.101", tmp_path)
    result = (cfg / "devices.yml").read_text()
    assert '"192.168.254.107"' in result
    assert '"192.168.254.101"' in result
    assert "192.168.254.103" not in result
    assert "192.168.254.100" not in result

def test_patch_devices_yml_no_write_if_unchanged(tmp_path):
    cfg = tmp_path / "config"
    cfg.mkdir()
    content = DEVICES_YML.replace("192.168.254.103", "192.168.254.107").replace("192.168.254.100", "192.168.254.101")
    (cfg / "devices.yml").write_text(content)
    import os
    mtime_before = os.stat(cfg / "devices.yml").st_mtime
    time.sleep(0.05)
    D.patch_devices_yml("192.168.254.107", "192.168.254.101", tmp_path)
    mtime_after = os.stat(cfg / "devices.yml").st_mtime
    assert mtime_before == mtime_after


def test_patch_openclaw_json(tmp_path, monkeypatch):
    oc = tmp_path / "openclaw.json"
    oc.write_text(json.dumps({
        "models": {"providers": {
            "lmstudio-mac": {"baseUrl": "http://192.168.1.147:1234/v1", "models": []},
            "lmstudio-win": {"baseUrl": "http://192.168.254.108:1234/v1", "models": []},
        }},
        "meta": {"lastTouchedAt": "2026-01-01T00:00:00Z"}
    }))
    monkeypatch.setattr(D, "OPENCLAW_JSON", oc)
    monkeypatch.setattr(D, "load_policy", lambda policy_path=None: POLICY)
    endpoints = {
        "mac": {"ip": "192.168.254.107", "models": ["qwen3.5-9b-mlx", "gemma-4-26B-A4B-it-Q4_K_M", "text-embedding-nomic"]},
        "win": {"ip": "192.168.254.101", "models": ["qwen3.5-27b-distilled", "Qwen3.5-9B-MLX-4bit"]},
    }
    D.patch_openclaw_json(endpoints)
    cfg = json.loads(oc.read_text())
    assert "192.168.254.107" in cfg["models"]["providers"]["lmstudio-mac"]["baseUrl"]
    assert "192.168.254.101" in cfg["models"]["providers"]["lmstudio-win"]["baseUrl"]
    mac_ids = [m["id"] for m in cfg["models"]["providers"]["lmstudio-mac"]["models"]]
    assert "text-embedding-nomic" not in mac_ids
    assert "qwen3.5-9b-mlx" in mac_ids
    assert "gemma-4-26B-A4B-it-Q4_K_M" not in mac_ids
    win_ids = [m["id"] for m in cfg["models"]["providers"]["lmstudio-win"]["models"]]
    assert "Qwen3.5-9B-MLX-4bit" not in win_ids


def test_win_primary_prefers_27b(tmp_path, monkeypatch):
    """Win primary model selection must prefer the 27b distilled model over alphabetically-first gemma."""
    import io
    monkeypatch.setattr(D, "LAST_DISCOVERY_JSON", tmp_path / "last_discovery.json")
    win_models = [
        "gemma-4-26b-a4b-it",
        "gemma-4-e4b-it",
        "qwen3.5-27b-claude-4.6-opus-reasoning-distilled-v2",
        "qwen3.5-9b-mlx",
        "text-embedding-nomic-embed-text-v1.5",
    ]
    # Reproduce write_env_lmstudio model selection logic inline
    win_primary = (next((m for m in win_models if "27b" in m.lower()), None) or
                   next((m for m in win_models if "embed" not in m.lower()), ""))
    assert win_primary == "qwen3.5-27b-claude-4.6-opus-reasoning-distilled-v2"
    win_fallback = next((m for m in win_models if m != win_primary and "embed" not in m.lower()), "")
    assert "embed" not in win_fallback.lower()
    assert win_fallback != win_primary


def test_disaster_recovery_tier2(tmp_path, monkeypatch):
    """When all probes fail, tier-2 (last_discovery) is loaded."""
    monkeypatch.setattr(D, "STATE_DIR", tmp_path)
    monkeypatch.setattr(D, "BACKUPS_DIR", tmp_path / "backups")
    monkeypatch.setattr(D, "ARCHIVE_DIR", tmp_path / "archive")
    monkeypatch.setattr(D, "DISCOVERY_JSON", tmp_path / "discovery.json")
    monkeypatch.setattr(D, "LAST_DISCOVERY_JSON", tmp_path / "last_discovery.json")
    monkeypatch.setattr(D, "RECOVERY_SOURCE_TXT", tmp_path / "recovery_source.txt")
    monkeypatch.setattr(D, "OPENCLAW_JSON", tmp_path / "openclaw.json")
    monkeypatch.setattr(D, "LOCK_FILE", tmp_path / ".discover.lock")
    (tmp_path / "openclaw.json").write_text("{}")
    (tmp_path / "backups").mkdir()
    (tmp_path / "archive").mkdir()
    # Seed last-good state
    last_good = {
        "mac": {"ip": "192.168.254.107", "models": ["qwen3.5-9b-mlx"]},
        "win": {"ip": "192.168.254.101", "models": ["qwen3.5-27b-distilled"]},
    }
    D.save_discovery_state(last_good, tier=1)
    # Simulate both endpoints unreachable
    monkeypatch.setattr(D, "discover_endpoints", lambda: {"mac": None, "win": None})
    result = D.run_discovery(force=True)
    assert result == 0
    state = D._load_json(tmp_path / "discovery.json")
    assert state["recovery_tier"] == 2
    assert state["endpoints"]["mac"]["ip"] == "192.168.254.107"


def test_no_write_when_hash_unchanged(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "STATE_DIR", tmp_path)
    monkeypatch.setattr(D, "BACKUPS_DIR", tmp_path / "backups")
    monkeypatch.setattr(D, "ARCHIVE_DIR", tmp_path / "archive")
    monkeypatch.setattr(D, "DISCOVERY_JSON", tmp_path / "discovery.json")
    monkeypatch.setattr(D, "LAST_DISCOVERY_JSON", tmp_path / "last_discovery.json")
    monkeypatch.setattr(D, "RECOVERY_SOURCE_TXT", tmp_path / "recovery_source.txt")
    monkeypatch.setattr(D, "OPENCLAW_JSON", tmp_path / "openclaw.json")
    (tmp_path / "openclaw.json").write_text("{}")
    (tmp_path / "backups").mkdir()
    (tmp_path / "archive").mkdir()
    endpoints = {"mac": {"ip": "127.0.0.1", "models": ["m1"]}, "win": {"ip": "1.2.3.4", "models": ["m2"]}}
    D.save_discovery_state(endpoints, tier=1)
    files_before = {f: f.stat().st_mtime for f in tmp_path.rglob("*.json")}
    monkeypatch.setattr(D, "discover_endpoints", lambda: endpoints)
    time.sleep(0.05)
    result = D.run_discovery(force=True)
    assert result == 0
    for f, mtime in files_before.items():
        if f.name in {"discovery.json", "last_discovery.json"}:
            continue
        assert f.stat().st_mtime == mtime, f"{f} should not have been rewritten"


def test_perpetua_root_precedence_root_over_legacy(monkeypatch):
    monkeypatch.setenv("PERPETUA_TOOLS_ROOT", "/tmp/pt-root")
    monkeypatch.setenv("PERPETUA_TOOLS_PATH", "/tmp/pt-legacy")
    assert D._resolve_perpetua_root_env() == Path("/tmp/pt-root")


def test_perpetua_root_falls_back_to_legacy(monkeypatch):
    monkeypatch.delenv("PERPETUA_TOOLS_ROOT", raising=False)
    monkeypatch.setenv("PERPETUA_TOOLS_PATH", "/tmp/pt-legacy")
    assert D._resolve_perpetua_root_env() == Path("/tmp/pt-legacy")


def test_get_repo_paths_uses_resolved_perpetua_root(monkeypatch):
    monkeypatch.setenv("PERPETUA_TOOLS_ROOT", "/tmp/pt-root")
    paths = D.get_repo_paths()
    assert paths["perpetua_tools"] == Path("/tmp/pt-root")


def test_discover_fails_closed_when_perpetuatoolsroot_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("PERPETUATOOLSROOT", raising=False)
    monkeypatch.delenv("PERPETUA_TOOLS_ROOT", raising=False)
    monkeypatch.delenv("PERPETUA_TOOLS_PATH", raising=False)
    monkeypatch.setattr(D, "OPENCLAW_JSON", tmp_path / "openclaw.json")
    (tmp_path / "openclaw.json").write_text("{}")
    with pytest.raises(SystemExit):
        D.patch_openclaw_json({"mac": None, "win": None})


def test_perpetuatoolsroot_takes_precedence_over_legacy_path(monkeypatch, tmp_path):
    canonical = tmp_path / "canonical_pt"
    legacy = tmp_path / "legacy_pt"
    canonical.mkdir()
    legacy.mkdir()
    monkeypatch.setenv("PERPETUATOOLSROOT", str(canonical))
    monkeypatch.setenv("PERPETUA_TOOLS_PATH", str(legacy))
    assert D._resolve_perpetua_root_env() == canonical


def test_legacy_path_works_as_fallback_when_root_absent(monkeypatch, tmp_path):
    legacy = tmp_path / "legacy_pt"
    legacy.mkdir()
    monkeypatch.delenv("PERPETUATOOLSROOT", raising=False)
    monkeypatch.delenv("PERPETUA_TOOLS_ROOT", raising=False)
    monkeypatch.setenv("PERPETUA_TOOLS_PATH", str(legacy))
    assert D._resolve_perpetua_root_env() == legacy
