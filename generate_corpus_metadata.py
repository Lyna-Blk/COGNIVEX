"""
generate_corpus_metadata.py
----------------------------
Scans data/corpus/ and all its subfolders, then generates a clean
corpus_metadata.json file with:
  - Every active substance (DCI) found as a top-level folder
  - Its commercial brand subfolders
  - The exact paths and MIME-inferred types of all files inside each
  
Run:
    python generate_corpus_metadata.py

Output:
    data/corpus_metadata.json
"""

import os
import json
import mimetypes
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CORPUS_ROOT = Path(__file__).parent / "data" / "corpus"
OUTPUT_FILE = Path(__file__).parent / "data" / "corpus_metadata.json"

# Extend mimetypes with common pharma-document extensions just in case
mimetypes.add_type("application/pdf", ".pdf")
mimetypes.add_type("text/csv", ".csv")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("image/jpeg", ".jpg")
mimetypes.add_type("image/jpeg", ".jpeg")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def infer_file_type(path: Path) -> str:
    """Return a human-readable type category for a file."""
    mime, _ = mimetypes.guess_type(str(path))
    if mime is None:
        return "unknown"
    if mime == "application/pdf":
        return "pdf"
    if mime.startswith("image/"):
        return mime.split("/")[-1]          # e.g. "png", "jpeg"
    if mime in ("text/csv", "application/csv"):
        return "csv"
    if mime.startswith("text/"):
        return "text"
    return mime                              # fall back to raw MIME


def file_entry(file_path: Path, base: Path) -> dict:
    """Build a metadata dict for a single file."""
    rel = file_path.relative_to(base).as_posix()
    stat = file_path.stat()
    return {
        "filename":   file_path.name,
        "relative_path": rel,
        "absolute_path": file_path.resolve().as_posix(),
        "type":       infer_file_type(file_path),
        "extension":  file_path.suffix.lower().lstrip(".") or "none",
        "size_bytes": stat.st_size,
    }


def scan_brand(brand_dir: Path, corpus_root: Path) -> dict:
    """
    Scan a commercial brand folder (second-level folder).
    Returns a dict with brand name, path, and its file list.
    """
    files = []
    # Walk the brand folder recursively (handles any unexpected deeper nesting)
    for item in sorted(brand_dir.rglob("*")):
        if item.is_file():
            files.append(file_entry(item, corpus_root))

    return {
        "brand_name":    brand_dir.name,
        "relative_path": brand_dir.relative_to(corpus_root).as_posix(),
        "absolute_path": brand_dir.resolve().as_posix(),
        "file_count":    len(files),
        "files":         files,
    }


def scan_dci(dci_dir: Path, corpus_root: Path) -> dict:
    """
    Scan a DCI (active substance) folder (first-level folder).
    - Direct files in this folder are captured as 'source_files'.
    - Immediate subfolders are treated as commercial brand folders.
    """
    brand_entries = []
    source_files  = []

    for item in sorted(dci_dir.iterdir()):
        if item.is_dir():
            brand_entries.append(scan_brand(item, corpus_root))
        elif item.is_file():
            source_files.append(file_entry(item, corpus_root))

    total_files = len(source_files) + sum(b["file_count"] for b in brand_entries)

    return {
        "dci":            dci_dir.name,
        "relative_path":  dci_dir.relative_to(corpus_root).as_posix(),
        "absolute_path":  dci_dir.resolve().as_posix(),
        "brand_count":    len(brand_entries),
        "total_files":    total_files,
        "source_files":   source_files,   # DCI-level files (not inside a brand folder)
        "brands":         brand_entries,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not CORPUS_ROOT.exists():
        raise FileNotFoundError(f"Corpus root not found: {CORPUS_ROOT}")

    print(f"[INFO] Scanning corpus at: {CORPUS_ROOT.resolve()}")

    dci_entries = []
    for item in sorted(CORPUS_ROOT.iterdir()):
        if item.is_dir():
            print(f"  --> DCI found: {item.name}")
            dci_entries.append(scan_dci(item, CORPUS_ROOT))

    metadata = {
        "_meta": {
            "generated_at":     datetime.now(timezone.utc).isoformat(),
            "corpus_root":      CORPUS_ROOT.resolve().as_posix(),
            "total_dci_count":  len(dci_entries),
            "total_brands":     sum(d["brand_count"] for d in dci_entries),
            "total_files":      sum(d["total_files"] for d in dci_entries),
        },
        "corpus": dci_entries,
    }

    # --- Serialize & validate ---
    json_str = json.dumps(metadata, indent=2, ensure_ascii=False)

    # Validate round-trip
    parsed_back = json.loads(json_str)
    assert parsed_back["_meta"]["total_dci_count"] == len(dci_entries), \
        "Validation failed: DCI count mismatch after round-trip."

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json_str, encoding="utf-8")

    print(f"\n[SUCCESS] corpus_metadata.json written to: {OUTPUT_FILE.resolve()}")
    print(f"  DCIs catalogued  : {metadata['_meta']['total_dci_count']}")
    print(f"  Brands catalogued: {metadata['_meta']['total_brands']}")
    print(f"  Total files      : {metadata['_meta']['total_files']}")
    print(f"  JSON size        : {OUTPUT_FILE.stat().st_size:,} bytes")
    print(f"  Validation       : PASSED [OK]")


if __name__ == "__main__":
    main()
