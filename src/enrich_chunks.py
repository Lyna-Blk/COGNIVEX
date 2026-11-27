"""
enrich_chunks.py
----------------
Step 1 of Week 3: Enrich chunk metadata with normalization data.

Reads  : data/processed/chunks_exp3.jsonl  (existing chunks)
         data/knowledge_graph/dci_dict.json (normalization dict)
Writes : data/processed/chunks_enriched.jsonl  (enriched chunks)
         data/processed/vectordb_enriched/      (new ChromaDB)

New metadata fields added to every chunk:
  - dci_normalized  : lowercase/accent-free DCI (for exact filtering)
  - atc             : ATC code (e.g. N02BE01)
  - classe          : therapeutic class
  - noms_commerciaux: comma-separated list of known brand names
"""

import json
import sys
import unicodedata
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

CHUNKS_IN  = ROOT / "data" / "processed" / "chunks_exp3.jsonl"
CHUNKS_OUT = ROOT / "data" / "processed" / "chunks_enriched.jsonl"
DICT_PATH  = ROOT / "data" / "knowledge_graph" / "dci_dict.json"
VECTOR_DB_DIR = ROOT / "data" / "processed" / "vectordb_enriched"
EMBEDDINGS_IN = ROOT / "data" / "processed" / "embeddings" / "embeddings_exp3.npy"

# ── Helpers ───────────────────────────────────────────────────────────────────
def norm(s: str) -> str:
    """Lowercase, strip accents, strip punctuation."""
    nfkd = unicodedata.normalize("NFKD", str(s))
    ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9\s\+]", " ", ascii_.lower()).strip()


def _build_lookup(dci_dict: dict) -> dict:
    """
    Returns {normalized_key: dci_entry} for all DCI names and
    all brand names (normalized) → their DCI entry.
    """
    lookup = {}
    for dci_key, entry in dci_dict.items():
        # DCI itself
        lookup[norm(dci_key)] = entry
        lookup[norm(entry["dci"])] = entry
        lookup[entry["dci_normalized"]] = entry
        # Brand names
        for gen in entry["generiques"]:
            nc_norm = gen["nom_normalized"]
            if nc_norm:
                lookup[nc_norm] = entry
    # Also add short aliases used as folder names in corpus
    _CORPUS_ALIASES = {
        "cotrimoxazole": "cotrimoxazole (sulfaméthoxazole + triméthoprime)",
    }
    for alias_norm, full_dci in _CORPUS_ALIASES.items():
        if full_dci in dci_dict:
            lookup[alias_norm] = dci_dict[full_dci]

    return lookup


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Load dci dict
    if not DICT_PATH.exists():
        raise FileNotFoundError("Run src/build_dci_dict.py first!")
    with open(DICT_PATH, encoding="utf-8") as f:
        dci_dict = json.load(f)
    lookup = _build_lookup(dci_dict)

    # Load existing chunks
    if not CHUNKS_IN.exists():
        raise FileNotFoundError(f"{CHUNKS_IN} not found!")
    chunks = []
    with open(CHUNKS_IN, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    print(f"[enrich_chunks] Loaded {len(chunks)} chunks from {CHUNKS_IN.name}")

    matched = 0
    unmatched_dcis = set()
    enriched = []

    for chunk in chunks:
        raw_dci = chunk.get("dci", "")
        raw_brand = chunk.get("brand", chunk.get("produit", ""))

        # Try to find entry: first by DCI, then by brand
        entry = lookup.get(norm(raw_dci)) or lookup.get(norm(raw_brand))

        if entry:
            matched += 1
            atc = entry.get("atc", "")
            classe = entry.get("classe", "")
            dci_norm = entry.get("dci_normalized", norm(entry["dci"]))
            brands = ", ".join(entry.get("tous_noms_commerciaux", [])[:10])  # cap at 10
        else:
            unmatched_dcis.add(raw_dci)
            atc = ""
            classe = ""
            dci_norm = norm(raw_dci)
            brands = ""

        enriched_chunk = {
            **chunk,
            "dci_normalized": dci_norm,
            "atc": atc,
            "classe": classe,
            "noms_commerciaux": brands,
        }
        enriched.append(enriched_chunk)

    # Write enriched chunks
    CHUNKS_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_OUT, "w", encoding="utf-8") as f:
        for c in enriched:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"[enrich_chunks] ✓ {len(enriched)} chunks written → {CHUNKS_OUT.name}")
    print(f"  Matched to dci_dict : {matched} / {len(chunks)}")
    if unmatched_dcis:
        print(f"  Unmatched DCI names : {sorted(unmatched_dcis)}")

    # ── Rebuild ChromaDB with enriched metadata ──────────────────────────────
    try:
        import chromadb
        import numpy as np
    except ImportError:
        print("[enrich_chunks] chromadb or numpy not available — skipping ChromaDB rebuild.")
        print("  Run: pip install chromadb numpy")
        return

    if not EMBEDDINGS_IN.exists():
        print(f"[enrich_chunks] Embeddings not found at {EMBEDDINGS_IN} — skipping ChromaDB.")
        return

    embeddings = np.load(EMBEDDINGS_IN)
    if len(embeddings) != len(enriched):
        print(f"[enrich_chunks] ⚠ Embeddings count ({len(embeddings)}) ≠ chunks count ({len(enriched)})")
        print("  → ChromaDB rebuild skipped. Re-run build_chunks.py + embedding notebook first.")
        return

    print(f"\n[enrich_chunks] Rebuilding ChromaDB at {VECTOR_DB_DIR} ...")
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))

    try:
        client.delete_collection("cognivex_enriched")
    except Exception:
        pass

    collection = client.create_collection(
        name="cognivex_enriched",
        metadata={"hnsw:space": "cosine", "description": "Week3 enriched with normalization"},
    )

    batch_size = 50
    for start in range(0, len(enriched), batch_size):
        batch_chunks = enriched[start:start + batch_size]
        batch_emb = embeddings[start:start + batch_size]

        collection.add(
            ids=[c["chunk_id"] for c in batch_chunks],
            embeddings=batch_emb.tolist(),
            documents=[c["text"] for c in batch_chunks],
            metadatas=[
                {
                    "dci":             str(c.get("dci", "")),
                    "dci_normalized":  str(c.get("dci_normalized", "")),
                    "atc":             str(c.get("atc", "")),
                    "classe":          str(c.get("classe", "")),
                    "produit":         str(c.get("brand", c.get("produit", ""))),
                    "doc_type":        str(c.get("document_type", c.get("doc_type", ""))),
                    "fichier":         str(c.get("file_path", c.get("fichier", ""))),
                    "page":            str(c.get("page", "")),
                    "noms_commerciaux": str(c.get("noms_commerciaux", "")),
                }
                for c in batch_chunks
            ],
        )
        if start % 500 == 0:
            print(f"  Added {start + len(batch_chunks)} / {len(enriched)} chunks...")

    print(f"[enrich_chunks] ✓ ChromaDB ready: {collection.count()} vectors in 'cognivex_enriched'")
    print(f"  Stored at: {VECTOR_DB_DIR}")


if __name__ == "__main__":
    main()
