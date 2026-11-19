
import json
import re
import unicodedata
import sys
from pathlib import Path

from openpyxl import load_workbook


# ============================================================
# PROJECT PATHS
# ============================================================

# This script is inside src/, so parent.parent = COGNIVEX/
ROOT = Path(__file__).resolve().parent.parent

EXCEL_FILE = (
    ROOT
    / "data"
    / "reference"
    / "Liste 40 medicaments.xlsx"
)

CORPUS_DIR = ROOT / "data" / "corpus"

OUTPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "corpus_metadataFinal.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

IGNORED_DIRS = {
    "fiches_dci",
    "processed",
    "reference",
    "documents_complementaires_non_reference",
}

FOLDER_ALIASES = {
    # Add aliases if Excel DCI names differ from corpus folder names.
    # "acide acetylsalicylique": "acide-acetylsalicylique",
}

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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize(value):
    """
    Normalize text:
    - Remove accents
    - Ignore uppercase/lowercase
    - Replace punctuation with spaces
    - Remove extra spaces
    """

    if value is None:
        return ""

    text = unicodedata.normalize("NFKD", str(value))

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = text.casefold()

    text = re.sub(r"[^a-z0-9]+", " ", text)

    return " ".join(text.split())


def text_value(value, fallback="Non renseigné dans l’Excel"):

    if value is None or str(value).strip() == "":
        return fallback

    return str(value).strip()


def find_column(headers, possible_names):
    """
    Find an Excel column using possible header names.
    """

    normalized_headers = {
        normalize(name): index
        for index, name in enumerate(headers)
    }

    for name in possible_names:

        index = normalized_headers.get(normalize(name))

        if index is not None:
            return index

    return None


# ============================================================
# FIND DCI FOLDER
# ============================================================

def find_dci_folder(dci):

    if not CORPUS_DIR.is_dir():
        return None

    wanted = normalize(dci)

    alias = FOLDER_ALIASES.get(wanted)

    if alias:

        candidate = CORPUS_DIR / alias

        if candidate.is_dir():
            return candidate

    ignored = {
        normalize(name)
        for name in IGNORED_DIRS
    }

    for folder in CORPUS_DIR.iterdir():

        if not folder.is_dir():
            continue

        if normalize(folder.name) in ignored:
            continue

        if normalize(folder.name) == wanted:
            return folder

    return None


# ============================================================
# FIND PRODUCT PDF FILES
# ============================================================

def get_product_pdfs(dci, brand):
    """
    Associate PDFs with a product only if the commercial name
    appears in the PDF path.
    """

    dci_folder = find_dci_folder(dci)

    if dci_folder is None:
        return []

    wanted_brand = normalize(brand)

    if not wanted_brand:
        return []

    pdfs = []

    for path in dci_folder.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() != ".pdf":
            continue

        path_text = normalize(" ".join(path.parts))

        if wanted_brand in path_text:

            pdfs.append(
                path.relative_to(ROOT).as_posix()
            )

    return sorted(pdfs)


# ============================================================
# EXTRACT URL
# ============================================================

def extract_url(source_text):
    """
    Extract a URL only if it is actually written in Excel.
    """

    match = re.search(
        r"https?://[^\s,;]+",
        source_text or "",
        flags=re.IGNORECASE
    )

    if not match:
        return "Non renseignée dans l’Excel"

    return match.group(0).rstrip(".)]}")


# ============================================================
# SOURCE AUTHORITY LEVEL
# ============================================================

def get_authority_level(source_text):
    """
    Return a configured source level if the source is recognized.
    0 means unknown, not necessarily unreliable.
    """

    source = normalize(source_text)

    for name, level in SOURCE_LEVELS.items():

        if normalize(name) in source:
            return level

    return 0


# ============================================================
# MAIN FUNCTION
# ============================================================

def main():

    print("\n" + "=" * 60)
    print("       COGNIVEX - CORPUS METADATA GENERATOR")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. CHECK PROJECT PATHS
    # --------------------------------------------------------

    print("\n[1/5] Checking project directories...")

    print("Project root:", PROJECT_ROOT)
    print("Excel file:", EXCEL_FILE)
    print("Corpus directory:", CORPUS_DIR)
    print("Output file:", OUTPUT_FILE)

    if not EXCEL_FILE.is_file():

        raise FileNotFoundError(
            "\nExcel introuvable !\n"
            f"Chemin recherché : {EXCEL_FILE}\n"
            "Vérifie que le fichier existe dans "
            "COGNIVEX/data/reference/"
        )

    if not CORPUS_DIR.is_dir():

        raise FileNotFoundError(
            "\nCorpus directory introuvable !\n"
            f"Chemin recherché : {CORPUS_DIR}"
        )

    print("\n[OK] Excel and corpus directories found.")

    # --------------------------------------------------------
    # 2. OPEN EXCEL
    # --------------------------------------------------------

    print("\n[2/5] Reading Excel file...")

    workbook = load_workbook(
        EXCEL_FILE,
        read_only=True,
        data_only=True
    )

    try:

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

            "dci": find_column(
                headers,
                ["DCI (nom de la substance)", "DCI"]
            ),

            "atc_indicatif": find_column(
                headers,
                ["Code ATC (indicatif)", "Code ATC"]
            ),

            "atc_confirme": find_column(
                headers,
                ["ATC confirmé"]
            ),

            "presence": find_column(
                headers,
                ["Présent dans la nomenclature algérienne ?"]
            ),

            "brand": find_column(
                headers,
                [
                    "N,C",
                    "Nom commercial",
                    "Nom commercial (N,C)"
                ]
            ),

            "form": find_column(
                headers,
                ["Forme"]
            ),

            "dosage": find_column(
                headers,
                ["Dosage"]
            ),

            "sources": find_column(
                headers,
                ["Sources", "Source"]
            ),

            "remarques": find_column(
                headers,
                ["Remarques", "Remarque"]
            ),

            "classe": find_column(
                headers,
                ["Classe"]
            ),

            "number": find_column(
                headers,
                ["N°", "N"]
            ),
        }

        if columns["dci"] is None:

            raise ValueError(
                "ما لقيتش عمود DCI. "
                "تحققي من عنوان العمود في Excel."
            )

        print("[OK] Excel headers detected.")

        # ----------------------------------------------------
        # 3. READ MEDICINE RECORDS
        # ----------------------------------------------------

        print("\n[3/5] Processing medicine records...")

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

            # Search for associated PDF files
            pdf_paths = get_product_pdfs(dci, brand)

            file_path = (
                pdf_paths[0]
                if pdf_paths
                else "Aucun PDF associé dans le corpus"
            )

            record = {

                "dci": dci,

                "brand": brand,

                "form": form,

                "dosage": dosage,

                "file_path": file_path,

                "file_paths": pdf_paths,

                "source_name": source_text,

                "source_url": extract_url(source_text),

                "collection_date": (
                    "À compléter : date réelle de consultation"
                ),

                "authority_level": get_authority_level(
                    source_text
                ),

                "atc_indicatif": text_value(
                    get("atc_indicatif")
                ),

                "atc_confirme": text_value(
                    get("atc_confirme")
                ),

                "present_dans_nomenclature": text_value(
                    get("presence")
                ),

                "classe": text_value(
                    get("classe")
                ),

                "remarques": text_value(
                    get("remarques")
                ),

                "numero_ligne_excel": excel_row_number,
            }

            records.append(record)

            print(
                f"   [{len(records)}] {dci} - {brand}"
            )

    finally:

        workbook.close()

    # --------------------------------------------------------
    # 4. CREATE OUTPUT DIRECTORY AND EXPORT JSON
    # --------------------------------------------------------

    print("\n[4/5] Generating JSON metadata...")

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            records,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # 5. FINAL SUMMARY
    # --------------------------------------------------------

    with_pdf = sum(
        bool(record["file_paths"])
        for record in records
    )

    without_pdf = len(records) - with_pdf

    print("\n[5/5] Generation completed.")

    print("\n" + "=" * 60)
    print("              GENERATION COMPLETE")
    print("=" * 60)

    print(f"Total medicine records : {len(records)}")

    print(f"Records with PDF       : {with_pdf}")

    print(f"Records without PDF    : {without_pdf}")

    print("\nJSON file created:")
    print(OUTPUT_FILE)

    print("\n" + "=" * 60)


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":

    try:
        main()

    except Exception as error:

        print("\n[ERROR]", error)
        sys.exit(1)

