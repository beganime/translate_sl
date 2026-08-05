import shutil
import subprocess
import tempfile
import os
from pathlib import Path

from django.conf import settings
from django.core.files import File
from docxtpl import DocxTemplate


class RenderError(RuntimeError):
    pass


def render_document(document, values=None):
    values = dict(values or document.values)
    if "аттестат" in document.template.name.lower():
        values = {key: (value if str(value).strip() else "-") for key, value in values.items()}
    output_name = f"document-{document.pk}.docx"
    with tempfile.TemporaryDirectory(prefix="translatesl-") as tmp:
        tmp_path = Path(tmp)
        docx_path = tmp_path / output_name
        template = DocxTemplate(document.template.file.path)
        template.render(values, autoescape=True)
        template.save(docx_path)
        if document.generated_docx:
            document.generated_docx.delete(save=False)
        if document.generated_pdf:
            document.generated_pdf.delete(save=False)
        with docx_path.open("rb") as stream:
            document.generated_docx.save(output_name, File(stream), save=False)

        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        pdf_path = docx_path.with_suffix(".pdf")
        if soffice:
            result = subprocess.run(
                [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(tmp_path), str(docx_path)],
                capture_output=True,
                text=True,
                timeout=120,
            )
        elif os.name == "nt" and settings.WORD_PDF_CONVERSION:
            script = settings.BASE_DIR / "scripts" / "convert_docx_to_pdf.ps1"
            subprocess.run(
                [
                    "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                    "-File", str(script), "-InputPath", str(docx_path), "-OutputPath", str(pdf_path),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        if pdf_path.exists():
            with pdf_path.open("rb") as stream:
                document.generated_pdf.save(pdf_path.name, File(stream), save=False)
        document.save(update_fields=["generated_docx", "generated_pdf", "updated_at"])
    return document


def process_document(document):
    from .gemini import extract_document

    document.status = document.Status.PROCESSING
    document.error_message = ""
    document.save(update_fields=["status", "error_message", "updated_at"])
    try:
        values = extract_document(document)
        document.extracted_data = values
        document.edited_data = values
        document.status = document.Status.REVIEW
        document.save(update_fields=["extracted_data", "edited_data", "status", "updated_at"])
        render_document(document, values)
    except Exception as exc:
        document.status = document.Status.ERROR
        document.error_message = str(exc)
        document.save(update_fields=["status", "error_message", "updated_at"])
        raise
    return document
