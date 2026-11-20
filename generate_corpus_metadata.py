import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORPUS_DIR = ROOT / "data"
FICHES_DIR = CORPUS_DIR / "fiches_dci"
OUTPUT_FILE = ROOT / "data" / "processed" / "corpus_metadata.json"

IGNORED_DIRS = {
    "processed",
    "reference",
    "documents_complementaires_non_reference",
}

SOURCE_LEVELS = {
    "anpp": 3,
    "miph": 3,
    "ansm": 3,
    "who": 3,
    "ema": 3,
    "dailymed": 3,
    "electronic medicines compendium": 3,
    "journal officiel": 3,
    "dzair pharma": 1,
    "dzair-pharma": 1,
    "pharmnet": 1,
    "dwa dz": 1,
}


def normalize(value):
    """Normalize text to simplify comparisons despite accents, hyphens, and casing."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def collect_corpus_pdfs(corpus_root, fiches_root, ignored_norm):
    """Collect all PDF files in the corpus outside the fiches folder and ignored directories."""
    if not corpus_root.is_dir():
        return []

    fiches_resolved = fiches_root.resolve() if fiches_root.exists() else None
    pdfs = []

    for pdf in sorted(corpus_root.rglob("*.pdf")):
        if fiches_resolved and fiches_resolved in pdf.resolve().parents:
            continue
        if any(normalize(part) in ignored_norm for part in pdf.parts):
            continue
        pdfs.append(pdf)

    return pdfs


def match_product_pdfs(all_pdfs, brand, dci):
    """Match PDF files belonging to the DCI or product to avoid mixing different drugs."""
    norm_dci = normalize(dci)
    norm_brand = normalize(brand)
    brand_tokens = [
        tok for tok in norm_brand.split() if not tok.isdigit() and len(tok) > 2
    ]

    # First collect PDFs associated with the DCI folder or DCI name itself
    dci_pdfs = []
    for pdf in all_pdfs:
        rel_posix = pdf.relative_to(ROOT).as_posix()
        norm_rel = normalize(rel_posix)
        if norm_dci and re.search(rf"(^| ){re.escape(norm_dci)}( |$)", norm_rel):
            dci_pdfs.append(rel_posix)

    if not dci_pdfs:
        return []

    # If files match the specific brand name within the DCI files, prefer them
    brand_specific = []
    for rel_posix in dci_pdfs:
        norm_rel = normalize(rel_posix)
        if norm_brand and norm_brand in norm_rel:
            brand_specific.append(rel_posix)
        elif brand_tokens and any(
            re.search(rf"(^| ){re.escape(tok)}( |$)", norm_rel) for tok in brand_tokens
        ):
            brand_specific.append(rel_posix)

    result = brand_specific if brand_specific else dci_pdfs
    return list(dict.fromkeys(result))


def extract_field(content, label_pattern):
    """Extract a field value whether formatted in bold (e.g., **Code ATC :**) or plain text."""
    match = re.search(
        rf"^\s*-\s*\**\s*{label_pattern}\s*\**\s*:\s*(.+)$",
        content,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    if not match:
        return None
    val = match.group(1).strip()
    val = re.sub(r"^\*\*|\*\*$", "", val).strip()
    return val


def parse_markdown_file(md_path):
    """Extract DCI metadata, actual product entries, and sources from a Markdown file."""
    content = md_path.read_text(encoding="utf-8")

    # 1. Extract DCI from the top-level heading
    title_match = re.search(
        r"^#\s*DCI\s*:\s*(.+)$", content, flags=re.MULTILINE | re.IGNORECASE
    )
    dci = title_match.group(1).strip().upper() if title_match else md_path.stem.upper()

    # 2. Extract core DCI fields
    code_atc = extract_field(content, r"Code\s+ATC") or "Non renseigné"
    present_miph = (
        extract_field(content, r"Pr[ée]sence\s+dans\s+la\s+nomenclature\s+MIPH")
        or "Non renseigné"
    )
    version_miph = (
        extract_field(content, r"Version\s+consult[ée]e\s+et\s+date")
        or "Non renseigné"
    )

    # 3. Extract actual products from the commercial names section
    products = []
    seen_products = set()

    products_section = re.search(
        r"^\s*-\s*\**\s*Noms\s+commerciaux[^\n]*\n(.*?)(?=^\s*-\s*\*\*|^\s*##\s+|\Z)",
        content,
        flags=re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    products_block = products_section.group(1) if products_section else content

    for brand_raw, form_raw, dosage_raw in re.findall(
        r"^\s*-\s+(.+?)\s+[—–-]\s+(.+?)\s+[—–-]\s+(.+?)\s*$",
        products_block,
        flags=re.MULTILINE,
    ):
        brand = brand_raw.strip()
        form = form_raw.strip()
        dosage = dosage_raw.strip()

        # Skip placeholders, headers, or source/document labels
        if "[" in brand or "]" in brand:
            continue
        if any(
            k in normalize(brand)
            for k in (
                "code atc",
                "presence dans la nomenclature",
                "version consultee",
                "noms commerciaux",
                "requetes en majuscules",
                "methode et date",
                "resultat",
                "source",
                "miph",
                "anpp",
                "ansm",
                "rcp",
                "notice",
            )
        ):
            continue

        key = (normalize(brand), normalize(form), normalize(dosage))
        if key not in seen_products:
            seen_products.add(key)
            products.append({
                "brand": brand,
                "form": form,
                "dosage": dosage,
            })

    # 4. Extract the "Sources consultées" section
    sources = []
    sources_section = re.search(
        r"^##\s*Sources\s+consult[ée]es\s*$(.*?)(?=^##\s+|\Z)",
        content,
        flags=re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    if sources_section:
        for line in re.findall(
            r"^\s*-\s+(.+)$", sources_section.group(1), flags=re.MULTILINE
        ):
            cleaned = line.strip()
            if cleaned and not (cleaned.startswith("[") and cleaned.endswith("]")):
                sources.append(cleaned)

    # 5. Extract the "Précision" section as remarks
    precision_section = re.search(
        r"^##\s*Pr[ée]cision\s*$(.*?)(?=^##\s+|\Z)",
        content,
        flags=re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    remarques = ""
    if precision_section:
        prec_lines = [
            re.sub(r"^\s*-\s*", "", l).strip()
            for l in precision_section.group(1).splitlines()
            if l.strip()
        ]
        remarques = " | ".join(prec_lines)

    return {
        "dci": dci,
        "code_atc": code_atc,
        "present_dans_miph": present_miph,
        "version_nomenclature": version_miph,
        "sources": sources,
        "remarques": remarques,
        "produits": products,
    }


def get_authority_level(sources):
    """Determine the highest authority level among the sources listed in a fiche."""
    max_level = 0
    for src in sources:
        norm_src = normalize(src)
        for name, level in SOURCE_LEVELS.items():
            if name in norm_src and level > max_level:
                max_level = level
    return max_level


def main():
    if not FICHES_DIR.is_dir():
        raise FileNotFoundError(f"Fiches directory not found: {FICHES_DIR}")

    ignored_norm = {normalize(name) for name in IGNORED_DIRS}
    all_pdfs = collect_corpus_pdfs(CORPUS_DIR, FICHES_DIR, ignored_norm)

    md_files = sorted(FICHES_DIR.rglob("*.md"))
    dci_records = []

    for md_path in md_files:
        parsed = parse_markdown_file(md_path)
        dci = parsed["dci"]
        sources = parsed["sources"]

        produits_with_files = []
        for prod in parsed["produits"]:
            pdfs = match_product_pdfs(all_pdfs, prod["brand"], dci)
            produit_entry = {
                "brand": prod["brand"],
                "form": prod["form"],
                "dosage": prod["dosage"],
            }

            if pdfs:
                produit_entry["file_paths"] = pdfs

            produits_with_files.append(produit_entry)

        dci_records.append({
            "dci": dci,
            "code_atc": parsed["code_atc"],
            "present_dans_miph": parsed["present_dans_miph"],
            "version_nomenclature": parsed["version_nomenclature"],
            "authority_level": get_authority_level(sources),
            "markdown_file": md_path.relative_to(ROOT).as_posix(),
            "sources": sources,
            "remarques": parsed["remarques"],
            "produits": produits_with_files,
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(dci_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    total_produits = sum(len(item["produits"]) for item in dci_records)
    print(f"JSON créé avec succès : {OUTPUT_FILE.relative_to(ROOT)}")
    print(f"Total des fiches / DCI générés : {len(dci_records)}")
    print(f"Total des produits extraits : {total_produits}")


if __name__ == "__main__":
    main()