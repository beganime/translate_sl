from pathlib import Path

from django import forms

from .models import SourceDocument


class UploadDocumentForm(forms.ModelForm):
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}

    class Meta:
        model = SourceDocument
        fields = ["title", "template", "source_pdf"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Например, Свидетельство — Иванов И.И."}),
            "source_pdf": forms.FileInput(attrs={"accept": ".pdf,.docx,.jpg,.jpeg,.png"}),
        }

    def clean_source_pdf(self):
        value = self.cleaned_data["source_pdf"]
        if Path(value.name).suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise forms.ValidationError("Поддерживаются PDF, DOCX, JPG и PNG.")
        if value.size > 50 * 1024 * 1024:
            raise forms.ValidationError("Размер файла не должен превышать 50 МБ.")
        return value


class DocumentReviewForm(forms.Form):
    title = forms.CharField(label="Название документа", max_length=220)

    def __init__(self, *args, document=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.document = document
        values = document.values if document else {}
        if document:
            self.fields["title"].initial = document.title
            for variable in document.template.variables.all():
                self.fields[f"var_{variable.name}"] = forms.CharField(
                    label=variable.label,
                    required=variable.required,
                    help_text=variable.ai_instruction,
                    initial=values.get(variable.name, ""),
                    widget=forms.Textarea(attrs={"rows": 2, "data-variable": variable.name}),
                )

    def variable_values(self):
        return {
            key.removeprefix("var_"): value
            for key, value in self.cleaned_data.items()
            if key.startswith("var_")
        }

