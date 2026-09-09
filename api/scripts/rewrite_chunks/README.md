# Archetype p1 batch rewrite — workflow

## What this is

A pipeline to fix ~325 RU + ~303 EN archetype openings across 99 categories
that currently start with item-name lists («Реквием по мечте, Олдбой,
Чёрный лебедь, Джокер. Ты любишь...»). User complaint: triggers feel of
"engine is showing me names I never picked, why is it acting smart?"

Result: shorter, more concrete p1 (~165 chars vs ~250) opened with
scene/antithesis/sensory/paradox/direct-speech instead of name lists.
п2-п4 of each archetype stay untouched.

## Files in this directory

| File | Purpose |
|---|---|
| `EDITOR_PROMPT.md` | Instructions for the AI editor agent. 6 worked examples. |
| `chunker.py` | Splits all archetypes-needing-rewrite into chunk_NN.json files |
| `chunk_NN.json` | Input batch for one agent run (~30 archetypes) |
| `chunk_NN_OUTPUT.json` | Agent's output — must be written by the agent |
| `apply_rewrites.py` | Merges all _OUTPUT.json back into prod categories.json |

## Workflow (the human running this)

### Step 1: prepare chunks

You need `categories_live.json` in the parent directory (`../`). Pull from prod:

```bash
scp root@185.186.76.89:/opt/untitled-pick-game-api/data/categories.json ../categories_live.json
```

Then chunk:
```bash
python chunker.py
# → writes chunk_01.json … chunk_NN.json
```

### Step 2: feed each chunk to an AI editor

For each chunk file, open a fresh agent session (Claude Sonnet/Opus, GPT-5,
or whatever your editor of choice). First message:

> Paste the full text of `EDITOR_PROMPT.md` here.
>
> Then paste the contents of `chunk_NN.json` (or attach as file) and ask:
> "Apply the rules above. Output JSON only, no markdown wrapper."

When the agent returns a JSON array, save it as `chunk_NN_OUTPUT.json` in
this directory (same number as input). Repeat for all chunks.

**Tip:** you can run multiple agents in parallel for different chunks.

### Step 3: merge outputs into categories.json

After ALL outputs are present in this directory:

```bash
# Apply to local copy first (sanity check)
python apply_rewrites.py ../categories_live.json
# Or directly to prod via ssh:
scp apply_rewrites.py root@185.186.76.89:/opt/untitled-pick-game-api/scripts/rewrite_chunks/
scp chunk_*_OUTPUT.json root@185.186.76.89:/opt/untitled-pick-game-api/scripts/rewrite_chunks/
ssh root@185.186.76.89 "cd /opt/untitled-pick-game-api/scripts/rewrite_chunks && python3 apply_rewrites.py"
```

apply_rewrites.py:
- Validates every output entry against its input
- Validates each new p1: length 80-220, no item names from category
- ABORTS atomically if any output is missing or fails validation
- Backs up categories.json before write
- Replaces ONLY the first paragraph (\\n\\n separator); п2-п4 untouched

If validation fails, fix the bad chunk's output and re-run. Backup remains.

### Step 4: verify live

```bash
# Run the regular audit on post-rewrite data
cd ../
python audit_live_full.py /opt/untitled-pick-game-api/data/categories.json
# Header SHA256 should differ from before; severity counts should be same
# (this fix doesn't touch trigger structure, only opener prose).

# Spot-check a few archetypes via API
curl -s https://isverifiedby.me/api/categories | python -c "
import json, sys
d = json.load(sys.stdin)
cats = d.get('categories') if isinstance(d, dict) else d
nf = next(c for c in cats if c['id'] == 'night_films')
tp = next(a for a in nf['archetypes'] if a['name'] == 'Тёмная психология')
print(tp['body'][:200])
"
# Should NOT start with «Джокер, Таксист, Тёмный рыцарь, Семь.»
```

## Estimated effort

- Chunker: ~2 sec
- ~12-13 chunks × ~30 archetypes each = ~360 entries total
- Per chunk via Claude Sonnet: ~2-3 minutes generation
- Total: ~30-45 min wall-clock if sequential; ~5-10 min if parallel
- Apply: ~1 sec
- Total cost (Anthropic API): roughly $5-15 for full rewrite

## Rollback

```bash
ssh root@185.186.76.89 "cp /opt/untitled-pick-game-api/data/categories.json.bak.rewrite_p1.<timestamp> /opt/untitled-pick-game-api/data/categories.json"
```

(Backup name is printed at start of apply_rewrites.py output.)
