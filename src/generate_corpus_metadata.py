import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parent
EXCEL_FILE = ROOT / "data" / "reference" / "Liste 40 medicaments.xlsx"
CORPUS_DIR = ROOT / "data" / "corpus"
OUTPUT_FILE = ROOT / "data" / "processed" / "corpus_metadataFinal.json"

IGNORED_DIRS = {
    "fiches_dci",
    "processed",
    "reference",
    "documents_complementaires_non_reference",
}

# أضيفي هنا الأسماء اللي تختلف بين Excel واسم dossier في corpus، إذا لزم.
FOLDER_ALIASES = {
    # "acide acetylsalicylique": "acide-acetylsalicylique",
}

# هذا المستوى يتعبّى فقط إذا كان مصدر Excel معروفًا.
# 0 يعني أن مستوى المصدر غير محدد، ماشي أنه مصدر غير موثوق.
SOURCE_LEVELS = {
    "anpp": 3,
    "miph": 3,
    "who": 3,
    "ema": 3,
    "dailymed": 3,
    "dzair pharma": 1,
    "pharmnet": 1,
    "dwa dz": 1,
}


def normalize(value):
    """يسهّل مقارنة الأسماء رغم اختلاف accents والشرطات والمسافات."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def text_value(value, fallback="Non renseigné dans l’Excel"):
    if value is None or str(value).strip() == "":
        return fallback
    return str(value).strip()


def find_column(headers, possible_names):
    """يقبل بعض الاختلافات البسيطة في أسماء أعمدة Excel."""
    normalized_headers = {normalize(name): index for index, name in enumerate(headers)}
    for name in possible_names:
        index = normalized_headers.get(normalize(name))
        if index is not None:
            return index
    return None


def find_dci_folder(dci):
    wanted = normalize(dci)
    alias = FOLDER_ALIASES.get(wanted)

    if alias:
        candidate = CORPUS_DIR / alias
        return candidate if candidate.is_dir() else None

    for folder in CORPUS_DIR.iterdir():
        if not folder.is_dir() or normalize(folder.name) in {
            normalize(name) for name in IGNORED_DIRS
        }:
            continue
        if normalize(folder.name) == wanted:
            return folder

    return None


def get_product_pdfs(dci, brand):
    """يربط PDF بالمنتج إذا ظهر DCI والاسم التجاري في مسار الملف."""
    dci_folder = find_dci_folder(dci)
    if dci_folder is None:
        return []

    wanted_brand = normalize(brand)
    pdfs = []

    for path in dci_folder.rglob("*.pdf"):
        path_text = normalize(" ".join(path.parts))

        # اربطي الملف بالاسم التجاري إذا كان موجودًا في المسار.
        # إذا ما كانش الاسم التجاري معروفًا، ما ننسبوش PDF عشوائيًا.
        if wanted_brand and wanted_brand in path_text:
            pdfs.append(path.relative_to(ROOT).as_posix())

    return pdfs


def extract_url(source_text):
    """يستخرج رابطًا فقط إذا كان مكتوبًا فعلًا في Excel."""
    match = re.search(r"https?://[^\s,;]+", source_text or "", flags=re.IGNORECASE)
    if not match:
        return "Non renseignée dans l’Excel"
    return match.group(0).rstrip(".)]}")


def get_authority_level(source_text):
    """يرجع مستوى معروفًا فقط إذا ذُكر مصدر معروف في Excel."""
    source = normalize(source_text)

    for name, level in SOURCE_LEVELS.items():
        if normalize(name) in source:
            return level

    return 0


def main():
    if not EXCEL_FILE.is_file():
        raise FileNotFoundError(
            f"Excel introuvable : {EXCEL_FILE}\n"
            "ضعيه في data/reference/Liste 40 medicaments.xlsx"
        )

    workbook = load_workbook(EXCEL_FILE, read_only=True, data_only=True)
    sheet = workbook.active
    rows = sheet.iter_rows(values_only=True)

    first_row = next(rows, None)
    if not first_row:
        raise ValueError("ملف Excel فارغ.")

    headers = [
        str(value).strip() if value is not None else ""
        for value in first_row
    ]

    columns = {
        "dci": find_column(headers, ["DCI (nom de la substance)", "DCI"]),
        "atc_indicatif": find_column(headers, ["Code ATC (indicatif)", "Code ATC"]),
        "atc_confirme": find_column(headers, ["ATC confirmé"]),
        "presence": find_column(
            headers,
            ["Présent dans la nomenclature algérienne ?"],
        ),
        "brand": find_column(headers, ["N,C", "Nom commercial", "Nom commercial (N,C)"]),
        "form": find_column(headers, ["Forme"]),
        "dosage": find_column(headers, ["Dosage"]),
        "sources": find_column(headers, ["Sources", "Source"]),
        "remarques": find_column(headers, ["Remarques", "Remarque"]),
        "classe": find_column(headers, ["Classe"]),
        "number": find_column(headers, ["N°", "N"]),
    }

    if columns["dci"] is None:
        raise ValueError(
            "ما لقيتش عمود DCI. تحققي من عنوان العمود في Excel."
        )

    records = []

    for excel_row_number, row in enumerate(rows, start=2):

        def get(field):
            index = columns.get(field)
            if index is None or index >= len(row):
                return None
            return row[index]

        dci_raw = get("dci")
        if dci_raw is None or not str(dci_raw).strip():
            continue

        dci = str(dci_raw).strip().upper()
        brand = text_value(get("brand"))
        form = text_value(get("form"))
        dosage = text_value(get("dosage"))
        source_text = text_value(get("sources"))

        pdf_paths = get_product_pdfs(dci, brand)

        # اسم الملف الأول في الحقل المطلوب، وجميع الملفات في الحقل الإضافي.
        file_path = pdf_paths[0] if pdf_paths else "Aucun PDF associé dans le corpus"

        records.append({
            "dci": dci,
            "brand": brand,
            "form": form,
            "dosage": dosage,
            "file_path": file_path,
            "file_paths": pdf_paths,
            "source_name": source_text,
            "source_url": extract_url(source_text),
            "collection_date": "À compléter : date réelle de consultation",
            "authority_level": get_authority_level(source_text),

            # معلومات أخرى موجودة في Excel
            "atc_indicatif": text_value(get("atc_indicatif")),
            "atc_confirme": text_value(get("atc_confirme")),
            "present_dans_nomenclature": text_value(get("presence")),
            "classe": text_value(get("classe")),
            "remarques": text_value(get("remarques")),
            "numero_ligne_excel": excel_row_number,
        })

    workbook.close()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"JSON créé : {OUTPUT_FILE.relative_to(ROOT)}")
    print(f"Lignes de médicaments exportées : {len(records)}")
    print(f"Lignes avec PDF associé : "
          f"{sum(bool(record['file_paths']) for record in records)}")
    print(f"Lignes sans PDF associé : "
          f"{sum(not record['file_paths'] for record in records)}")


if __name__ == "__main__":
    main()