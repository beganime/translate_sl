#!/usr/bin/env bash
set -euo pipefail

cd /opt/translate-sl
COMPOSE=(sudo docker compose -f docker-compose.production.yml)

echo '=== django check ==='
"${COMPOSE[@]}" exec -T web python manage.py check

echo '=== migrations ==='
"${COMPOSE[@]}" exec -T web python manage.py migrate --noinput
"${COMPOSE[@]}" exec -T web python manage.py makemigrations --check --dry-run

echo '=== medical template import ==='
"${COMPOSE[@]}" exec -T web python manage.py import_medical_templates

echo '=== database and template integrity ==='
"${COMPOSE[@]}" exec -T web python manage.py shell -c "from django.contrib.auth import get_user_model; from docxtpl import DocxTemplate; from studio.models import DocumentTemplate,SourceDocument,AIConfiguration; expected={'Медицинский сертификат на ВИЧ (форма 082-1/у)','Результаты анализов на гепатит (HBsAg / Anti-HCV)','Медицинская справка 086/у','Справка противотуберкулёзной больницы'}; qs=DocumentTemplate.objects.filter(name__in=expected); assert qs.count()==4,(qs.count(),list(qs.values_list('name',flat=True))); assert DocumentTemplate.objects.count()==8,DocumentTemplate.objects.count(); assert SourceDocument.objects.count()==102,SourceDocument.objects.count(); assert get_user_model().objects.count()==1,get_user_model().objects.count(); c=AIConfiguration.objects.first(); assert c and bool(c.get_api_key()),'AI key missing or cannot be decrypted'; [(lambda disk,db,name: (_ for _ in ()).throw(AssertionError((name,disk,db))) if disk!=db else None)(set(DocxTemplate(t.file.path).get_undeclared_template_variables()),set(t.variables.values_list('name',flat=True)),t.name) for t in qs]; print({'templates':DocumentTemplate.objects.count(),'documents':SourceDocument.objects.count(),'users':get_user_model().objects.count(),'ai_configurations':AIConfiguration.objects.count(),'ai_key_decrypts':True,'medical_templates':sorted(qs.values_list('name',flat=True))})"

echo '=== document toolchain ==='
"${COMPOSE[@]}" exec -T web sh -c 'command -v pdftoppm; pdftoppm -v 2>&1 | head -n 1; command -v soffice; soffice --version | head -n 1'

echo '=== production login flow ==='
sudo docker cp /opt/translate-sl/deploy/test_production_login.py translatesl-web:/tmp/test_production_login.py
sudo docker exec -w /app translatesl-web python /tmp/test_production_login.py
sudo docker exec translatesl-web rm -f /tmp/test_production_login.py

echo '=== container health ==='
sudo docker inspect --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' translatesl-web

echo '=== HTTP checks ==='
for path in / /accounts/login/ /admin/; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' "https://translate.manager-sl.ru${path}")
  echo "${path} ${code}"
done

echo '=== recent errors ==='
if sudo docker logs --since 10m translatesl-web 2>&1 | grep -Ei 'Traceback|Internal Server Error|ERROR' >/tmp/translatesl-errors.txt; then
  cat /tmp/translatesl-errors.txt
  exit 1
fi
echo 'No traceback/Internal Server Error/ERROR in recent logs.'
