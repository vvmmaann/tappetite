"""Rewrite full body+body_en of each archetype in 'physics_laws' category.

Reason: existing bodies are ~70% about the physics law (history, formulas,
who discovered it) and only ~30% about the user's mindset. Goal is the
opposite ratio - ~70-80% about how this person thinks/processes the world,
~20-30% with the law as a metaphor or anchor. Law NAMES the type of
thinking, doesn't lecture about itself.

Source data: scripts/_physics_rewrites.json (13 archetypes; produced by
agent given the prompt at _physics_archetypes_rewrite_prompt.md).

This script replaces the FULL body and body_en (not just п1). Names,
triggers, and ids are unchanged - same matching logic, same archetype
wins for the same top-3.

Run on server:
    cd /opt/untitled-pick-game-api
    python3 scripts/rewrite_physics_archetypes_20260518.py
    systemctl restart untitled-pick-game-api

Backs up categories.json with timestamp before writing.
"""
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
SRC = Path("/opt/untitled-pick-game-api/data/categories.json")
REWRITES = HERE / "_physics_rewrites.json"
CATEGORY_ID = "physics_laws"


def main():
    if not SRC.exists():
        print(f"[err] not found: {SRC}", file=sys.stderr)
        sys.exit(1)
    if not REWRITES.exists():
        print(f"[err] rewrites file not found: {REWRITES}", file=sys.stderr)
        sys.exit(1)

    rewrites = json.loads(REWRITES.read_text(encoding="utf-8"))
    if not isinstance(rewrites, list):
        print(f"[err] rewrites file should be a JSON array", file=sys.stderr)
        sys.exit(1)

    # Build name -> (body, body_en) map. id_for_match is the RU name.
    by_name = {}
    for entry in rewrites:
        name = entry.get("id_for_match", "").strip()
        body = entry.get("body", "")
        body_en = entry.get("body_en", "")
        if not name or not body or not body_en:
            print(f"[err] bad entry: {entry}", file=sys.stderr)
            sys.exit(1)
        by_name[name] = (body, body_en)

    print(f"[ok] loaded {len(by_name)} rewrites from {REWRITES.name}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = SRC.with_suffix(f".json.bak.{ts}")
    shutil.copy2(SRC, backup)
    print(f"[ok] backup: {backup}")

    data = json.loads(SRC.read_text(encoding="utf-8"))
    cats = data if isinstance(data, list) else data.get("categories", [])

    target = next((c for c in cats if c.get("id") == CATEGORY_ID), None)
    if not target:
        print(f"[err] category '{CATEGORY_ID}' not found", file=sys.stderr)
        sys.exit(1)

    found, missing = [], set(by_name)
    arch_list = target.get("archetypes", []) or []

    def apply_one(arch_obj, name, where):
        new_body, new_body_en = by_name[name]
        old_body = arch_obj.get("body", "") or ""
        old_body_en = arch_obj.get("body_en", "") or ""

        # Sanity: 4 paragraphs separated by \n\n
        new_paras = new_body.split("\n\n")
        new_paras_en = new_body_en.split("\n\n")
        if len(new_paras) != 4 or len(new_paras_en) != 4:
            print(
                f"[warn] '{name}' ({where}): expected 4 paragraphs, "
                f"got RU={len(new_paras)} EN={len(new_paras_en)}",
                file=sys.stderr,
            )

        # Length sanity
        ru_len = len(new_body)
        en_len = len(new_body_en)
        if not (700 <= ru_len <= 1400):
            print(f"[warn] '{name}' RU length={ru_len} (target 800-1200)", file=sys.stderr)
        if not (700 <= en_len <= 1400):
            print(f"[warn] '{name}' EN length={en_len} (target 800-1200)", file=sys.stderr)

        # Em-dash sanity (user rule)
        if "—" in new_body or "—" in new_body_en:
            print(f"[warn] '{name}' contains em-dash (forbidden)", file=sys.stderr)

        arch_obj["body"] = new_body
        arch_obj["body_en"] = new_body_en
        found.append((name, where, len(old_body), ru_len, len(old_body_en), en_len))
        missing.discard(name)

    # 1) Named archetypes in archetypes[]
    for arch in arch_list:
        name = (arch.get("name") or "").strip()
        if name in by_name:
            apply_one(arch, name, "archetypes[]")

    # 2) defaultArchetype (category-level fallback)
    da = target.get("defaultArchetype")
    if isinstance(da, dict):
        da_name = (da.get("name") or "").strip()
        if da_name in by_name:
            apply_one(da, da_name, "defaultArchetype")

    print(f"\n[ok] applied to {len(found)}/{len(by_name)} archetypes:")
    for name, where, old_ru, new_ru, old_en, new_en in found:
        print(f"  - {name:25s} [{where:18s}]  RU: {old_ru:4d} -> {new_ru:4d}  EN: {old_en:4d} -> {new_en:4d}")

    if missing:
        print(f"\n[warn] not found in '{CATEGORY_ID}': {sorted(missing)}")
        print("       (check archetype names - they may have changed)")
        sys.exit(2)

    # List all physics_laws archetype names so user can see what wasn't touched
    untouched = [a.get("name") for a in arch_list if (a.get("name") or "").strip() not in by_name]
    if untouched:
        print(f"\n[info] physics_laws archetypes NOT touched: {untouched}")

    SRC.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[ok] wrote: {SRC}")
    print("Next: systemctl restart untitled-pick-game-api")


if __name__ == "__main__":
    main()
