"""Restore canonical English typography in edited chunks (in place).

Editor systematically converted U+2014 (em-dash) → U+2013 (en-dash) and
also re-flowed numeric ranges through en-dash. We undo:
  - Pattern A: ` – `  → ` — `   (en-dash with spaces around → em-dash, parenthetical use)
  - Pattern B: \d–\d → \d-\d   (en-dash between digits → ASCII hyphen, range use)
  - Also catch: `[A-Za-zА-Я]–[A-Za-zА-Я]` mid-word → ASCII hyphen
  - Also catch: `15–60 sec`, `2-4` style ranges

Backup written to *.bak.typography_<ts>
"""
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

EDIT_DIR = Path('C:/Users/uncle/Claude/taste_twins/en_chunks/edited')

EM = '—'  # U+2014
EN = '–'  # U+2013
HY = '-'  # U+002D

def fix(text: str) -> tuple[str, dict]:
    counts = {'space_em': 0, 'digit_hyphen': 0, 'word_hyphen': 0}
    # Pattern A: en-dash bracketed by spaces → em-dash
    def _a(m):
        counts['space_em'] += 1
        return ' ' + EM + ' '
    text = re.sub(r' ' + EN + r' ', _a, text)
    # Pattern B: en-dash between digits → hyphen
    def _b(m):
        counts['digit_hyphen'] += 1
        return m.group(1) + HY + m.group(2)
    text = re.sub(r'(\d)' + EN + r'(\d)', _b, text)
    # Pattern C: en-dash between letters (no spaces) → hyphen
    def _c(m):
        counts['word_hyphen'] += 1
        return m.group(1) + HY + m.group(2)
    text = re.sub(r'([A-Za-zА-Яа-яЁё])' + EN + r'([A-Za-zА-Яа-яЁё])', _c, text)
    return text, counts


def main():
    ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    files = sorted(EDIT_DIR.glob('*.md'))
    grand = {'space_em': 0, 'digit_hyphen': 0, 'word_hyphen': 0, 'files': 0}
    for f in files:
        original = f.read_text(encoding='utf-8')
        new, counts = fix(original)
        if new == original:
            print(f'  {f.name}: no change')
            continue
        # Backup once per file
        bak = f.with_suffix(f'.md.bak.typography.{ts}')
        shutil.copy2(f, bak)
        f.write_text(new, encoding='utf-8')
        for k in counts:
            grand[k] += counts[k]
        grand['files'] += 1
        print(f'  {f.name}: space_em={counts["space_em"]}  digit_hyphen={counts["digit_hyphen"]}  word_hyphen={counts["word_hyphen"]}')
    print()
    print(f'Files patched: {grand["files"]}')
    print(f'Total space-em-dashes restored: {grand["space_em"]}')
    print(f'Total digit-hyphens restored:   {grand["digit_hyphen"]}')
    print(f'Total word-hyphens restored:    {grand["word_hyphen"]}')

if __name__ == '__main__':
    main()
