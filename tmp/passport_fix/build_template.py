import shutil
import sys
from pathlib import Path

from docx import Document


source = Path(sys.argv[1])
target = Path(sys.argv[2])
shutil.copy2(source, target)
document = Document(target)

# Exact run-level replacements preserve all spacing, line breaks, anchors,
# fonts and paragraph geometry from the approved reference document.
replacements = {
    (15, 2): "{{ view }}",
    (15, 6): "{{ passport }}",
    (17, 1): "{{ surname }}",
    (18, 1): "{{ name }}",
    (20, 1): "{{ national }}",
    (22, 1): "{{ date_of_birth }}",
    (22, 5): "{{ personal_passport }}",
    (24, 1): "{{ sex }}",
    (26, 1): "{{ passport_start }}",
    (28, 1): "{{ passport_end }}",
    (28, 6): "   {{ signature }}",
    (30, 1): "TKM{{ surname | upper }}",
    (30, 3): "{{ name | upper }}",
    (31, 1): "{{ passport_num | upper }}",
    (31, 3): "{{ passport_code | upper }}",
    (31, 9): "{{ alike | upper }}",
}

expected = {
    (15, 2): "P",
    (15, 6): "A1907243",
    (17, 1): "КЕРИМБЕРДИЕВА",
    (18, 1): "ГУЛЬБАНУ",
    (20, 1): "Туркменистан",
    (22, 1): "04.04.2004",
    (22, 5): "DZ00260305",
    (24, 1): "женский",
    (26, 1): "03.05.2022",
    (28, 1): "02.05.2027",
    (28, 6): "   подпись имеется",
    (30, 1): "TKMКЕРИМБЕРДИЕВА",
    (30, 3): "ГУЛЬБАНУ",
    (31, 1): "A1907243<",
    (31, 3): "2TKM0404044",
    (31, 9): "F2705020DZ00260305<<<<20",
}

for location, replacement in replacements.items():
    paragraph_index, run_index = location
    run = document.paragraphs[paragraph_index].runs[run_index]
    if run.text != expected[location]:
        raise RuntimeError(
            f"Reference mismatch at paragraph {paragraph_index}, run {run_index}: {run.text!r}"
        )
    run.text = replacement

document.save(target)
print(target)
