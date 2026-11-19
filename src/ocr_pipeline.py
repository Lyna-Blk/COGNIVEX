"""
ocr_pipeline.py  (v4 — PyMuPDF fitz + RapidOCR direct backend)
----------------------------------------------------------------
OCR + Cleaning pipeline for COGNIVEX data/corpus/ without pymupdf4llm.

- Scanned / image-heavy PDFs -> renders pages via fitz + RapidOCR -> .md
- Image files (.png/.jpg/...) -> RapidOCR direct -> .md
- Text-based PDFs            -> fitz text extraction + noise strip -> .md
- CSV files                  -> copied as-is (structured data)

Output mirror : data/processed_corpus/   (originals are NEVER modified)
Resumes safely: already-processed files are skipped automatically.
Output format : Markdown (.md)

Usage:
    python src/ocr_pipeline.py
"""

import sys
import json
import re
import time
import shutil
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

# -- Dependency guard ----------------------------------------------------------
try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        sys.exit("[ERROR] PyMuPDF is not installed. Run: python -m pip install pymupdf")

try:
    from PIL import Image
    import numpy as np
except ImportError:
    sys.exit("[ERROR] Pillow/numpy not installed. Run: python -m pip install pillow numpy")

try:
    from rapidocr_onnxruntime import RapidOCR
    _rapid_engine = RapidOCR()
    HAS_RAPID = True
except ImportError:
    HAS_RAPID = False
    print("[WARN] rapidocr_onnxruntime not found — will fall back to embedded PDF text only.")

# -- Paths ---------------------------------------------------------------------
PROJECT_ROOT   = Path(__file__).resolve().parent.parent
CORPUS_ROOT    = PROJECT_ROOT / "data" / "corpus"
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed_corpus"
PROCESSED_DIR  = PROJECT_ROOT / "data" / "processed"
AUDIT_JSON     = PROCESSED_DIR / "corpus_audit_report.json"
META_JSON      = PROCESSED_DIR / "corpus_metadata.json"
LOG_JSON       = PROCESSED_DIR / "ocr_pipeline_log.json"

if not AUDIT_JSON.exists() and (PROJECT_ROOT / "data" / "corpus_audit_report.json").exists():
    AUDIT_JSON = PROJECT_ROOT / "data" / "corpus_audit_report.json"

# -- Settings ------------------------------------------------------------------
PDF_RENDER_DPI        = 200
MIN_PAGE_TEXT_CHARS   = 80     # pages with fewer chars get OCR'd if RapidOCR is active

# -- Noise patterns to strip ---------------------------------------------------
NOISE_PATTERNS = [
    r"ANNEXE\s+I\s*\n?\s*RESUME DES CARACTERISTIQUES DU PRODUIT",
    r"Email\s*:\s*contact@ldmgroupe\.com",
    r"CONSTANTINE\s*:.*?(?:Khroub|Tél|Tel).*",
    r"Z\.I\s+Oued\s+Hamimime.*",
    r"Oued\s+Hamimime.*",
    r"ldmgroupe\.com",
]

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

# -- Console helpers -----------------------------------------------------------
def banner(msg):
    print("\n" + "=" * 60)
    print("  " + msg)
    print("=" * 60)

def step(msg):
    print("\n[>>] " + msg)

def ok(msg):
    print("  [OK]  " + msg)

def warn(msg):
    print("  [!!]  " + msg)

def progress(current, total, label):
    if total <= 0:
        return
    pct = int(current / total * 40)
    bar = "#" * pct + "-" * (40 - pct)
    print(f"\r  [{bar}] {current}/{total}  {label[:45]:<45}", end="", flush=True)


# =============================================================================
# OCR & extraction helpers
# =============================================================================

def ocr_np_image(img_rgb: np.ndarray) -> str:
    if not HAS_RAPID:
        return ""
    result, _ = _rapid_engine(img_rgb)
    if not result:
        return ""
    return "\n".join(item[1].strip() for item in result if len(item) > 1 and item[1].strip())


def ocr_image_to_text(img_path: Path) -> str:
    if not HAS_RAPID:
        return f"[RapidOCR not available — could not process {img_path.name}]"
    with Image.open(img_path) as im:
        img = np.array(im.convert("RGB"))
    return ocr_np_image(img)


def render_page_to_rgb(page) -> np.ndarray:
    pix = page.get_pixmap(dpi=PDF_RENDER_DPI)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        return np.array(Image.fromarray(img, mode="RGBA").convert("RGB"))
    if pix.n == 1:
        return np.array(Image.fromarray(img, mode="L").convert("RGB"))
    return img


def pdf_to_markdown_fitz(pdf_path: Path, force_ocr_all: bool = False) -> tuple[str, str]:
    """
    Extracts Markdown-like text from a PDF using PyMuPDF (fitz) + RapidOCR
    for scanned/low-text pages. Returns (markdown_text, method_used).
    """
    doc = fitz.open(str(pdf_path))
    pages_md = []
    ocr_pages = 0
    text_pages = 0

    try:
        for page_num, page in enumerate(doc, start=1):
            embedded = page.get_text("text").strip()
            use_ocr = HAS_RAPID and (force_ocr_all or len(embedded) < MIN_PAGE_TEXT_CHARS)

            if use_ocr:
                try:
                    rgb = render_page_to_rgb(page)
                    ocr_text = ocr_np_image(rgb).strip()
                except Exception as e:
                    ocr_text = f"[OCR page error: {e}]"
                chosen = ocr_text if len(ocr_text) >= len(embedded) else embedded
                if ocr_text:
                    ocr_pages += 1
                else:
                    text_pages += 1
            else:
                chosen = embedded
                text_pages += 1

            pages_md.append(f"## Page {page_num}\n\n{chosen}".strip())
    finally:
        doc.close()

    if ocr_pages > 0 and text_pages > 0:
        method = "fitz + RapidOCR (hybrid)"
    elif ocr_pages > 0:
        method = "fitz + RapidOCR (scanned)"
    else:
        method = "fitz embedded text"

    return "\n\n---\n\n".join(pages_md).strip(), method


def clean_noise(text: str, noise_patterns: list) -> str:
    clean = text
    for pat in noise_patterns:
        clean = re.sub(pat, "", clean, flags=re.IGNORECASE | re.MULTILINE)
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean.strip()


def build_noise_patterns_from_audit(audit: dict, file_rel: str) -> list:
    patterns = list(NOISE_PATTERNS)
    for entry in audit.get("files", []):
        if entry.get("path") == file_rel:
            for sample in entry.get("noise_samples", []):
                m = re.match(r'^"(.+?)"\s*\(x\d+\)$', sample, re.DOTALL)
                if m:
                    patterns.append(re.escape(m.group(1).strip()))
    return patterns


# =============================================================================
# Output writer
# =============================================================================

MD_HEADER = """\
---
source: "{source}"
dci: "{dci}"
brand: "{brand}"
method: "{method}"
processed: "{timestamp}"
chars: {chars}
---

"""

def write_md(out_path: Path, text: str, meta: dict):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = MD_HEADER.format(**meta, chars=len(text))
    out_path.write_text(header + text, encoding="utf-8")


def make_meta(src_path: Path, rel: str, method: str) -> dict:
    parts = Path(rel).parts
    return {
        "source":    src_path.resolve().as_posix(),
        "dci":       parts[0] if len(parts) > 0 else "unknown",
        "brand":     parts[1] if len(parts) > 1 else "root",
        "method":    method,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# Pipeline stages
# =============================================================================

def stage_ocr_pdfs(needs_ocr: list, log: dict) -> dict:
    step(f"Stage 1/3 — OCR {len(needs_ocr)} scanned/low-text PDFs via fitz + RapidOCR")
    processed = skipped = errors = 0

    for idx, rel in enumerate(needs_ocr, 1):
        src_path = CORPUS_ROOT / rel
        out_path = PROCESSED_ROOT / Path(rel).with_suffix(".md")
        progress(idx, len(needs_ocr), Path(rel).name)

        if not src_path.exists():
            warn(f"\n  Missing source file: {rel}")
            log["files"][rel] = {"status": "error", "error": "Source file not found"}
            errors += 1
            continue

        if out_path.exists() and out_path.stat().st_size > 100:
            skipped += 1
            log["files"][rel] = {"status": "skipped_existing", "output": out_path.resolve().as_posix()}
            continue

        t0 = time.time()
        try:
            md, method = pdf_to_markdown_fitz(src_path, force_ocr_all=True)
            meta = make_meta(src_path, rel, method)
            write_md(out_path, md, meta)
            elapsed = round(time.time() - t0, 1)
            log["files"][rel] = {
                "status":  "ocr_ok",
                "output":  out_path.resolve().as_posix(),
                "chars":   len(md),
                "seconds": elapsed,
            }
            processed += 1
        except Exception as e:
            warn(f"\n  ERROR on {rel}: {e}")
            log["files"][rel] = {"status": "error", "error": str(e)}
            errors += 1

    print()
    ok(f"PDFs — processed: {processed}  skipped (cached): {skipped}  errors: {errors}")
    return log


def stage_ocr_images(non_pdf_files: list, log: dict) -> dict:
    img_files = [f for f in non_pdf_files if Path(f).suffix.lower() in IMAGE_EXTS]
    step(f"Stage 2/3 — OCR {len(img_files)} image files via RapidOCR")
    processed = skipped = errors = 0

    for idx, rel in enumerate(img_files, 1):
        src_path = CORPUS_ROOT / rel
        out_path = PROCESSED_ROOT / Path(rel).with_suffix(".md")
        progress(idx, len(img_files), Path(rel).name)

        if not src_path.exists():
            warn(f"\n  Missing source file: {rel}")
            log["files"][rel] = {"status": "error", "error": "Source file not found"}
            errors += 1
            continue

        if out_path.exists() and out_path.stat().st_size > 50:
            skipped += 1
            log["files"][rel] = {"status": "skipped_existing", "output": out_path.resolve().as_posix()}
            continue

        t0 = time.time()
        try:
            text = ocr_image_to_text(src_path)
            meta = make_meta(src_path, rel, "RapidOCR direct image")
            write_md(out_path, text, meta)
            elapsed = round(time.time() - t0, 1)
            log["files"][rel] = {
                "status":  "ocr_ok",
                "output":  out_path.resolve().as_posix(),
                "chars":   len(text),
                "seconds": elapsed,
            }
            processed += 1
        except Exception as e:
            warn(f"\n  ERROR on {rel}: {e}")
            log["files"][rel] = {"status": "error", "error": str(e)}
            errors += 1

    print()
    ok(f"Images — processed: {processed}  skipped: {skipped}  errors: {errors}")
    return log


def stage_clean_valid_pdfs(valid_for_rag: list, audit: dict, log: dict) -> dict:
    step(f"Stage 3/3 — Extract + denoise {len(valid_for_rag)} text-based PDFs")
    processed = skipped = errors = 0

    for idx, rel in enumerate(valid_for_rag, 1):
        src_path = CORPUS_ROOT / rel
        out_path = PROCESSED_ROOT / Path(rel).with_suffix(".md")
        progress(idx, len(valid_for_rag), Path(rel).name)

        if not src_path.exists():
            warn(f"\n  Missing source file: {rel}")
            log["files"][rel] = {"status": "error", "error": "Source file not found"}
            errors += 1
            continue

        if out_path.exists() and out_path.stat().st_size > 100:
            skipped += 1
            log["files"][rel] = {"status": "skipped_existing", "output": out_path.resolve().as_posix()}
            continue

        noise = build_noise_patterns_from_audit(audit, rel)
        try:
            raw_md, method = pdf_to_markdown_fitz(src_path, force_ocr_all=False)
            clean = clean_noise(raw_md, noise)
            meta = make_meta(src_path, rel, f"{method} + noise strip ({len(noise)} patterns)")
            write_md(out_path, clean, meta)
            log["files"][rel] = {
                "status":                 "cleaned_ok",
                "output":                 out_path.resolve().as_posix(),
                "clean_chars":            len(clean),
                "noise_patterns_applied": len(noise),
            }
            processed += 1
        except Exception as e:
            warn(f"\n  ERROR on {rel}: {e}")
            log["files"][rel] = {"status": "error", "error": str(e)}
            errors += 1

    print()
    ok(f"Valid PDFs — processed: {processed}  skipped (cached): {skipped}  errors: {errors}")
    return log


def stage_copy_csvs(non_pdf_files: list, log: dict) -> dict:
    csv_files = [f for f in non_pdf_files if f.lower().endswith(".csv")]
    step(f"Bonus — Copying {len(csv_files)} CSV files as structured data")
    for rel in csv_files:
        src = CORPUS_ROOT / rel
        dst = PROCESSED_ROOT / rel
        if not src.exists():
            warn(f"Missing CSV: {rel}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        ok(f"Copied: {rel}")
        log["files"][rel] = {"status": "copied", "output": dst.resolve().as_posix()}
    return log


# =============================================================================
# corpus_metadata.json update (safe if not generated yet)
# =============================================================================

def update_metadata(log: dict):
    step("Updating corpus_metadata.json with processed text paths...")
    if not META_JSON.exists():
        warn(f"{META_JSON} not found yet — skipping metadata update.")
        return

    meta = json.loads(META_JSON.read_text(encoding="utf-8"))
    updated = 0

    for dci_entry in meta.get("corpus", []):
        for f in dci_entry.get("source_files", []):
            rel = f.get("relative_path") or f.get("path")
            if rel and rel in log["files"] and "output" in log["files"][rel]:
                f["processed_text_path"] = log["files"][rel]["output"]
                f["ocr_status"] = log["files"][rel]["status"]
                updated += 1
        for brand in dci_entry.get("brands", []):
            for f in brand.get("files", []):
                rel = f.get("relative_path") or f.get("path")
                if rel and rel in log["files"] and "output" in log["files"][rel]:
                    f["processed_text_path"] = log["files"][rel]["output"]
                    f["ocr_status"] = log["files"][rel]["status"]
                    updated += 1

    meta.setdefault("_meta", {})
    meta["_meta"]["ocr_pipeline_run"] = datetime.now(timezone.utc).isoformat()
    meta["_meta"]["processed_files"] = updated
    meta["_meta"]["processed_corpus_root"] = PROCESSED_ROOT.resolve().as_posix()
    meta["_meta"]["ocr_engine"] = "PyMuPDF (fitz) + RapidOCR"

    META_JSON.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    ok(f"Updated {updated} file entries in corpus_metadata.json")


# =============================================================================
# Verification
# =============================================================================

def verify_outputs(log: dict):
    step("Verifying outputs...")
    md_files = list(PROCESSED_ROOT.rglob("*.md"))
    csv_files = list(PROCESSED_ROOT.rglob("*.csv"))
    total_chars = sum(
        v.get("chars", v.get("clean_chars", 0))
        for v in log["files"].values()
        if isinstance(v, dict)
    )
    ok(f"Markdown files produced    : {len(md_files)}")
    ok(f"CSV files copied           : {len(csv_files)}")
    ok(f"Total characters extracted : {total_chars:,}")

    samples = [p for p in md_files if p.stat().st_size > 200][:3]
    if samples:
        print("\n  --- Spot-check (snippet of 3 files) ---")
        for p in samples:
            content = p.read_text(encoding="utf-8")
            snippet = content[200:350].replace("\n", " ").strip()
            print(f"  {p.name}: {repr(snippet[:120])}")


# =============================================================================
# Main
# =============================================================================

def main():
    banner("COGNIVEX OCR + Cleaning Pipeline  (fitz + RapidOCR)")
    print(f"  Corpus root   : {CORPUS_ROOT}")
    print(f"  Output root   : {PROCESSED_ROOT}")
    print(f"  Audit JSON    : {AUDIT_JSON}")
    print(f"  OCR engine    : {'RapidOCR (onnxruntime)' if HAS_RAPID else 'NOT AVAILABLE'}")
    print(f"  Output format : Markdown (.md)")
    print(f"  Resume mode   : ON")

    if not CORPUS_ROOT.exists():
        sys.exit(f"[ERROR] Corpus directory not found: {CORPUS_ROOT}")

    if not AUDIT_JSON.exists():
        sys.exit(f"[ERROR] Run `python src/audit_corpus.py` first — {AUDIT_JSON} not found.")

    audit      = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    needs_ocr  = audit.get("needs_ocr", [])
    valid_pdfs = audit.get("valid_for_rag", [])
    non_pdf    = audit.get("non_pdf_files", [])

    if LOG_JSON.exists():
        log = json.loads(LOG_JSON.read_text(encoding="utf-8"))
        already = sum(1 for v in log.get("files", {}).values() if v.get("status") != "error")
        print(f"\n  Resuming — {already} files already done, skipping them.")
    else:
        log = {"started_at": datetime.now(timezone.utc).isoformat(), "files": {}}

    log.setdefault("files", {})
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)
    t_total = time.time()

    log = stage_ocr_pdfs(needs_ocr, log)
    LOG_JSON.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

    log = stage_ocr_images(non_pdf, log)
    LOG_JSON.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

    log = stage_clean_valid_pdfs(valid_pdfs, audit, log)
    LOG_JSON.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

    log = stage_copy_csvs(non_pdf, log)
    LOG_JSON.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

    update_metadata(log)
    verify_outputs(log)

    elapsed = round(time.time() - t_total, 1)
    statuses = defaultdict(int)
    for v in log["files"].values():
        statuses[v.get("status", "unknown")] += 1

    total_chars = sum(
        v.get("chars", v.get("clean_chars", 0))
        for v in log["files"].values()
        if isinstance(v, dict)
    )

    banner("PIPELINE COMPLETE")
    print(f"  Total runtime       : {elapsed:.0f}s  ({elapsed/60:.1f} min)")
    print(f"  OCR ok              : {statuses['ocr_ok']}")
    print(f"  Cleaned ok          : {statuses['cleaned_ok']}")
    print(f"  Copied (CSV)        : {statuses['copied']}")
    print(f"  Skipped (cached)    : {statuses['skipped_existing']}")
    print(f"  Errors              : {statuses['error']}")
    print(f"  Total chars         : {total_chars:,}")
    print()
    print(f"  Clean .md files  -> {PROCESSED_ROOT}")
    print(f"  Pipeline log     -> {LOG_JSON}")
    print(f"  Updated metadata -> {META_JSON}")
    print("=" * 60)


if __name__ == "__main__":
    main()