#!/usr/bin/env bash
set -euo pipefail

STAGE=/tmp/translatesl-release-20260715
case "$STAGE" in
  /tmp/translatesl-release-*) ;;
  *) echo "Unsafe stage path" >&2; exit 2 ;;
esac

echo "[1/5] Extracting release"
rm -rf "$STAGE"
mkdir -p "$STAGE"
python3 -m zipfile -e /tmp/TranslateSL-deploy.zip "$STAGE"
test -f "$STAGE/Dockerfile"
test -f "$STAGE/studio/management/commands/import_medical_templates.py"
test -f "$STAGE/медсправка_ВИЧ_шаблон.docx"

echo "[2/5] Updating application source"
sudo rsync -a --delete \
  --exclude='.env.production' \
  --exclude='data/' \
  --exclude='db.sqlite3' \
  --exclude='media/' \
  "$STAGE/" /opt/translate-sl/

echo "[3/5] Building web image"
cd /opt/translate-sl
sudo docker compose -f docker-compose.production.yml build web

echo "[4/5] Recreating web container"
sudo docker compose -f docker-compose.production.yml up -d --no-deps web

echo "[5/5] Waiting for healthcheck"
for _ in $(seq 1 30); do
  status=$(sudo docker inspect translatesl-web --format '{{.State.Health.Status}}' 2>/dev/null || true)
  echo "health=$status"
  if [ "$status" = healthy ]; then
    exit 0
  fi
  if [ "$status" = unhealthy ]; then
    sudo docker logs --tail 120 translatesl-web
    exit 1
  fi
  sleep 5
done

sudo docker logs --tail 120 translatesl-web
exit 1
