from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from studio.models import DocumentTemplate, SourceDocument, TemplateVariable


ATTESTAT_VARIABLES = [
    ("seria_and_num", "Серия и номер", "Найди серию и номер аттестата целиком, например: А № 2354902.", False),
    ("fio", "Фамилия и имя", "Полное имя владельца. Транслитерируй на русский по данным документа и паспорта.", True),
    ("date_of_birth", "Дата рождения", "Дата рождения в формате ДД.ММ.ГГГГ.", False),
    ("city", "Место рождения", "Город, этрап, велаят или другое место рождения, полностью по-русски.", True),
    ("year", "Год окончания", "Год завершения обучения, только четыре цифры.", False),
    ("school_name", "Название школы", "Полное название и номер школы по-русски.", True),
    ("school_address", "Адрес школы", "Этрап, город и велаят школы по-русски.", True),
    ("turkmen_lang", "Туркменский язык", "Оценка с расшифровкой по-русски: 5 (отлично), 4 (хорошо) и т. п.", True),
    ("turkmen_literature", "Туркменская литература", "Оценка с русской расшифровкой.", True),
    ("russuian_lang", "Родной язык", "Оценка по предмету; пустая строка, если предмет не заполнен.", True),
    ("russian_literature", "Русская литература", "Оценка; пустая строка, если предмет не заполнен.", True),
    ("english_lang", "Английский язык", "Оценка с русской расшифровкой.", True),
    ("russian_lang", "Русский язык", "Оценка с русской расшифровкой.", True),
    ("algebra", "Алгебра и начала анализа", "Оценка с русской расшифровкой.", True),
    ("geometry", "Геометрия", "Оценка с русской расшифровкой.", True),
    ("informatics", "Информатика", "Оценка с русской расшифровкой.", True),
    ("communications", "Информационно-коммуникационные технологии", "Оценка с русской расшифровкой.", True),
    ("physics", "Физика", "Оценка с русской расшифровкой.", True),
    ("astronomy", "Астрономия", "Оценка с русской расшифровкой.", True),
    ("chemistry", "Химия", "Оценка с русской расшифровкой.", True),
    ("biology", "Биология", "Оценка с русской расшифровкой.", True),
    ("ecology", "Экология", "Оценка с русской расшифровкой.", True),
    ("geography", "География", "Оценка с русской расшифровкой.", True),
    ("history_turkmenistan", "История Туркменистана", "Оценка с русской расшифровкой.", True),
    ("world_history", "Всеобщая история", "Оценка с русской расшифровкой.", True),
    ("social_science", "Обществоведение", "Оценка с русской расшифровкой.", True),
    ("state_and_law", "Основы государства и права", "Оценка с русской расшифровкой.", True),
    ("economics", "Основы экономики", "Оценка с русской расшифровкой.", True),
    ("modern_technologies", "Основы современных технологий", "Оценка с русской расшифровкой.", True),
    ("modeling_and_graphics", "Моделирование и графика", "Оценка; пустая строка, если предмет не заполнен.", True),
    ("ethics", "Культура поведения", "Оценка с русской расшифровкой.", True),
    ("cultural_heritage", "Культурное наследие Туркменистана", "Оценка с русской расшифровкой.", True),
    ("world_culture", "Мировая культура", "Оценка с русской расшифровкой.", True),
    ("project_design", "Основы проектирования", "Оценка с русской расшифровкой.", True),
    ("physical_education", "Физкультура", "Оценка с русской расшифровкой.", True),
    ("life_safety", "Основы безопасности жизнедеятельности", "Оценка с русской расшифровкой.", True),
    ("behavior", "Поведение", "Характеристика поведения по-русски, например: примерное.", True),
    ("date_of_issue", "Дата выдачи", "Дата выдачи аттестата в формате ДД.ММ.ГГГГ.", False),
    ("seal_text", "Текст печати", "Переведи весь различимый текст круглой печати: ведомство, школа, этрап, город и велаят. Не используй данные другого шаблона.", True),
]

PASSPORT_VARIABLES = [
    ("view", "Вид документа", "Однобуквенный тип паспорта из машиносчитываемой зоны, обычно P.", False),
    ("passport", "Номер паспорта", "Номер паспорта с буквами и цифрами без пробелов.", False),
    ("surname", "Фамилия", "Фамилия владельца русскими буквами.", True),
    ("name", "Имя", "Имя владельца русскими буквами.", True),
    ("national", "Гражданство", "Гражданство по-русски.", True),
    ("date_of_birth", "Дата рождения", "Дата рождения в формате ДД.ММ.ГГГГ.", False),
    ("personal_passport", "Личный номер", "Персональный номер с документа без пробелов.", False),
    ("sex", "Пол", "Пол по-русски: женский или мужской.", True),
    ("passport_start", "Дата выдачи", "Дата выдачи в формате ДД.ММ.ГГГГ.", False),
    ("passport_end", "Дата окончания", "Дата истечения срока в формате ДД.ММ.ГГГГ.", False),
    ("signature", "Подпись владельца", "Верни «подпись имеется», если подпись видна, иначе пустую строку.", True),
    ("passport_num", "MRZ: номер паспорта", "Первые 9 символов номера паспорта в нижней машиносчитываемой строке.", False),
    ("passport_code", "MRZ: код", "Контрольная цифра и последующий MRZ-фрагмент после номера паспорта, точно как напечатано.", False),
    ("alike", "MRZ: окончание", "Оставшаяся часть второй строки MRZ после паспортного фрагмента, точно как напечатано.", False),
]

BIRTH_VARIABLES = [
    ("certificate_number", "Серия и номер свидетельства", "Серия и номер целиком, включая знак №.", False),
    ("child_full_name", "ФИО ребёнка", "Фамилия, имя и отчество русскими буквами в именительном падеже.", True),
    ("birth_date", "Дата рождения", "Дата рождения в формате ДД.ММ.ГГГГ.", False),
    ("birth_date_words", "Дата рождения прописью", "Полная дата рождения словами по-русски.", True),
    ("birth_place", "Место рождения", "Полное место рождения по-русски: населённый пункт, район, область и республика.", True),
    ("registration_date", "Дата регистрации", "Дата регистрации акта о рождении в формате ДД.ММ.ГГГГ.", False),
    ("record_number", "Номер актовой записи", "Только номер записи акта о рождении.", False),
    ("father_full_name", "Отец", "Полное имя отца русскими буквами.", True),
    ("father_nationality", "Национальность отца", "Национальность отца по-русски.", True),
    ("mother_full_name", "Мать", "Полное имя матери русскими буквами.", True),
    ("mother_nationality", "Национальность матери", "Национальность матери по-русски.", True),
    ("registration_office", "Орган регистрации", "Полное название и местонахождение ЗАГС по-русски.", True),
    ("issue_date", "Дата выдачи", "Дата выдачи свидетельства в формате ДД.ММ.ГГГГ.", False),
    ("seal_text", "Печать", "Верни «печать имеется», если печать видна; иначе пустую строку.", True),
]

INTERNAL_PASSPORT_VARIABLES = [
    ("full_name", "ФИО", "Фамилия, имя и отчество русскими буквами.", True),
    ("series_number", "Серия и номер", "Серия и номер внутреннего паспорта целиком.", False),
    ("birth_date", "Дата рождения", "Дата рождения в формате ДД.ММ.ГГГГ.", False),
    ("birth_place", "Место рождения", "Полное место рождения по-русски.", True),
    ("nationality", "Национальность", "Национальность по-русски.", True),
    ("issuer", "Кем выдан", "Полное название органа выдачи по-русски.", True),
    ("issue_date", "Дата выдачи", "Дата выдачи в формате ДД.ММ.ГГГГ.", False),
    ("seal_text", "Печать", "Переведи различимый текст печати или верни «печать имеется».", True),
    ("registration_authority_1", "Орган регистрации 1", "Орган, поставивший первый штамп о регистрации.", True),
    ("registration_address_1", "Адрес регистрации 1", "Первый адрес регистрации полностью по-русски.", True),
    ("registration_date_1", "Дата регистрации 1", "Дата первого штампа в формате ДД.ММ.ГГГГ.", False),
    ("registration_authority_2", "Орган регистрации 2", "Орган, поставивший второй штамп о регистрации.", True),
    ("registration_address_2", "Адрес регистрации 2", "Второй адрес регистрации полностью по-русски.", True),
    ("registration_date_2", "Дата регистрации 2", "Дата второго штампа в формате ДД.ММ.ГГГГ.", False),
    ("country_code", "Код страны", "Трёхбуквенный код страны, как на документе.", False),
    ("passport_number", "Номер на международной странице", "Номер паспорта с международной страницы.", False),
    ("surname", "Фамилия в MRZ", "Фамилия латиницей как на международной странице.", False),
    ("name", "Имя в MRZ", "Имя латиницей как на международной странице.", False),
    ("birth_place_short", "Краткое место рождения", "Место рождения с международной страницы по-русски.", True),
    ("sex", "Пол", "Однобуквенное значение пола M или F.", False),
    ("mrz_line_1", "MRZ строка 1", "Первая строка MRZ целиком, без пробелов, точно как напечатано.", False),
    ("mrz_line_2", "MRZ строка 2", "Вторая строка MRZ целиком, без пробелов, точно как напечатано.", False),
]


class Command(BaseCommand):
    help = "Import the two workspace templates and scans into the database"

    def handle(self, *args, **options):
        root = Path(settings.BASE_DIR)
        attestat_docx = root / "Аттестат_доделанный.docx"
        passport_docx = root / "Загран_доделанный_v2.docx"
        birth_docx = root / "Свидетельство_о_рождении_доделанный.docx"
        internal_docx = root / "Внутренний_паспорт_доделанный.docx"
        attestat_pdf = root / "аттестат Гулбону.PDF"
        passport_pdf = root / "гулбону загран.PDF"
        birth_pdf = root / "свид_о_рож_нужен_перевод.pdf"
        internal_pdf = root / "внутренний_пасспорт_нужен_перевод.pdf"
        for path in [attestat_docx, passport_docx, birth_docx, internal_docx, birth_pdf, internal_pdf]:
            if not path.exists():
                raise CommandError(f"Не найден файл: {path}")

        attestat = self._upsert_template(
            "Аттестат о среднем образовании",
            attestat_docx,
            ATTESTAT_VARIABLES,
            "Аттестат Туркменистана. Читай все три страницы одного разворота; сверяй туркменскую и английскую части. "
            "Рукописные оценки переводи по шкале: 5 — отлично, 4 — хорошо, 3 — удовлетворительно. "
            "Каждую строку предмета проверяй отдельно: не копируй оценку русского языка в пустые строки родного языка или литературы.",
        )
        passport = self._upsert_template(
            "Заграничный паспорт Туркменистана",
            passport_docx,
            PASSPORT_VARIABLES,
            "Паспорт на скане может быть повёрнут. Используй визуальную зону и MRZ для взаимной проверки значений.",
        )
        birth = self._upsert_template(
            "Свидетельство о рождении",
            birth_docx,
            BIRTH_VARIABLES,
            "Советское свидетельство о рождении с рукописными записями на русском и туркменском языках. "
            "Сверяй печатные подписи полей и рукописные значения; не путай дату рождения, регистрации и выдачи.",
        )
        internal = self._upsert_template(
            "Внутренний паспорт Туркменистана",
            internal_docx,
            INTERNAL_PASSPORT_VARIABLES,
            "Старый внутренний паспорт может занимать несколько отдельных сканов. Объедини данные основной страницы, "
            "русского перевода, регистрации и международной страницы. MRZ перепиши посимвольно.",
        )
        if attestat_pdf.exists():
            self._upsert_scan("Аттестат — Гулбону Керимбердиева", attestat, attestat_pdf)
        if passport_pdf.exists():
            self._upsert_scan("Загранпаспорт — Гулбону Керимбердиева", passport, passport_pdf)
        self._upsert_scan("Свидетельство о рождении — Максат Эйранлыев", birth, birth_pdf)
        self._upsert_scan("Внутренний паспорт — Максат Эйранлыев", internal, internal_pdf)
        self.stdout.write(self.style.SUCCESS("Четыре шаблона, переменные и четыре скана добавлены в базу."))

    def _upsert_template(self, name, path, variables, prompt):
        template, _ = DocumentTemplate.objects.get_or_create(name=name)
        template.description = f"Импортирован из {path.name}"
        template.extraction_prompt = prompt
        template.is_active = True
        with path.open("rb") as stream:
            template.file.save(path.name, File(stream), save=False)
        template.save()
        template.variables.all().delete()
        TemplateVariable.objects.bulk_create([
            TemplateVariable(
                template=template,
                name=variable,
                label=label,
                ai_instruction=instruction,
                translate_to_russian=translate,
                required=False,
                sort_order=index * 10,
            )
            for index, (variable, label, instruction, translate) in enumerate(variables, 1)
        ])
        return template

    def _upsert_scan(self, title, template, path):
        document, created = SourceDocument.objects.get_or_create(title=title, defaults={"template": template})
        document.template = template
        if created:
            document.status = SourceDocument.Status.UPLOADED
            document.error_message = ""
        with path.open("rb") as stream:
            document.source_pdf.save(path.name, File(stream), save=False)
        document.save()
        return document
