# Passport template fidelity contract

- Reference: `C:\Users\ThinkPad\Downloads\translates\Загранпаспорт — Гулбону Керимбердиева.docx`
- Working reference: `C:\Users\ThinkPad\Desktop\projects\TranslateSL\tmp\passport_fix\reference.docx`
- SHA-256: `6E50E837555281A030486360589BAF3C563B3F451BABFDB11212D1E148AE0291`
- Pages: 1; sections: 1.
- Page: A4 portrait, 8.27 × 11.69 in.
- Margins: left 1.18 in, right 0.59 in, top 0.79 in, bottom 0.79 in.
- Typography: preserve every reference run property; Times New Roman, data and MRZ lines 14 pt, labels 10 pt.
- Layout authority: all paragraph spacing, literal spaces, tabs, line breaks, drawing anchors and the photo rectangle come from the reference and must remain unchanged.
- Editable slots: view, passport, surname, name, national, date_of_birth, personal_passport, sex, passport_start, passport_end, signature, passport_num, passport_code, alike.
- Stable locations: body paragraphs 15, 17, 18, 20, 22, 24, 26, 28, 30 and 31 (zero-based indexes in `python-docx`), with replacements applied to the exact value runs only.
- MRZ surname and name must use Jinja `upper`; MRZ number/code/ending also use `upper`.
- Preserve-only package features: the VML photo rectangle, Word drawing anchor, section geometry, styles, theme, settings, relationships and all unchanged runs.
- Fidelity gates: one page; photo rectangle visible; upper values vertically under their labels; no text clipping; MRZ remains two bold lines; all reference furniture stays fixed.
