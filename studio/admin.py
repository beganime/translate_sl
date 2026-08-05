import re
import zipfile

from django import forms
from django.contrib import admin, messages

from .models import AIConfiguration, DocumentTemplate, SourceDocument, TemplateVariable


class AIConfigurationAdminForm(forms.ModelForm):
    api_key = forms.CharField(
        label="API-ключ Gemini",
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password"}),
        help_text="Оставьте пустым, чтобы сохранить текущий ключ. Ключ шифруется перед записью в БД.",
    )

    class Meta:
        model = AIConfiguration
        fields = ["name", "model_name", "api_key", "temperature", "timeout_seconds", "system_prompt", "is_active"]

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.cleaned_data.get("api_key"):
            obj.set_api_key(self.cleaned_data["api_key"])
        if commit:
            obj.save()
        return obj


@admin.register(AIConfiguration)
class AIConfigurationAdmin(admin.ModelAdmin):
    form = AIConfigurationAdminForm
    list_display = ["name", "model_name", "is_active", "has_key", "updated_at"]

    @admin.display(boolean=True, description="Ключ задан")
    def has_key(self, obj):
        return bool(obj.api_key_encrypted)


class TemplateVariableInline(admin.TabularInline):
    model = TemplateVariable
    extra = 1
    fields = ["sort_order", "name", "label", "ai_instruction", "translate_to_russian", "required"]


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "variable_count", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]
    inlines = [TemplateVariableInline]
    actions = ["discover_variables"]

    @admin.display(description="Переменных")
    def variable_count(self, obj):
        return obj.variables.count()

    @admin.action(description="Найти Jinja-переменные в выбранных DOCX")
    def discover_variables(self, request, queryset):
        created = 0
        for template in queryset:
            try:
                with zipfile.ZipFile(template.file.path) as archive:
                    xml = "\n".join(
                        archive.read(name).decode("utf-8", errors="ignore")
                        for name in archive.namelist()
                        if name.startswith("word/") and name.endswith(".xml")
                    )
                # Word may split a Jinja expression across runs/tags.
                plain = re.sub(r"<[^>]+>", "", xml)
                names = set(re.findall(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}", plain))
                for index, name in enumerate(sorted(names)):
                    _, was_created = TemplateVariable.objects.get_or_create(
                        template=template,
                        name=name,
                        defaults={"label": name.replace("_", " ").capitalize(), "sort_order": index * 10},
                    )
                    created += int(was_created)
            except Exception as exc:
                self.message_user(request, f"{template}: {exc}", level=messages.ERROR)
        self.message_user(request, f"Добавлено новых переменных: {created}", level=messages.SUCCESS)


@admin.register(TemplateVariable)
class TemplateVariableAdmin(admin.ModelAdmin):
    list_display = ["label", "name", "template", "translate_to_russian", "required", "sort_order"]
    list_filter = ["template", "translate_to_russian", "required"]
    search_fields = ["label", "name", "ai_instruction"]


@admin.register(SourceDocument)
class SourceDocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "template", "status", "created_at", "updated_at"]
    list_filter = ["status", "template"]
    search_fields = ["title"]
    readonly_fields = ["extracted_data", "edited_data", "error_message", "created_at", "updated_at"]

