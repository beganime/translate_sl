#!/usr/bin/env bash
set -euo pipefail

for _ in 1 2 3 4 5 6; do
  status="$(docker inspect translatesl-web --format '{{.State.Health.Status}}')"
  [[ "$status" == "healthy" ]] && break
  sleep 5
done
[[ "$status" == "healthy" ]]

docker cp /tmp/test_production_login.py translatesl-web:/tmp/test_production_login.py
docker exec -w /app translatesl-web python /tmp/test_production_login.py
systemctl start translate-sl-backup.service
find /var/backups/translate-sl -maxdepth 1 -type f -name 'translate-sl_*.tar.gz' -printf '%T@ %f %s\n' | sort -nr | head -2
