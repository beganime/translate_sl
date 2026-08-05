#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/translate-sl"
DATA_DIR="${APP_DIR}/data"
BACKUP_DIR="/var/backups/translate-sl"
STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
WORK_DIR="${BACKUP_DIR}/.${STAMP}"

mkdir -p "$WORK_DIR"
SOURCE_DB="${DATA_DIR}/db.sqlite3" TARGET_DB="${WORK_DIR}/db.sqlite3" python3 -c \
  'import os, sqlite3; source=sqlite3.connect(os.environ["SOURCE_DB"]); target=sqlite3.connect(os.environ["TARGET_DB"]); source.backup(target); target.close(); source.close()'
tar -C "$DATA_DIR" -czf "${WORK_DIR}/media.tar.gz" media
tar -C "$WORK_DIR" -czf "${BACKUP_DIR}/translate-sl_${STAMP}.tar.gz" db.sqlite3 media.tar.gz
rm -rf "$WORK_DIR"
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'translate-sl_*.tar.gz' -mtime +14 -delete
