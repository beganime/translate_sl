#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/translate-sl"
ARCHIVE="/tmp/TranslateSL-deploy.zip"

if [[ -e "$APP_DIR" ]]; then
  echo "Refusing to overwrite existing $APP_DIR" >&2
  exit 1
fi
if [[ ! -f "$ARCHIVE" ]]; then
  echo "Archive not found: $ARCHIVE" >&2
  exit 1
fi

install -d -m 0755 "$APP_DIR"
python3 -m zipfile -e "$ARCHIVE" "$APP_DIR"

install -d -m 0750 "$APP_DIR/data" "$APP_DIR/data/staticfiles"
mv "$APP_DIR/db.sqlite3" "$APP_DIR/data/db.sqlite3"
mv "$APP_DIR/media" "$APP_DIR/data/media"
chown -R 10001:10001 "$APP_DIR/data"
chmod 0640 "$APP_DIR/data/db.sqlite3"

django_secret="$(openssl rand -hex 48)"
data_secret="$(openssl rand -hex 48)"
umask 077
{
  printf 'DJANGO_DEBUG=0\n'
  printf 'DJANGO_SECRET_KEY=%s\n' "$django_secret"
  printf 'DJANGO_ALLOWED_HOSTS=translate.manager-sl.ru\n'
  printf 'DJANGO_CSRF_TRUSTED_ORIGINS=https://translate.manager-sl.ru\n'
  printf 'DJANGO_SECURE_SSL_REDIRECT=1\n'
  printf 'DJANGO_SECURE_HSTS_SECONDS=31536000\n'
  printf 'DJANGO_LOG_LEVEL=INFO\n'
  printf 'DATA_ENCRYPTION_SECRET=%s\n' "$data_secret"
  printf 'OLD_DATA_ENCRYPTION_SECRET=dev-only-change-me-translate-sl\n'
  printf 'WORD_PDF_CONVERSION=0\n'
} > "$APP_DIR/.env.production"

install -d -m 0750 -o translatesl-deploy -g translatesl-deploy /var/backups/translate-sl
chmod 0755 "$APP_DIR/deploy/container-entrypoint.sh" "$APP_DIR/deploy/backup-container.sh"

cd "$APP_DIR"
docker compose -f docker-compose.production.yml config --quiet
echo "TranslateSL files and production environment are prepared."
