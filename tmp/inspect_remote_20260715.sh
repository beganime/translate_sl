#!/usr/bin/env bash
set -euo pipefail
cd /opt/translate-sl
sudo docker compose -f docker-compose.production.yml exec -T web python manage.py shell -c "from studio.models import DocumentTemplate,SourceDocument; print('TEMPLATES',DocumentTemplate.objects.count()); print(list(DocumentTemplate.objects.values_list('id','name','template_file'))); print('DOCS',SourceDocument.objects.count()); print(list(SourceDocument.objects.order_by('-id').values_list('id','title','source_file')[:8]))"
