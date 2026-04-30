# Module: Lessons + SKILL.md Authoring Tooling

> Status: stub — v1 carry-over, ships at own pace

## What it does

Ports the existing lessons capture system (`docs/LESSONS.md`, `/self-improve` skill, `scripts/capture_lesson.py`) and SKILL.md authoring toolchain from v1 into the v2 module ecosystem.

## Current state in v1.0 RC

- `docs/LESSONS.md` — canonical chronological lesson log (52KB, shared across ECC/AutoResearcher/Claude sessions)
- `scripts/capture_lesson.py` — appends lessons in Symptom → Cause → Fix → Rule format
- `orama-system/SKILL.md` + `bin/orama-system/SKILL.md` — the mother skill

## v2 migration

- Lessons format stays the same (Symptom → Cause → Fix → Rule)
- `GossipBus` events can auto-trigger lesson capture at graph completion
- SKILL.md authoring moves to a dedicated `oramasys/orama/skills/` namespace
- AFRP gate + CIDF content insertion framework preserved as non-kernel utilities

## TDD note

The lessons system IS part of the TDD policy (per `tdd.md`): every completed graph run should capture one lesson. This module makes that automatic.
