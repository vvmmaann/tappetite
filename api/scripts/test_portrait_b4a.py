"""Live test for api/portrait.py (B4a chunk).

Generates a real AI portrait for one user by hitting the Anthropic API.
Reads ANTHROPIC_API_KEY from /opt/untitled-pick-game-api/.env or env.

Usage on server:
  cd /opt/untitled-pick-game-api
  python3 scripts/test_portrait_b4a.py 2                  # global portrait for user 2 (Uncle), default Sonnet
  python3 scripts/test_portrait_b4a.py 2 en               # English portrait
  python3 scripts/test_portrait_b4a.py 2 ru claude-haiku-4-5   # Use Haiku to compare cost/quality

Prints:
- The full system+user prompt summary (chars, history_count)
- Latency + token usage + $$ cost
- The portrait text

Does NOT write to DB. Pure read + API call.
"""
import os
import sys
import sqlite3
import json
from pathlib import Path

sys.path.insert(0, "/opt/untitled-pick-game-api")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Load env from systemd's canonical location first, fall back to legacy /opt
for ENV_PATH in [
    Path("/etc/untitled-pick-game-api.env"),
    Path("/opt/untitled-pick-game-api/.env"),
]:
    if not ENV_PATH.exists():
        continue
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        # Don't overwrite if already set in env / earlier file
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("[err] ANTHROPIC_API_KEY not in env or /opt/untitled-pick-game-api/.env")
    sys.exit(1)

from portrait import generate_global_portrait, DEFAULT_MODEL


def main(argv: list[str]):
    if len(argv) < 2:
        print(f"usage: {argv[0]} <user_id> [lang=ru] [model={DEFAULT_MODEL}]")
        sys.exit(2)

    user_id = int(argv[1])
    lang = argv[2] if len(argv) > 2 else "ru"
    model = argv[3] if len(argv) > 3 else DEFAULT_MODEL

    print(f"=== Generating portrait ===")
    print(f"  user_id: {user_id}")
    print(f"  lang:    {lang}")
    print(f"  model:   {model}")
    print()

    db = sqlite3.connect("/opt/untitled-pick-game-api/data/db.sqlite")
    db.row_factory = sqlite3.Row
    cats_data = json.load(open("/opt/untitled-pick-game-api/data/categories.json"))
    categories = cats_data if isinstance(cats_data, list) else cats_data.get("categories", [])

    try:
        result = generate_global_portrait(db, user_id, categories, lang=lang, model=model)
    except Exception as e:
        print(f"[err] generation failed: {e}")
        sys.exit(1)

    print(f"=== Metrics ===")
    print(f"  History: {result['history_count']} tournaments")
    print(f"  Prompt: {result['prompt_chars']:,} chars")
    print(f"  Tokens: {result['input_tokens']:,} in / {result['output_tokens']:,} out")
    print(f"  Cost:   ${result['cost_usd']:.4f}")
    print(f"  Latency: {result['latency_sec']}s")
    print(f"  Model returned: {result['model']}")
    print()
    print("=== PORTRAIT ===")
    print(result["text"])
    print()
    print(f"=== Words: ~{len(result['text'].split())} ===")


if __name__ == "__main__":
    main(sys.argv)
