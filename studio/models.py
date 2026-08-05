import base64
import hashlib
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def _fernet(secret=None):
    digest = hashlib.sha256((secret or settings.DATA_ENCRYPTION_SECRET).encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


class AIConfiguration(models.Model):
    name = models.CharField("Название", max_length=100, default="Google Gemini")
    model_name = models.CharField("Модель", max_length=100, default="gemini-3.5-flash")
    api_key_encrypted = models.TextField("API-ключ (зашифрован)", blank=True, editable=False)
    temperature = models.FloatField("Температура", default=0.1)
    timeout_seconds = models.PositiveIntegerField("Таймаут, секунд", default=180)
    system_prompt = models.TextField(
        "Общая инструкция агенту",
        default=("Ты — эксперт по распознаванию официальных документов. Извлекай только подтверждённые "
                 "сканом данные, переводи текстовые значения на русский язык и не выдумывай отсутствующие сведения."),
    )
    is_active = models.BooleanField("Активна", default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "настройка ИИ"
        verbose_name_plural = "настройки ИИ"

    def __str__(self):
        return f"{self.name} · {self.model_name}"

    def set_api_key(self, value):
        if value:
            self.api_key_encrypted = _fernet().encrypt(value.strip().encode()).decode()

    def get_api_key(self):
        if not self.api_key_encrypted:
            return ""
        for secret in [settings.DATA_ENCRYPTION_SECRET, *settings.DATA_ENCRYPTION_SECRET_FALLBACKS]:
            try:
                return _fernet(secret).decrypt(self.api_key_encrypted.encode()).decode()
            except InvalidToken:
                continue
        raise ValidationError("Не удалось расшифровать API-ключ. Проверьте DATA_ENCRYPTION_SECRET и его fallback-значения.")

    def save(self, *args, **kwargs):
        if self.is_active:
            AIConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class DocumentTemplate(models.Model):
    name = models.CharField("Название шаблона", max_length=180)
    description = models.TextField("Описание", blank=True)
    file = models.FileField("DOCX с переменными Jinja", upload_to="templates/")
    extraction_prompt = models.TextField(
        "Дополнительная инструкция для этого шаблона",
        blank=True,
        help_text="Например: формат дат, особенности печатей, правила транслитерации.",
    )
    is_active = models.BooleanField("Доступен для загрузки", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "шаблон документа"
        verbose_name_plural = "шаблоны документов"

    def __str__(self):
        return self.name

    def clean(self):
        if self.file and Path(self.file.name).suffix.lower() != ".docx":
            raise ValidationError({"file": "Загрузите шаблон в формате DOCX."})


class TemplateVariable(models.Model):
    template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE, related_name="variables", verbose_name="Шаблон")
    name = models.CharField("Имя Jinja-переменной", max_length=120)
    label = models.CharField("Название поля", max_length=180)
    ai_instruction = models.TextField("Что искать на скане", blank=True)
    translate_to_russian = models.BooleanField("Перевести на русский", default=True)
    required = models.BooleanField("Обязательное", default=False)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = [("template", "name")]
        verbose_name = "переменная шаблона"
        verbose_name_plural = "переменные шаблона"

    def __str__(self):
        return f"{self.label} ({{{{ {self.name} }}}})"

    def clean(self):
        import re
        if self.name and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.name):
            raise ValidationError({"name": "Используйте латинские буквы, цифры и подчёркивание; не начинайте с цифры."})


class SourceDocument(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Загружен"
        PROCESSING = "processing", "Обрабатывается"
        REVIEW = "review", "На проверке"
        READY = "ready", "Готов"
        ERROR = "error", "Ошибка"

    title = models.CharField("Название документа", max_length=220)
    template = models.ForeignKey(DocumentTemplate, on_delete=models.PROTECT, related_name="documents", verbose_name="Шаблон")
    source_pdf = models.FileField("Скан PDF", upload_to="scans/%Y/%m/")
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.UPLOADED)
    extracted_data = models.JSONField("Результат ИИ", default=dict, blank=True)
    edited_data = models.JSONField("Отредактированные данные", default=dict, blank=True)
    generated_docx = models.FileField("Готовый DOCX", upload_to="results/%Y/%m/", blank=True)
    generated_pdf = models.FileField("PDF для предпросмотра", upload_to="results/%Y/%m/", blank=True)
    error_message = models.TextField("Ошибка", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "обрабатываемый документ"
        verbose_name_plural = "обрабатываемые документы"

    def __str__(self):
        return self.title

    @property
    def values(self):
        return self.edited_data or self.extracted_data or {}
