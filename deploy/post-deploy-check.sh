#!/usr/bin/env bash
set -euo pipefail

install -m 0644 /tmp/translate-sl-backup.service /etc/systemd/system/translate-sl-backup.service
install -m 0644 /tmp/translate-sl-backup.timer /etc/systemd/system/translate-sl-backup.timer
systemctl daemon-reload
systemctl enable --now translate-sl-backup.timer
systemctl start translate-sl-backup.service
systemctl is-active translate-sl-backup.timer
find /var/backups/translate-sl -maxdepth 1 -type f -name 'translate-sl_*.tar.gz' -printf '%f %s bytes\n'

cd /opt/translate-sl
docker compose -f docker-compose.production.yml exec -T web python manage.py shell -c \
  'from studio.models import AIConfiguration, DocumentTemplate, SourceDocument; c=AIConfiguration.objects.filter(is_active=True).first(); print({"templates": DocumentTemplate.objects.count(), "documents": SourceDocument.objects.count(), "api_key_decrypts": bool(c and c.get_api_key())})'

docker compose -f docker-compose.production.yml exec -T web sh -c '
  set -eu
  file=$(find /app/media/results -type f -name "*.docx" | head -n 1)
  test -n "$file"
  rm -rf /tmp/lo-test
  mkdir -p /tmp/lo-test
  soffice --headless --convert-to pdf --outdir /tmp/lo-test "$file" >/tmp/lo-output.txt 2>&1
  find /tmp/lo-test -type f -name "*.pdf" -size +0c | grep -q .
  echo libreoffice_pdf_ok
'
