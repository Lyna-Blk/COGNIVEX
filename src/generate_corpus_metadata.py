"""
generate_corpus_metadata.py   (merged & updated version)
--------------------------------------------------------
ONE script that builds data/processed/corpus_metadata.json from:
1. data/corpus/                  source files (DCI / brand folders)
2. data/processed_corpus/        OCR / cleaned .md outputs
3. data/fiches_dci/              DCI fiches (ATC code, brands, sources...)
4. data/processed/corpus_audit_report.json
5. data/processed/ocr_pipeline_log.json

Run from the project root:
    .\\.venv\\Scripts\\python.exe src\\generate_corpus_metadata.py
"""

import re
import json
import hashlib
import unicodedata
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

# ----------------------------------------------------------------------------
# Paths (script lives in src/)
# ----------------------------------------------------------------------------
PROJECT_ROOT   = Path(__file__).resolve().parent.parent
CORPUS_ROOT    = PROJECT_ROOT / "data" / "corpus"
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed_corpus"
FICHES_ROOT    = PROJECT_ROOT / "data" / "fiches_dci"
PROCESSED_DIR  = PROJECT_ROOT / "data" / "processed"

AUDIT_JSON = PROCESSED_DIR / "corpus_audit_report.json"
LOG_JSON   = PROCESSED_DIR / "ocr_pipeline_log.json"
META_JSON  = PROCESSED_DIR / "corpus_metadata.json"

JUNK_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}
IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff", "avif"}

# Authority of the sources written inside a fiche (higher = more reliable)
SOURCE_LEVELS = {
    "anpp": 4, "miph": 4,
    "ansm": 3, "who": 3, "oms": 3, "ema": 3, "dailymed": 3,
    "dzair pharma": 1, "dzair-pharma": 1, "pharmnet": 1, "dwa dz": 1,
}


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def normalize_key(name: str) -> str:
    """Accent/case/punctuation-insensitive key. '+' and 'et' are treated the same."""
    s = unicodedata.normalize("NFKD", str(name or ""))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.casefold().replace("+", " et ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def load_json_safe(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel_to_project(path: Path) -> str:
    """Project-relative POSIX path (portable between teammates)."""
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def is_junk(path: Path) -> bool:
    n = path.name.lower()
    return n in JUNK_NAMES or n.startswith("~$") or n.startswith(".")


# ----------------------------------------------------------------------------
# Fiche DCI parsing (supports both list and Markdown-table fiches)
# ----------------------------------------------------------------------------
def extract_field(content: str, label_pattern: str):
    m = re.search(
        rf"^\s*-\s*\**\s*{label_pattern}\s*\**\s*:\s*(.+)$",
        content, flags=re.MULTILINE | re.IGNORECASE,
    )
    if not m:
        return None
    val = m.group(1).strip()
    return re.sub(r"^\*\*|\*\*$", "", val).strip()


def parse_fiche(content: str) -> dict:
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    code_atc = extract_field(content, r"Code\s+ATC") or "Non renseigné"
    present_miph = (
        extract_field(content, r"Pr[ée]sence\s+dans\s+la\s+nomenclature\s+MIPH")
        or "Non renseigné"
    )
    version_miph = (
        extract_field(content, r"Version\s+consult[ée]e\s+et\s+date")
        or "Non renseigné"
    )

    products, seen = [], set()
    skip_words = (
        "code atc", "presence dans la nomenclature", "version consultee",
        "noms commerciaux", "requetes en majuscules", "methode et date",
        "resultat", "source", "miph", "anpp", "ansm", "rcp", "notice",
        "nom commercial", "specialite", "marque", "forme", "dosage", "laboratoire"
    )

    def clean_cell(val: str) -> str:
        v = re.sub(r"\*+", "", val or "").strip()
        v = re.sub(r"\s+", " ", v)
        return v

    def add_product(brand: str, form: str, dosage: str, lab: str = ""):
        brand = clean_cell(brand)
        form = clean_cell(form)
        dosage = clean_cell(dosage)
        lab = clean_cell(lab)

        if not brand or not form:
            return
        if brand.startswith("[") and brand.endswith("]"):
            return
        nb = normalize_key(brand)
        if not nb or any(k in nb for k in skip_words):
            return

        key = (nb, normalize_key(form), normalize_key(dosage))
        if key not in seen:
            seen.add(key)
            item = {"brand": brand, "form": form, "dosage": dosage}
            if lab and lab not in {"-", "—", "–", "/", "N/A", "Non renseigné"}:
                item["laboratoire"] = lab
            products.append(item)

    lines = content.splitlines()

    # 1) Parse ALL Markdown tables in the fiche
    for line in lines:
        s = line.strip()
        if "|" not in s:
            continue
        inner = s[1:-1] if (s.startswith("|") and s.endswith("|")) else s
        cells = [c.strip() for c in inner.split("|")]
        if len(cells) < 3:
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        lab = cells[3] if len(cells) >= 4 else ""
        add_product(cells[0], cells[1], cells[2], lab)

    # 2) Parse bullet-list products: - BRAND — FORM — DOSAGE (— LAB)
    for line in lines:
        m = re.match(r"^\s*[-*]\s+(.+)$", line)
        if not m:
            continue
        body = re.sub(r"\*+", "", m.group(1)).strip()
        parts = [p.strip() for p in re.split(r"\s+[—–-]\s+", body) if p.strip()]
        if len(parts) >= 3:
            lab = parts[3] if len(parts) >= 4 else ""
            add_product(parts[0], parts[1], parts[2], lab)

    # 3) Extract section under "## Sources consultées" line by line
    sources = []
    in_sources = False
    for line in lines:
        s = line.strip()
        if re.match(r"^##\s+Sources\s+consult[ée]es\b", s, flags=re.IGNORECASE):
            in_sources = True
            continue
        if in_sources and re.match(r"^##\s+", s):
            break
        if in_sources:
            m = re.match(r"^[-*]\s+(.+)$", s)
            if m:
                item = m.group(1).strip()
                if item.startswith("[") and item.endswith("]"):
                    item = item[1:-1].strip()
                item = re.sub(r"\*+", "", item).strip()
                if item and not normalize_key(item).startswith(("source 1", "source 2", "source 3", "exemple")):
                    sources.append(item)

    # 4) Extract section under "## Précision" line by line
    remarques_list = []
    in_precision = False
    for line in lines:
        s = line.strip()
        if re.match(r"^##\s+Pr[ée]cision\b", s, flags=re.IGNORECASE):
            in_precision = True
            continue
        if in_precision and re.match(r"^##\s+", s):
            break
        if in_precision and s and not re.match(r"^-{3,}$", s):
            clean_l = re.sub(r"^[-*]\s+", "", s)
            clean_l = re.sub(r"\*+", "", clean_l).strip()
            if clean_l:
                remarques_list.append(clean_l)
    remarques = " | ".join(remarques_list)

    # 5) Authority level
    level = 0
    for txt in list(sources) + [present_miph, version_miph]:
        nt = normalize_key(txt)
        for name, lv in SOURCE_LEVELS.items():
            if normalize_key(name) in nt and lv > level:
                level = lv

    return {
        "code_atc": code_atc,
        "present_dans_miph": present_miph,
        "version_nomenclature": version_miph,
        "authority_level": level,
        "sources": sources,
        "remarques": remarques,
        "produits": products,
    }


def index_fiches(fiches_dir: Path) -> list:
    fiches = []
    if not fiches_dir.exists():
        return fiches
    for md in sorted(fiches_dir.rglob("*.md")):
        if not md.is_file() or is_junk(md):
            continue
        content = md.read_text(encoding="utf-8", errors="replace")
        sections = [l.lstrip("#").strip() for l in content.splitlines()
                    if re.match(r"^#{1,4}\s+\S+", l)]
        title = re.search(r"^#\s*DCI\s*:\s*(.+)$", content, flags=re.MULTILINE | re.IGNORECASE)
        keys = {normalize_key(md.stem)}
        if title:
            keys.add(normalize_key(title.group(1)))
        fiches.append({
            "stem": md.stem,
            "path": rel_to_project(md),
            "chars": len(content),
            "sections": sections,
            "keys": keys,
            "parsed": parse_fiche(content),
            "matched": False,
        })
    return fiches


def find_fiche(fiches: list, dci_name: str):
    key = normalize_key(dci_name)
    for f in fiches:
        if key in f["keys"]:
            return f
    return None


# ----------------------------------------------------------------------------
# Provenance guess from file name / folder
# 1 = most reliable ... 6 = least
# ----------------------------------------------------------------------------
def classify_source(rel: str) -> dict:
    p = Path(rel)
    name = p.name.lower()
    parts = [x.lower() for x in p.parts]
    ext = p.suffix.lower().lstrip(".")

    if "documents_complementaires_non_reference" in parts:
        return {"source_type": "complementary_non_reference", "authority_tier": 5}
    if "anpp" in name or "anmdmr" in name:
        return {"source_type": "dz_official", "authority_tier": 1}
    if "dailymed" in name or "daily med" in name:
        return {"source_type": "us_dailymed", "authority_tier": 3}
    if ext == "csv":
        return {"source_type": "nomenclature_export", "authority_tier": 2}
    if name.startswith("source") or ext == "md" or "dwadz" in name or name.startswith("dwa"):
        return {"source_type": "dz_professional_site", "authority_tier": 4}
    if name.startswith("article"):
        return {"source_type": "scientific_article", "authority_tier": 6}
    if "ansm" in name:
        return {"source_type": "fr_institutional", "authority_tier": 3}
    if ext in IMAGE_EXTS:
        return {"source_type": "product_image", "authority_tier": 6}
    return {"source_type": "label_country_unverified", "authority_tier": 2}


def guess_doc_type(name: str, ext: str) -> str:
    n = name.lower()
    if ext == "csv":
        return "nomenclature"
    if ext in IMAGE_EXTS:
        return "image"
    if n.startswith("rcp") or "_rcp" in n or " rcp" in n or "-rcp" in n or "rcp-" in n or "rcp." in n:
        return "rcp"
    if "notice" in n:
        return "notice"
    if n.startswith("article"):
        return "article"
    if "interaction" in n or "iteraction" in n or "interactiob" in n:
        return "interaction_page"
    if "generique" in n:
        return "generics_page"
    if n.startswith("source") or ext == "md":
        return "web_page"
    return "other"


def read_text_chars(md_path: Path) -> int:
    """Characters of the real text, without the front-matter header."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0
    if text.startswith("---"):
        parts = text.split("\n---\n", 1)
        if len(parts) == 2:
            text = parts[1]
    return len(text.strip())


def text_quality(ext: str, chars: int, pages, has_text_file: bool) -> str:
    if not has_text_file:
        return "no_text"
    if ext == "csv":
        return "structured_data"
    if ext in IMAGE_EXTS:
        return "image_short_text" if chars < 300 else "ok"
    if pages:
        return "low_text" if chars / pages < 100 else "ok"
    return "low_text" if chars < 500 else "ok"


# ----------------------------------------------------------------------------
# One record per source file
# ----------------------------------------------------------------------------
def build_file_record(src: Path, audit_map: dict, log_map: dict) -> dict:
    rel = src.relative_to(CORPUS_ROOT).as_posix()
    aud = audit_map.get(rel, {})
    lg = log_map.get(rel, {})
    ext = src.suffix.lower().lstrip(".")

    expected_md = PROCESSED_ROOT / Path(rel).with_suffix(".md")
    expected_same = PROCESSED_ROOT / Path(rel)

    processed = None
    if expected_md.exists():
        processed = expected_md
    elif ext == "csv" and expected_same.exists():
        processed = expected_same
    elif ext == "md":
        processed = src
    elif isinstance(lg.get("output"), str):
        cand = Path(lg["output"].replace("\\", "/"))
        if not cand.is_absolute():
            cand = PROJECT_ROOT / cand
        if cand.exists():
            processed = cand

    chars = 0
    if processed is not None and processed.suffix.lower() == ".md":
        chars = read_text_chars(processed)

    pages = aud.get("page_count")
    prov = classify_source(rel)

    return {
        "filename": src.name,
        "relative_path": rel,
        "extension": ext,
        "doc_type": guess_doc_type(src.name, ext),
        "source_type": prov["source_type"],
        "authority_tier": prov["authority_tier"],
        "size_bytes": src.stat().st_size,
        "hash_sha256": aud.get("hash_sha256") or sha256_of(src),
        "is_duplicate": False,
        "page_count": pages,
        "audit_status": aud.get("status", "unknown"),
        "audit_issues": aud.get("issues", []),
        "ocr_status": lg.get("status", "processed" if processed else "unprocessed"),
        "processed_path": rel_to_project(processed) if processed else None,
        "extracted_chars": chars,
        "text_quality": text_quality(ext, chars, pages, processed is not None),
    }


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def generate_metadata():
    audit_data = load_json_safe(AUDIT_JSON, {})
    log_data = load_json_safe(LOG_JSON, {"files": {}})

    audit_map = {e["path"]: e for e in audit_data.get("files", [])
                 if isinstance(e, dict) and e.get("path")}
    log_map = log_data.get("files", {}) if isinstance(log_data.get("files"), dict) else {}

    fiches = index_fiches(FICHES_ROOT)

    buckets = defaultdict(lambda: {"source_files": [], "brands": defaultdict(list)})
    root_files, all_records = [], []

    if CORPUS_ROOT.exists():
        for src in sorted(p for p in CORPUS_ROOT.rglob("*") if p.is_file() and not is_junk(p)):
            rec = build_file_record(src, audit_map, log_map)
            all_records.append(rec)
            parts = src.relative_to(CORPUS_ROOT).parts
            if len(parts) == 1:
                root_files.append(rec)
            elif len(parts) == 2:
                buckets[parts[0]]["source_files"].append(rec)
            else:
                buckets[parts[0]]["brands"]["/".join(parts[1:-1])].append(rec)

    by_hash = defaultdict(list)
    for r in all_records:
        by_hash[r["hash_sha256"]].append(r)
    duplicate_groups = []
    for h, group in by_hash.items():
        if len(group) > 1:
            duplicate_groups.append([g["relative_path"] for g in group])
            for g in group[1:]:
                g["is_duplicate"] = True

    corpus_entries = []
    dcis_with_fiche = 0
    for dci_name in sorted(buckets, key=normalize_key):
        b = buckets[dci_name]
        fiche = find_fiche(fiches, dci_name)
        if fiche:
            fiche["matched"] = True
            dcis_with_fiche += 1
            p = fiche["parsed"]
            fiche_obj = {
                "exists": True,
                "path": fiche["path"],
                "chars": fiche["chars"],
                "sections": fiche["sections"],
                "code_atc": p["code_atc"],
                "present_dans_miph": p["present_dans_miph"],
                "version_nomenclature": p["version_nomenclature"],
                "authority_level": p["authority_level"],
                "sources": p["sources"],
                "remarques": p["remarques"],
                "produits": p["produits"],
            }
        else:
            fiche_obj = {"exists": False, "path": None, "chars": 0, "sections": [],
                         "code_atc": None, "produits": []}

        brands = [{"brand": n, "files": b["brands"][n]} for n in sorted(b["brands"], key=normalize_key)]
        files = b["source_files"] + [f for br in brands for f in br["files"]]

        corpus_entries.append({
            "dci": dci_name,
            "normalized_dci": normalize_key(dci_name),
            "fiche_dci": fiche_obj,
            "stats": {
                "total_files": len(files),
                "files_with_text": sum(1 for f in files if f["processed_path"]),
                "low_text_files": sum(1 for f in files if f["text_quality"] == "low_text"),
                "brand_count": len(brands),
                "total_chars": sum(f["extracted_chars"] for f in files),
            },
            "source_files": b["source_files"],
            "brands": brands,
        })

    orphaned = [{"dci_stem": f["stem"], "path": f["path"], "chars": f["chars"],
                 "code_atc": f["parsed"]["code_atc"]}
                for f in fiches if not f["matched"]]

    total_chars = sum(r["extracted_chars"] for r in all_records)
    low_text = [r["relative_path"] for r in all_records if r["text_quality"] == "low_text"]

    metadata = {
        "_meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "corpus_root": rel_to_project(CORPUS_ROOT),
            "processed_corpus_root": rel_to_project(PROCESSED_ROOT),
            "fiches_dci_root": rel_to_project(FICHES_ROOT),
            "total_dcis": len(corpus_entries),
            "dcis_with_fiche": dcis_with_fiche,
            "dcis_without_fiche": len(corpus_entries) - dcis_with_fiche,
            "orphaned_fiches_count": len(orphaned),
            "root_files_count": len(root_files),
            "total_source_files": len(all_records),
            "total_processed_files": sum(1 for r in all_records if r["processed_path"]),
            "total_extracted_chars": total_chars,
            "low_text_files_count": len(low_text),
            "duplicate_groups_count": len(duplicate_groups),
        },
        "low_text_files": low_text,
        "duplicate_groups": duplicate_groups,
        "corpus": corpus_entries,
        "root_files": root_files,
        "orphaned_fiches_dci": orphaned,
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    META_JSON.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    m = metadata["_meta"]
    print("=" * 60)
    print("  COGNIVEX Unified Corpus Metadata Generated")
    print("=" * 60)
    print(f"  Output file            : {META_JSON}")
    print(f"  Total DCIs             : {m['total_dcis']}")
    print(f"  DCIs with fiche        : {m['dcis_with_fiche']}")
    print(f"  DCIs without fiche     : {m['dcis_without_fiche']}")
    print(f"  Orphaned fiches        : {m['orphaned_fiches_count']}")
    print(f"  Source files indexed   : {m['total_source_files']}")
    print(f"  Files with text linked : {m['total_processed_files']}")
    print(f"  Low-text files (check) : {m['low_text_files_count']}")
    print(f"  Duplicate groups       : {m['duplicate_groups_count']}")
    print(f"  Total extracted chars  : {m['total_extracted_chars']:,}")
    print("=" * 60)
    if low_text:
        print("  Low-text files:")
        for p in low_text:
            print("   -", p)
    if orphaned:
        print("  Orphaned fiches (no corpus folder):")
        for o in orphaned:
            print("   -", o["dci_stem"])


if __name__ == "__main__":
    generate_metadata()