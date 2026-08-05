import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "translate_sl.settings")

import django

django.setup()

from studio.models import SourceDocument
from studio.services.rendering import render_document


VERIFIED = {
    23: {
        "medical_organization": "Марыйский велаятский центр профилактики СПИДа",
        "certificate_number": "870302",
        "patient_full_name": "Азадов Мухамметмырат",
        "examination_result": "Антитела к ВИЧ не обнаружены (результат отрицательный)",
        "citizenship": "Туркменистан",
        "destination_country": "Российская Федерация",
        "birth_date": "27.12.2008",
        "passport_number": "II MR 454561",
        "validity_period": "3 месяца",
        "issue_date": "29.04.2026",
        "doctor_name": "Оразмаммедова С. А.",
        "commission_chair_name": "",
        "seal_text": "Министерство здравоохранения и медицинской промышленности Туркменистана. Марыйский велаятский центр профилактики СПИДа. Для документов.",
    },
    24: {
        "medical_organization": "Вирусологическая лаборатория Службы санитарного надзора и контроля заболеваний Марыйского велаята",
        "report_number": "1410",
        "patient_full_name": "Атаев Мухамметмырат",
        "birth_date": "2008",
        "sex": "",
        "address": "Мургап, Гёкдепе",
        "additional_information": "",
        "hbsag_cutoff_od": "0,250",
        "hbsag_sample_od": "0,033",
        "hbsag_result": "отрицательный",
        "hbsag_report_number": "",
        "hbsag_test_date": "14.04.2026",
        "anti_hcv_cutoff_od": "0,360",
        "anti_hcv_sample_od": "0,131",
        "anti_hcv_result": "отрицательный",
        "anti_hcv_report_number": "",
        "anti_hcv_test_date": "14.04.2026",
        "result_issue_date": "14.04.2026",
        "performer": "подпись имеется",
        "department_head": "",
        "seal_text": "Министерство здравоохранения и медицинской промышленности Туркменистана. Служба санитарного надзора и контроля заболеваний Марыйского велаята. Вирусологическая лаборатория.",
    },
    25: {
        "stamp_health_authority": "Управление здравоохранения Марыйского велаята",
        "stamp_medical_organization": "Сакарчагинская этрапская больница",
        "stamp_number": "",
        "stamp_date": "",
        "medical_organization": "Сакарчагинская этрапская больница",
        "certificate_number": "267",
        "consultation_date": "14.07.2026",
        "issuer": "Сакарчагинская этрапская больница, консультативно-диагностическое отделение",
        "destination_institution": "-",
        "patient_full_name": "Азадов Мухамметмырат",
        "sex": "мужской",
        "birth_date": "27.12.2008",
        "address": "Марыйский велаят, Сакарчагинский этрап, генгешлик Солтаныз",
        "past_illnesses": "нет",
        "therapist": "здоров, подпись и печать имеются",
        "surgeon": "здоров, подпись и печать имеются",
        "neurologist": "практически здоров, подпись и печать имеются",
        "ophthalmologist": "острота зрения 1,0/1,0, здоров, подпись и печать имеются",
        "otolaryngologist": "здоров, подпись и печать имеются",
        "other_specialists": "",
        "narcologist": "на учёте не состоит",
        "psychiatrist": "на учёте не состоит",
        "dermatovenerologist": "",
        "xray_result": "лёгкие и сердце в норме, подпись имеется",
        "laboratory_result": "анализы крови и мочи в норме",
        "vaccinations": "прививки выполнены по плану; эпидемиологическое окружение спокойное",
        "commission_chair": "подпись имеется",
        "institution_head": "подпись имеется",
        "seal_text": "Министерство здравоохранения и медицинской промышленности Туркменистана. Управление здравоохранения Марыйского велаята. Сакарчагинская этрапская больница.",
    },
    26: {
        "medical_organization": "Лебапская велаятская противотуберкулёзная больница",
        "stamp_number": "3128",
        "stamp_date": "08.07.2016",
        "patient_full_name_dative": "Сувхановой Мехри Батыровне",
        "birth_year": "2007",
        "xray_date": "20.06.2024",
        "issue_date": "08.07.2024",
        "destination_country": "Россия",
        "chief_physician": "Ходжамбердиев Д. Р.",
        "seal_text": "Министерство здравоохранения и медицинской промышленности Туркменистана. Лебапское велаятское управление здравоохранения. Лебапская велаятская противотуберкулёзная больница.",
    },
}


for document_id, values in VERIFIED.items():
    document = SourceDocument.objects.get(pk=document_id)
    document.edited_data = values
    document.status = SourceDocument.Status.REVIEW
    document.error_message = ""
    document.save(update_fields=["edited_data", "status", "error_message", "updated_at"])
    render_document(document, values)
    print(f"Проверенные значения применены: документ #{document_id}")
