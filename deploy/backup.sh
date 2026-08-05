#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/translate-sl"
BACKUP_DIR="/var/backups/translate-sl"
STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
WORK_DIR="${BACKUP_DIR}/.${STAMP}"

mkdir -p "$WORK_DIR"
sqlite3 "${APP_DIR}/db.sqlite3" ".backup '${WORK_DIR}/db.sqlite3'"
tar -C "$APP_DIR" -czf "${WORK_DIR}/media.tar.gz" media
tar -C "$WORK_DIR" -czf "${BACKUP_DIR}/translate-sl_${STAMP}.tar.gz" db.sqlite3 media.tar.gz
rm -rf "$WORK_DIR"
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'translate-sl_*.tar.gz' -mtime +14 -delete
