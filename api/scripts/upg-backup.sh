#!/bin/bash
# UNTITLED PICK GAME — daily backup
#
# What:
#   - db.sqlite: atomic snapshot via sqlite3 .backup (safe with running app)
#   - categories.json: plain copy (file is rewritten atomically by app)
#   - Both gzipped, named with UTC timestamp
#
# Where: /var/backups/upg/
# Retention: 30 days (older files auto-deleted)
# Cron: daily at 03:17 UTC (offset to avoid hitting common busy times)
#
# Verify: ls -lah /var/backups/upg/ ; logger -t upg-backup messages
# Test:   sudo /usr/local/bin/upg-backup.sh

set -euo pipefail

BACKUP_DIR="/var/backups/upg"
DB_SRC="/opt/untitled-pick-game-api/data/db.sqlite"
JSON_SRC="/opt/untitled-pick-game-api/data/categories.json"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"  # contains user data — root-only

ts=$(date -u +%Y%m%d-%H%M%S)

# ─── SQLite backup (atomic, no lock) ──────────────────────────────
db_out="$BACKUP_DIR/db-${ts}.sqlite"
sqlite3 "$DB_SRC" ".backup '$db_out'"
gzip "$db_out"

# ─── categories.json (atomic copy then gzip) ──────────────────────
json_out="$BACKUP_DIR/categories-${ts}.json"
cp "$JSON_SRC" "$json_out"
gzip "$json_out"

# ─── Retention ────────────────────────────────────────────────────
find "$BACKUP_DIR" -type f -name 'db-*.sqlite.gz' -mtime +${RETENTION_DAYS} -delete
find "$BACKUP_DIR" -type f -name 'categories-*.json.gz' -mtime +${RETENTION_DAYS} -delete

# ─── Log ──────────────────────────────────────────────────────────
db_size=$(stat -c '%s' "${db_out}.gz")
json_size=$(stat -c '%s' "${json_out}.gz")
total_count=$(find "$BACKUP_DIR" -type f -name '*.gz' | wc -l)
logger -t upg-backup "OK ts=${ts} db=${db_size}b json=${json_size}b total_files=${total_count}"
