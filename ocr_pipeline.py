"""
ocr_pipeline.py  (v3 — pymupdf4llm + RapidOCR backend)
---------------------------------------------------------
Full OCR + Cleaning pipeline for COGNIVEX data/corpus/

  - 59 image-only PDFs  → pymupdf4llm.to_markdown() with RapidOCR → .md
  - 39 PNG screenshots  → RapidOCR direct → .md
  -  2 text-based PDFs  → pymupdf4llm.to_markdown() + noise strip → .md
  -  6 CSVs             → copied as-is (structured data)

Output mirror : data/processed_corpus/   (originals are NEVER modified)
Resumes safely: already-processed files are skipped automatically.
Output format : Markdown (.md) — better structured for RAG chunking.

Usage:
    python ocr_pipeline.py
"""

import sys
import json
import re
import time
import shutil
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

# ── Dependency guard ──────────────────────────────────────────────────────────
try:
    import pymupdf as fitz
except ImportError:
    import fitz

try:
    import pymupdf4llm
except ImportError:
    sys.exit("[ERROR] pymupdf4llm not installed. Run: python -m pip install pymupdf4llm")

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
    print("[WARN] rapidocr_onnxruntime not found — will fall back to embedded text only.")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT           = Path(__file__).parent
CORPUS_ROOT    = ROOT / "data" / "corpus"
PROCESSED_ROOT = ROOT / "data" / "processed_corpus"
AUDIT_JSON     = ROOT / "data" / "corpus_audit_report.json"
META_JSON      = ROOT / "data" / "corpus_metadata.json"
LOG_JSON       = ROOT / "data" / "ocr_pipeline_log.json"

# ── Settings ──────────────────────────────────────────────────────────────────
PDF_RENDER_DPI = 200     # DPI for rendering PDF pages to images for OCR

# ── Noise patterns to strip from the 2 valid text PDFs ───────────────────────
NOISE_PATTERNS = [
    r"ANNEXE\s+I\s*\n?\s*RESUME DES CARACTERISTIQUES DU PRODUIT",
    r"Email\s*:\s*contact@ldmgroupe\.com",
    r"CONSTANTINE\s*:.*?(?:Khroub|Tél|Tel).*",
    r"Z\.I\s+Oued\s+Hamimime.*",
    r"Oued\s+Hamimime.*",
    r"ldmgroupe\.com",
]

# ── Console helpers ───────────────────────────────────────────────────────────
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
    pct = int(current / total * 40)
    bar = "#" * pct + "-" * (40 - pct)
    print(f"\r  [{bar}] {current}/{total}  {label[:45]:<45}", end="", flush=True)


# =============================================================================
# OCR helpers
# =============================================================================

def ocr_pdf_to_markdown(pdf_path: Path) -> str:
    """
    Use pymupdf4llm to extract/OCR a PDF to clean Markdown.
    With rapidocr_onnxruntime installed, it automatically uses
    RapidOCR for image-only pages (no Tesseract needed).
    """
    doc = fitz.open(str(pdf_path))
    md  = pymupdf4llm.to_markdown(doc, show_progress=False)
    doc.close()
    return md


def ocr_image_to_text(img_path: Path) -> str:
    """
    Run RapidOCR directly on a PNG/image file.
    Returns joined text lines.
    """
    if not HAS_RAPID:
        return f"[RapidOCR not available — could not process {img_path.name}]"

    img = np.array(Image.open(img_path).convert("RGB"))
    result, _ = _rapid_engine(img)
    if not result:
        return ""
    # result is list of [box, text, confidence]
    return "\n".join(item[1] for item in result if item[1].strip())


def extract_pdf_text_clean(pdf_path: Path, noise_patterns: list) -> str:
    """
    For the 2 text-based PDFs: extract via pymupdf4llm then strip noise.
    """
    md    = ocr_pdf_to_markdown(pdf_path)
    clean = md
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
        "source":    str(src_path),
        "dci":       parts[0] if len(parts) > 0 else "unknown",
        "brand":     parts[1] if len(parts) > 1 else "root",
        "method":    method,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# Pipeline stages
# =============================================================================

def stage_ocr_pdfs(needs_ocr: list, log: dict) -> dict:
    step(f"Stage 1/3 — OCR {len(needs_ocr)} image-only PDFs via pymupdf4llm + RapidOCR")
    processed = skipped = errors = 0

    for idx, rel in enumerate(needs_ocr, 1):
        src_path = CORPUS_ROOT / rel
        out_path = PROCESSED_ROOT / (rel.rsplit(".", 1)[0] + ".md")
        progress(idx, len(needs_ocr), Path(rel).name)

        # Resume: skip if already processed successfully
        if out_path.exists() and out_path.stat().st_size > 100:
            skipped += 1
            log["files"][rel] = {"status": "skipped_existing", "output": str(out_path)}
            continue

        t0 = time.time()
        try:
            md   = ocr_pdf_to_markdown(src_path)
            meta = make_meta(src_path, rel,
                             "pymupdf4llm + RapidOCR (onnxruntime)" if HAS_RAPID
                             else "pymupdf4llm (no OCR engine)")
            write_md(out_path, md, meta)
            elapsed = round(time.time() - t0, 1)
            log["files"][rel] = {
                "status":  "ocr_ok",
                "output":  str(out_path),
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


def stage_ocr_pngs(non_pdf_files: list, log: dict) -> dict:
    png_files = [f for f in non_pdf_files if f.lower().endswith(".png")]
    step(f"Stage 2/3 — OCR {len(png_files)} PNG screenshots via RapidOCR")
    processed = skipped = errors = 0

    for idx, rel in enumerate(png_files, 1):
        src_path = CORPUS_ROOT / rel
        out_path = PROCESSED_ROOT / (rel.rsplit(".", 1)[0] + ".md")
        progress(idx, len(png_files), Path(rel).name)

        if out_path.exists() and out_path.stat().st_size > 50:
            skipped += 1
            log["files"][rel] = {"status": "skipped_existing", "output": str(out_path)}
            continue

        t0 = time.time()
        try:
            text = ocr_image_to_text(src_path)
            meta = make_meta(src_path, rel, "RapidOCR (onnxruntime) direct image")
            write_md(out_path, text, meta)
            elapsed = round(time.time() - t0, 1)
            log["files"][rel] = {
                "status":  "ocr_ok",
                "output":  str(out_path),
                "chars":   len(text),
                "seconds": elapsed,
            }
            processed += 1
        except Exception as e:
            warn(f"\n  ERROR on {rel}: {e}")
            log["files"][rel] = {"status": "error", "error": str(e)}
            errors += 1

    print()
    ok(f"PNGs — processed: {processed}  skipped: {skipped}  errors: {errors}")
    return log


def stage_clean_valid_pdfs(valid_for_rag: list, audit: dict, log: dict) -> dict:
    step(f"Stage 3/3 — Extract + denoise {len(valid_for_rag)} text-based PDFs")
    for rel in valid_for_rag:
        src_path = CORPUS_ROOT / rel
        out_path = PROCESSED_ROOT / (rel.rsplit(".", 1)[0] + ".md")
        print(f"  Processing: {rel}")

        noise = build_noise_patterns_from_audit(audit, rel)
        try:
            clean = extract_pdf_text_clean(src_path, noise)
            meta  = make_meta(src_path, rel,
                              f"pymupdf4llm Markdown + noise strip ({len(noise)} patterns)")
            write_md(out_path, clean, meta)
            ok(f"{Path(rel).name}  ->  {len(clean):,} clean chars")
            log["files"][rel] = {
                "status":                 "cleaned_ok",
                "output":                 str(out_path),
                "clean_chars":            len(clean),
                "noise_patterns_applied": len(noise),
            }
        except Exception as e:
            warn(f"ERROR on {rel}: {e}")
            log["files"][rel] = {"status": "error", "error": str(e)}
    return log


def stage_copy_csvs(non_pdf_files: list, log: dict) -> dict:
    csv_files = [f for f in non_pdf_files if f.lower().endswith(".csv")]
    step(f"Bonus — Copying {len(csv_files)} CSV files as structured data")
    for rel in csv_files:
        src = CORPUS_ROOT / rel
        dst = PROCESSED_ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        ok(f"Copied: {rel}")
        log["files"][rel] = {"status": "copied", "output": str(dst)}
    return log


# =============================================================================
# corpus_metadata.json update
# =============================================================================

def update_metadata(log: dict):
    step("Updating corpus_metadata.json with processed text paths...")
    meta    = json.loads(META_JSON.read_text(encoding="utf-8"))
    updated = 0

    for dci_entry in meta.get("corpus", []):
        for f in dci_entry.get("source_files", []):
            rel = f["relative_path"]
            if rel in log["files"] and "output" in log["files"][rel]:
                f["processed_text_path"] = log["files"][rel]["output"]
                f["ocr_status"]          = log["files"][rel]["status"]
                updated += 1
        for brand in dci_entry.get("brands", []):
            for f in brand.get("files", []):
                rel = f["relative_path"]
                if rel in log["files"] and "output" in log["files"][rel]:
                    f["processed_text_path"] = log["files"][rel]["output"]
                    f["ocr_status"]          = log["files"][rel]["status"]
                    updated += 1

    meta["_meta"]["ocr_pipeline_run"]      = datetime.now(timezone.utc).isoformat()
    meta["_meta"]["processed_files"]       = updated
    meta["_meta"]["processed_corpus_root"] = str(PROCESSED_ROOT.resolve())
    meta["_meta"]["ocr_engine"]            = "pymupdf4llm + RapidOCR (onnxruntime)"

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
    ok(f"Markdown files produced : {len(md_files)}")
    ok(f"CSV files copied        : {len(csv_files)}")
    ok(f"Total characters extracted : {total_chars:,}")

    # Spot-check 3 files
    samples = [p for p in md_files if p.stat().st_size > 200][:3]
    if samples:
        print("\n  --- Spot-check (first 150 chars of 3 files) ---")
        for p in samples:
            snippet = p.read_text(encoding="utf-8")[200:350].replace("\n", " ").strip()
            print(f"  {p.name}: {repr(snippet[:120])}")


# =============================================================================
# Main
# =============================================================================

def main():
    banner("COGNIVEX OCR + Cleaning Pipeline  (pymupdf4llm + RapidOCR)")
    print(f"  Corpus root   : {CORPUS_ROOT}")
    print(f"  Output root   : {PROCESSED_ROOT}")
    print(f"  OCR engine    : {'RapidOCR (onnxruntime)' if HAS_RAPID else 'NOT AVAILABLE'}")
    print(f"  Output format : Markdown (.md)")
    print(f"  Resume mode   : ON")

    if not AUDIT_JSON.exists():
        sys.exit(f"[ERROR] Run audit_corpus.py first — {AUDIT_JSON} not found.")

    audit      = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    needs_ocr  = audit.get("needs_ocr", [])
    valid_pdfs = audit.get("valid_for_rag", [])
    non_pdf    = audit.get("non_pdf_files", [])

    # Load or create pipeline log (supports resume)
    if LOG_JSON.exists():
        log     = json.loads(LOG_JSON.read_text(encoding="utf-8"))
        already = sum(1 for v in log["files"].values()
                      if v.get("status") not in ("error",))
        print(f"\n  Resuming — {already} files already done, skipping them.")
    else:
        log = {"started_at": datetime.now(timezone.utc).isoformat(), "files": {}}

    PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)
    t_total = time.time()

    # Run all stages, saving log after each
    log = stage_ocr_pdfs(needs_ocr, log)
    LOG_JSON.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

    log = stage_ocr_pngs(non_pdf, log)
    LOG_JSON.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

    log = stage_clean_valid_pdfs(valid_pdfs, audit, log)
    LOG_JSON.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

    log = stage_copy_csvs(non_pdf, log)
    LOG_JSON.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

    update_metadata(log)
    verify_outputs(log)

    # Final summary
    elapsed = round(time.time() - t_total, 1)
    statuses = defaultdict(int)
    for v in log["files"].values():
        statuses[v.get("status", "unknown")] += 1

    total_chars = sum(
        v.get("chars", v.get("clean_chars", 0))
        for v in log["files"].values() if isinstance(v, dict)
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
