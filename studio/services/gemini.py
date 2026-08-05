import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import requests
from django.conf import settings

from studio.models import AIConfiguration


class GeminiError(RuntimeError):
    pass


def _scan_parts(pdf_bytes):
    """Rasterize scan pages so Gemini can inspect handwriting at a useful scale."""
    executable = settings.PDFTOPPM_PATH
    if not executable and os.name == "nt":
        bundled = list(Path.home().glob(".cache/codex-runtimes/*/dependencies/native/poppler/Library/bin/pdftoppm.exe"))
        executable = str(bundled[0]) if bundled else ""
    executable = executable or shutil.which("pdftoppm")
    if not executable:
        return [{"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(pdf_bytes).decode("ascii")}}]

    parts = []
    total_bytes = 0
    try:
        with tempfile.TemporaryDirectory(prefix="translatesl-pages-") as temp_dir:
            temp = Path(temp_dir)
            pdf_path = temp / "scan.pdf"
            pdf_path.write_bytes(pdf_bytes)
            prefix = temp / "page"
            result = subprocess.run(
                [str(executable), "-jpeg", "-jpegopt", "quality=88", "-r", "200", str(pdf_path), str(prefix)],
                capture_output=True,
                timeout=180,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.decode(errors="replace")[:500])
            pages = sorted(temp.glob("page-*.jpg"), key=lambda path: int(path.stem.rsplit("-", 1)[1]))
            if not pages:
                raise RuntimeError("pdftoppm не создал изображения страниц")
            if len(pages) > 30:
                raise GeminiError("В одном PDF поддерживается не более 30 страниц.")
            for page_number, page in enumerate(pages, 1):
                image = page.read_bytes()
                total_bytes += len(image)
                if total_bytes > 15 * 1024 * 1024:
                    raise GeminiError("Скан слишком большой после подготовки страниц (более 15 МБ).")
                parts.append({"text": f"Страница скана {page_number} из {len(pages)}."})
                parts.append({"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(image).decode("ascii")}})
    except GeminiError:
        raise
    except Exception as exc:
        raise GeminiError(f"Не удалось подготовить страницы PDF для распознавания: {exc}") from exc
    return parts


def _response_schema(variables):
    properties = {}
    required = []
    for variable in variables:
        instruction = variable.ai_instruction or f"Значение поля «{variable.label}»"
        if variable.translate_to_russian:
            instruction += ". Верни значение на русском языке; имена собственные транслитерируй бережно."
        instruction += " Если значение не найдено, верни пустую строку."
        properties[variable.name] = {"type": "string", "description": instruction}
        required.append(variable.name)
    # The v1beta generateContent Schema proto does not accept the standard
    # JSON Schema additionalProperties keyword.
    return {"type": "object", "properties": properties, "required": required}


def extract_document(document):
    config = AIConfiguration.objects.filter(is_active=True).first()
    if not config:
        raise GeminiError("В админке нет активной настройки Gemini.")
    api_key = config.get_api_key()
    if not api_key:
        raise GeminiError("В активной настройке Gemini не указан API-ключ.")
    variables = list(document.template.variables.all())
    if not variables:
        raise GeminiError("У выбранного шаблона нет переменных для извлечения.")

    with document.source_pdf.open("rb") as stream:
        pdf_bytes = stream.read()

    prompt = "\n\n".join(filter(None, [
        config.system_prompt,
        document.template.extraction_prompt,
        f"Искомый тип документа: «{document.template.name}». PDF может содержать несколько разных документов, "
        "несколько разворотов и страницы в произвольном порядке. Сначала найди только страницы, относящиеся к "
        "указанному типу документа, объедини сведения со всех его страниц и полностью игнорируй остальные документы. "
        "Проанализируй выбранные страницы визуально и заполни все поля по JSON-схеме. "
        "Сохраняй номера, даты и суммы точно; не добавляй пояснений к значениям и не переноси данные из другого документа. "
        "Перед отправкой JSON выполни второй независимый визуальный проход по каждому заполненному полю. Особенно внимательно "
        "перепроверь рукописные ФИО, номера документов, десятичные показатели и все даты. Если год на бланке состоит из "
        "напечатанного префикса «20» и двух рукописных цифр, объедини их в четырёхзначный год, не заменяя цифры догадкой. "
        "Не сокращай имя и не копируй номер или дату из соседнего поля только потому, что целевое поле пустое.",
    ]))
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.model_name}:generateContent"
    )
    payload = {
        "contents": [{"parts": [*_scan_parts(pdf_bytes), {"text": prompt}]}],
        "generationConfig": {
            "temperature": config.temperature,
            "responseMimeType": "application/json",
            "responseSchema": _response_schema(variables),
        },
    }
    try:
        response = None
        for attempt in range(2):
            try:
                response = requests.post(
                    endpoint,
                    headers={"x-goog-api-key": api_key},
                    json=payload,
                    timeout=max(config.timeout_seconds, 300),
                )
            except (requests.Timeout, requests.ConnectionError):
                if attempt == 0:
                    time.sleep(3)
                    continue
                raise
            if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                retry_after = response.headers.get("Retry-After", "5")
                try:
                    delay = min(max(float(retry_after), 1), 30)
                except ValueError:
                    delay = 5
                time.sleep(delay)
                continue
            break
        if response is None:
            raise GeminiError("Gemini API не вернул ответ после повторной попытки.")
        response.raise_for_status()
        body = response.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
    except requests.RequestException as exc:
        detail = ""
        if getattr(exc, "response", None) is not None:
            detail = exc.response.text[:1200]
        raise GeminiError(f"Ошибка Gemini API: {exc}. {detail}") from exc
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise GeminiError("Gemini вернул ответ в неожиданном формате.") from exc
    return {variable.name: str(result.get(variable.name, "") or "") for variable in variables}
