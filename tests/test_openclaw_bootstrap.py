from __future__ import annotations

import json

import openclaw_bootstrap as bootstrap


def test_apply_runtime_payload_writes_pt_resolved_config(monkeypatch, tmp_path):
    monkeypatch.setattr(bootstrap.Path, "home", lambda: tmp_path)
    payload = {
        "gateway": {
            "gateway_ready": True,
            "gateway_url": "http://127.0.0.1:18789",
            "openclaw_config": {
                "gateway": {"port": 18789},
                "agents": {"defaults": {"workspace": "x"}},
            },
        },
        "role_routing": {"topology": "manager-local_researcher-remote"},
    }

    result = bootstrap.apply_runtime_payload(payload, force=False)

    written = json.loads((tmp_path / ".openclaw" / "openclaw.json").read_text(encoding="utf-8"))
    assert written["gateway"]["port"] == 18789
    assert result["gateway_ready"] is True
    assert result["topology"] == "manager-local_researcher-remote"
