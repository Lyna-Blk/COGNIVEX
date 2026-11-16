"""
audit_corpus.py
---------------
Audits every file inside data/corpus/ for RAG-ingestion quality:

  1. PDF extractability  - real text vs. scanned image-only PDF
  2. Character count     - flags empty / near-empty documents
  3. Corruption check    - catches unreadable / malformed PDFs
  4. Duplicate detection - SHA-256 hash + size across all folders
  5. Noise artifacts     - detects repeated headers/footers, very short pages

Outputs
  - Live progress to stdout
  - data/corpus_audit_report.json   (machine-readable)
  - data/corpus_audit_report.txt    (human-readable summary)
"""

import os
import sys
import json
import hashlib
import re
import textwrap
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

# -- Dependency guard ----------------------------------------------------------
try:
    import pymupdf as fitz          # PyMuPDF >= 1.24  (import name changed)
except ImportError:
    try:
        import fitz                 # older PyMuPDF
    except ImportError:
        sys.exit("[ERROR] PyMuPDF is not installed. Run: python -m pip install pymupdf")

# -- Configuration -------------------------------------------------------------
CORPUS_ROOT   = Path(__file__).parent / "data" / "corpus"
REPORT_JSON   = Path(__file__).parent / "data" / "corpus_audit_report.json"
REPORT_TXT    = Path(__file__).parent / "data" / "corpus_audit_report.txt"

MIN_CHARS_PER_PAGE    = 200    # pages below this are "noise/near-empty"
MIN_CHARS_TOTAL       = 100    # whole document below this -> flag for OCR
NOISE_REPEAT_THRESH   = 5      # a text block repeated >= N times = header/footer noise
IMAGE_PAGE_RATIO_WARN = 0.5    # >50% image-only pages -> flag for OCR


# =============================================================================
# Helpers
# =============================================================================

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_all_files(root: Path) -> list:
    return sorted(p for p in root.rglob("*") if p.is_file())


# =============================================================================
# PDF Analysis
# =============================================================================

def analyze_pdf(path: Path) -> dict:
    """
    Returns a rich dict describing a PDF's RAG-readiness.
    """
    result = {
        "status": "ok",
        "page_count": 0,
        "total_chars": 0,
        "image_only_pages": 0,
        "short_pages": 0,
        "has_noise": False,
        "noise_samples": [],
        "issues": [],
    }

    try:
        doc = fitz.open(str(path))
    except Exception as e:
        result["status"] = "corrupt"
        result["issues"].append(f"Cannot open PDF: {e}")
        return result

    result["page_count"] = len(doc)
    if len(doc) == 0:
        result["status"] = "empty"
        result["issues"].append("PDF has 0 pages")
        doc.close()
        return result

    block_counter = defaultdict(int)

    for page in doc:
        text = page.get_text("text").strip()
        chars = len(text)
        result["total_chars"] += chars

        if chars == 0:
            result["image_only_pages"] += 1
        elif chars < MIN_CHARS_PER_PAGE:
            result["short_pages"] += 1

        # Collect small text blocks for noise detection
        for block in page.get_text("blocks"):
            block_text = block[4].strip() if len(block) > 4 else ""
            if 5 < len(block_text) < 120:
                block_counter[block_text] += 1

    doc.close()

    # -- Noise detection -------------------------------------------------------
    noisy_blocks = {t: n for t, n in block_counter.items() if n >= NOISE_REPEAT_THRESH}
    if noisy_blocks:
        result["has_noise"] = True
        result["noise_samples"] = [
            '"{}" (x{})'.format(t[:80], n) for t, n in
            sorted(noisy_blocks.items(), key=lambda x: -x[1])[:5]
        ]

    # -- Status assignment -----------------------------------------------------
    total      = result["total_chars"]
    img_pages  = result["image_only_pages"]
    n_pages    = result["page_count"]
    img_ratio  = img_pages / n_pages if n_pages else 0

    if total < MIN_CHARS_TOTAL:
        result["status"] = "needs_ocr" if img_pages > 0 else "empty"
        result["issues"].append(
            "Only {} chars extracted - likely scanned image PDF".format(total) if img_pages
            else "Only {} chars - document appears empty".format(total)
        )
    elif img_ratio >= IMAGE_PAGE_RATIO_WARN:
        result["status"] = "needs_ocr"
        result["issues"].append(
            "{}/{} pages ({:.0%}) have no extractable text - partial scan".format(
                img_pages, n_pages, img_ratio)
        )

    if result["has_noise"]:
        result["issues"].append(
            "Repeated header/footer noise detected ({} unique blocks)".format(len(noisy_blocks))
        )

    if result["short_pages"] > 0 and result["status"] == "ok":
        result["issues"].append(
            "{} page(s) have fewer than {} chars".format(result["short_pages"], MIN_CHARS_PER_PAGE)
        )

    return result


# =============================================================================
# Main Audit
# =============================================================================

def run_audit():
    print("\n" + "=" * 56)
    print("   COGNIVEX Corpus RAG Audit Tool")
    print("=" * 56 + "\n")

    all_files   = collect_all_files(CORPUS_ROOT)
    total_files = len(all_files)
    print("Found {} files in {}\n".format(total_files, CORPUS_ROOT))

    # -- Pass 1: Hash map for duplicate detection ------------------------------
    print("[1/3] Computing file hashes for duplicate detection...")
    hash_map = defaultdict(list)
    size_map = defaultdict(list)

    for path in all_files:
        size = path.stat().st_size
        size_map[size].append(path)

    candidate_dupes = {p for paths in size_map.values() if len(paths) > 1 for p in paths}
    file_hashes = {}

    for path in all_files:
        if path in candidate_dupes:
            h = sha256(path)
            file_hashes[path] = h
            hash_map[h].append(path)
        else:
            file_hashes[path] = None

    duplicate_groups = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    dupe_files       = {p for paths in duplicate_groups.values() for p in paths[1:]}
    print("   Duplicate groups found: {}\n".format(len(duplicate_groups)))

    # -- Pass 2: Per-file analysis ---------------------------------------------
    print("[2/3] Analysing PDF content quality...")

    file_results    = []
    valid_for_rag   = []
    needs_ocr       = []
    empty_or_corrupt= []
    noisy_files     = []
    non_pdf_files   = []

    for i, path in enumerate(all_files, 1):
        rel = path.relative_to(CORPUS_ROOT).as_posix()
        ext = path.suffix.lower()

        entry = {
            "path":         rel,
            "absolute":     path.resolve().as_posix(),
            "extension":    ext.lstrip("."),
            "size_bytes":   path.stat().st_size,
            "hash_sha256":  file_hashes.get(path),
            "is_duplicate": path in dupe_files,
        }

        if ext == ".pdf":
            print("   [{:>3}/{}] {}".format(i, total_files, rel[:65]), end="\r")
            pdf_info = analyze_pdf(path)
            entry.update(pdf_info)

            if pdf_info["status"] == "ok" and not (path in dupe_files):
                valid_for_rag.append(rel)
            elif pdf_info["status"] == "needs_ocr":
                needs_ocr.append(rel)
            elif pdf_info["status"] in ("empty", "corrupt"):
                empty_or_corrupt.append(rel)

            if pdf_info.get("has_noise"):
                noisy_files.append(rel)
        else:
            entry["status"] = "non_pdf"
            non_pdf_files.append(rel)

        file_results.append(entry)

    print(" " * 80, end="\r")
    print("   Done analysing {} files.\n".format(total_files))

    # -- Pass 3: Duplicate report ----------------------------------------------
    print("[3/3] Building duplicate report...")
    dup_report = []
    for h, paths in duplicate_groups.items():
        dup_report.append({
            "hash":       h,
            "files":      [p.relative_to(CORPUS_ROOT).as_posix() for p in paths],
            "size_bytes": paths[0].stat().st_size,
        })
    print("   Done.\n")

    # -- Assemble final report -------------------------------------------------
    report = {
        "_meta": {
            "generated_at":     datetime.now(timezone.utc).isoformat(),
            "corpus_root":      CORPUS_ROOT.resolve().as_posix(),
            "total_files":      total_files,
            "total_pdf":        sum(1 for f in file_results if f["extension"] == "pdf"),
            "valid_for_rag":    len(valid_for_rag),
            "needs_ocr":        len(needs_ocr),
            "empty_or_corrupt": len(empty_or_corrupt),
            "noisy":            len(noisy_files),
            "non_pdf":          len(non_pdf_files),
            "duplicate_groups": len(duplicate_groups),
        },
        "valid_for_rag":    valid_for_rag,
        "needs_ocr":        needs_ocr,
        "empty_or_corrupt": empty_or_corrupt,
        "noisy_files":      noisy_files,
        "non_pdf_files":    non_pdf_files,
        "duplicate_groups": dup_report,
        "files":            file_results,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # -- Human-readable TXT report ---------------------------------------------
    lines = []
    sep   = "=" * 72
    thin  = "-" * 72

    def h1(t):   lines.append("\n{}\n  {}\n{}".format(sep, t, sep))
    def h2(t):   lines.append("\n{}\n  {}\n{}".format(thin, t, thin))
    def li(t):   lines.append("    {}".format(t))
    def blank():  lines.append("")

    h1("COGNIVEX CORPUS RAG AUDIT REPORT")
    li("Generated : {}".format(report["_meta"]["generated_at"]))
    li("Corpus    : {}".format(report["_meta"]["corpus_root"]))
    blank()

    h2("SUMMARY")
    m = report["_meta"]
    li("Total files scanned       : {}".format(m["total_files"]))
    li("Total PDFs analysed       : {}".format(m["total_pdf"]))
    blank()
    li("[READY]  Valid for RAG ingestion  : {}".format(m["valid_for_rag"]))
    li("[OCR]    Need OCR processing      : {}".format(m["needs_ocr"]))
    li("[ERROR]  Empty / Corrupt PDFs     : {}".format(m["empty_or_corrupt"]))
    li("[NOISE]  Have header/footer noise : {}".format(m["noisy"]))
    li("[IMAGE]  Non-PDF files (PNG/CSV)  : {}".format(m["non_pdf"]))
    li("[DUPE]   Duplicate file groups    : {}".format(m["duplicate_groups"]))

    h2("VALID FILES READY FOR RAG INGESTION")
    if valid_for_rag:
        for f in valid_for_rag:
            li("[OK]  {}".format(f))
    else:
        li("(none)")

    h2("FILES NEEDING OCR (image-only or partial scans)")
    if needs_ocr:
        for f in needs_ocr:
            entry  = next(e for e in file_results if e["path"] == f)
            issues = "; ".join(entry.get("issues", []))
            li("[OCR]  {}".format(f))
            li("       => {}".format(issues))
    else:
        li("(none)")

    h2("EMPTY OR CORRUPTED PDFs")
    if empty_or_corrupt:
        for f in empty_or_corrupt:
            entry  = next(e for e in file_results if e["path"] == f)
            issues = "; ".join(entry.get("issues", []))
            li("[ERR]  {}".format(f))
            li("       => {}".format(issues))
    else:
        li("(none)")

    h2("FILES WITH HEADER/FOOTER NOISE ARTIFACTS")
    if noisy_files:
        for f in noisy_files:
            entry   = next(e for e in file_results if e["path"] == f)
            samples = entry.get("noise_samples", [])
            li("[NOISE]  {}".format(f))
            for s in samples[:3]:
                li("         Repeated block: {}".format(s))
    else:
        li("(none)")

    h2("DUPLICATE FILE GROUPS")
    if dup_report:
        for grp in dup_report:
            li("Hash: {}...  Size: {:,} bytes".format(grp["hash"][:16], grp["size_bytes"]))
            for fp in grp["files"]:
                li("  - {}".format(fp))
            blank()
    else:
        li("(none)")

    h2("NON-PDF FILES (may need separate ingestion pipeline)")
    for f in non_pdf_files:
        entry = next(e for e in file_results if e["path"] == f)
        li("[{:>4}]  {}  ({:,} bytes)".format(
            entry["extension"].upper(), f, entry["size_bytes"]))

    h1("END OF REPORT")

    REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")

    # -- Console final summary -------------------------------------------------
    print("=" * 56)
    print("  AUDIT COMPLETE")
    print("=" * 56)
    print("  Total files scanned       : {}".format(m["total_files"]))
    print("  Total PDFs analysed       : {}".format(m["total_pdf"]))
    print()
    print("  [READY]  Valid for RAG ingestion  : {}".format(m["valid_for_rag"]))
    print("  [OCR]    Need OCR processing      : {}".format(m["needs_ocr"]))
    print("  [ERROR]  Empty / Corrupt PDFs     : {}".format(m["empty_or_corrupt"]))
    print("  [NOISE]  Have header/footer noise : {}".format(m["noisy"]))
    print("  [IMAGE]  Non-PDF files            : {}".format(m["non_pdf"]))
    print("  [DUPE]   Duplicate file groups    : {}".format(m["duplicate_groups"]))
    print()
    print("  Reports saved:")
    print("    JSON : {}".format(REPORT_JSON))
    print("    TXT  : {}".format(REPORT_TXT))
    print("=" * 56)


if __name__ == "__main__":
    run_audit()
