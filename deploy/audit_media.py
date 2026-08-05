import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "translate_sl.settings")
sys.path.insert(0, "/app")

import django

django.setup()

from studio.models import DocumentTemplate, SourceDocument


missing = []
for document in SourceDocument.objects.all():
    for field_name in ("source_pdf", "generated_docx", "generated_pdf"):
        stored_file = getattr(document, field_name)
        if stored_file and not stored_file.storage.exists(stored_file.name):
            missing.append((str(document.pk), field_name, stored_file.name))

for template in DocumentTemplate.objects.all():
    if template.file and not template.file.storage.exists(template.file.name):
        missing.append((f"template:{template.pk}", "file", template.file.name))

print(repr(missing))
