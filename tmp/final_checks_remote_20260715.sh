#!/usr/bin/env bash
set -euo pipefail
cd /opt/translate-sl

sudo docker exec -u 0 translatesl-web rm -f /tmp/test_production_login.py

echo '=== container health ==='
sudo docker inspect --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' translatesl-web

echo '=== HTTP checks ==='
for path in / /accounts/login/ /admin/; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' "https://translate.manager-sl.ru${path}")
  echo "${path} ${code}"
done

echo '=== final database counts ==='
sudo docker compose -f docker-compose.production.yml exec -T web python manage.py shell -c "from django.contrib.auth import get_user_model; from studio.models import DocumentTemplate,SourceDocument,AIConfiguration; print({'templates':DocumentTemplate.objects.count(),'documents':SourceDocument.objects.count(),'users':get_user_model().objects.count(),'ai_configurations':AIConfiguration.objects.count()}); assert (DocumentTemplate.objects.count(),SourceDocument.objects.count(),get_user_model().objects.count(),AIConfiguration.objects.count())==(8,102,1,1)"

echo '=== recent errors ==='
sudo docker logs --since 15m translatesl-web > /tmp/translatesl-combined.log 2>&1
if grep -Ei 'Traceback|Internal Server Error|ERROR' /tmp/translatesl-combined.log > /tmp/translatesl-errors.txt; then
  cat /tmp/translatesl-errors.txt
  exit 1
fi
echo 'No traceback/Internal Server Error/ERROR in recent logs.'

echo '=== service inventory ==='
sudo docker ps --format '{{.Names}}|{{.Status}}' | sort
