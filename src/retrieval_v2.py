"""
retrieval_v2.py
---------------
Step 3 of Week 3: Updated search that uses normalization before retrieval.

Changes vs retrieval.py:
  1. normalize_query() called on user query → resolves DCI before search
  2. BM25 search expanded with DCI name when brand name typed
  3. ChromaDB uses enriched collection + optional DCI filter
  4. Results tagged with match_type (exact/fuzzy/alias)

Usage:
    from src.retrieval_v2 import search
    results = search("DOLIPRANE interaction aspirine", top_k=5)
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from normalize_names import normalize_query, _load_dict

# ── Config ────────────────────────────────────────────────────────────────────
CHUNKS_ENRICHED = ROOT / "data" / "processed" / "chunks_enriched.jsonl"
CHUNKS_ORIG     = ROOT / "data" / "processed" / "chunks_exp3.jsonl"
VECTOR_DB_ENRICHED = ROOT / "data" / "processed" / "vectordb_enriched"
VECTOR_DB_ORIG     = ROOT / "data" / "processed" / "vectordb_exp3"
EMBEDDINGS_FILE    = ROOT / "data" / "processed" / "embeddings" / "embeddings_exp3.npy"

COLLECTION_ENRICHED = "cognivex_enriched"
COLLECTION_ORIG     = "cognivex_chunks"
EMBEDDING_MODEL     = "intfloat/multilingual-e5-small"

_dci_dict  = None
_chunks    = None
_bm25      = None
_chroma    = None
_model     = None


# ── Lazy loaders ─────────────────────────────────────────────────────────────
def _get_dict():
    global _dci_dict
    if _dci_dict is None:
        _dci_dict = _load_dict()
    return _dci_dict


def _get_chunks():
    global _chunks
    if _chunks is not None:
        return _chunks
    # Prefer enriched, fall back to original
    path = CHUNKS_ENRICHED if CHUNKS_ENRICHED.exists() else CHUNKS_ORIG
    _chunks = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                _chunks.append(json.loads(line))
    print(f"[retrieval_v2] Loaded {len(_chunks)} chunks from {path.name}")
    return _chunks


def _get_bm25():
    global _bm25
    if _bm25 is not None:
        return _bm25
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        raise SystemExit("rank_bm25 not installed. Run: pip install rank-bm25")

    import unicodedata, re
    def tokenize(text):
        nfkd = unicodedata.normalize("NFKD", str(text))
        ascii_ = nfkd.encode("ascii", "ignore").decode("ascii").lower()
        return re.findall(r"[a-z0-9]+", ascii_)

    chunks = _get_chunks()
    corpus = [tokenize(c["text"] + " " + c.get("dci", "") + " " + c.get("dci_normalized", ""))
              for c in chunks]
    _bm25 = BM25Okapi(corpus)
    return _bm25


def _get_chroma():
    global _chroma
    if _chroma is not None:
        return _chroma
    try:
        import chromadb
    except ImportError:
        return None

    # Prefer enriched collection
    db_path = VECTOR_DB_ENRICHED if VECTOR_DB_ENRICHED.exists() else VECTOR_DB_ORIG
    coll_name = COLLECTION_ENRICHED if VECTOR_DB_ENRICHED.exists() else COLLECTION_ORIG

    client = chromadb.PersistentClient(path=str(db_path))
    try:
        _chroma = client.get_collection(coll_name)
        print(f"[retrieval_v2] ChromaDB: '{coll_name}' ({_chroma.count()} vectors)")
    except Exception as e:
        print(f"[retrieval_v2] ChromaDB not available: {e}")
        _chroma = None
    return _chroma


def _get_model():
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
    except Exception:
        _model = None
    return _model


# ── Core search ───────────────────────────────────────────────────────────────
def _expand_query(query: str, norm_result: dict) -> str:
    """
    If query is a brand name, expand it with the DCI name so BM25
    can find chunks tagged with the DCI folder name.
    """
    if not norm_result["found"]:
        return query
    dci = norm_result["dci"] or ""
    # If the original query doesn't already contain the DCI words, append them
    import unicodedata, re
    def simple_norm(s):
        n = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode("ascii").lower()
        return set(re.findall(r"[a-z]+", n))
    q_words = simple_norm(query)
    dci_words = simple_norm(dci)
    if not dci_words.issubset(q_words):
        return f"{query} {dci}"
    return query


def search_bm25(query: str, top_k: int = 5, dci_filter: str = None) -> list[dict]:
    """BM25 keyword search, optionally filtered to one DCI."""
    import unicodedata, re
    def tokenize(text):
        nfkd = unicodedata.normalize("NFKD", str(text))
        ascii_ = nfkd.encode("ascii", "ignore").decode("ascii").lower()
        return re.findall(r"[a-z0-9]+", ascii_)

    bm25  = _get_bm25()
    chunks = _get_chunks()

    tokens = tokenize(query)
    scores = bm25.get_scores(tokens)

    # Build (score, chunk) pairs, applying DCI filter if needed
    scored = []
    for i, (score, chunk) in enumerate(zip(scores, chunks)):
        if dci_filter:
            chunk_dci = (chunk.get("dci_normalized") or chunk.get("dci", "")).lower()
            if dci_filter.lower() not in chunk_dci:
                continue
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: -x[0])
    return [
        {**c, "score_bm25": round(s, 4), "method": "BM25"}
        for s, c in scored[:top_k]
    ]


def search_semantic(query: str, top_k: int = 5, dci_filter: str = None) -> list[dict]:
    """Semantic search via ChromaDB."""
    chroma = _get_chroma()
    model  = _get_model()
    if chroma is None or model is None:
        return []

    prefix = "query: " if "e5" in EMBEDDING_MODEL.lower() else ""
    q_emb = model.encode(prefix + query, normalize_embeddings=True).tolist()

    where = None
    if dci_filter:
        where = {"dci_normalized": {"$eq": dci_filter}}

    try:
        results = chroma.query(
            query_embeddings=[q_emb],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        # Fall back without filter if filter fails
        results = chroma.query(
            query_embeddings=[q_emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            **meta,
            "text": doc,
            "score_semantic": round(1 - dist, 4),
            "method": "SEMANTIC",
        })
    return hits


def search(query: str, top_k: int = 5, method: str = "hybrid") -> dict:
    """
    Main search function with normalization.

    Parameters
    ----------
    query  : user query (can be brand name, DCI, with typos, etc.)
    top_k  : number of results to return per method
    method : 'bm25' | 'semantic' | 'hybrid'

    Returns
    -------
    {
        "query_original"    : str,
        "query_expanded"    : str,          # after normalization
        "normalization"     : dict,         # full normalize_query result
        "results_bm25"      : [...],        # if method in bm25/hybrid
        "results_semantic"  : [...],        # if method in semantic/hybrid
    }
    """
    dci_dict = _get_dict()

    # ── 1. Normalize query ───────────────────────────────────────────────────
    norm_result = normalize_query(query, dci_dict)
    dci_norm    = norm_result.get("dci_normalized") if norm_result["found"] else None

    # Expand query with DCI name if brand was typed
    expanded = _expand_query(query, norm_result)

    # ── 2. BM25 ──────────────────────────────────────────────────────────────
    bm25_results = []
    if method in ("bm25", "hybrid"):
        bm25_results = search_bm25(expanded, top_k=top_k, dci_filter=dci_norm)

    # ── 3. Semantic ───────────────────────────────────────────────────────────
    sem_results = []
    if method in ("semantic", "hybrid"):
        sem_results = search_semantic(expanded, top_k=top_k, dci_filter=dci_norm)

    return {
        "query_original":   query,
        "query_expanded":   expanded,
        "normalization":    norm_result,
        "results_bm25":     bm25_results,
        "results_semantic": sem_results,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Search with normalization")
    parser.add_argument("query", nargs="+", help="Query text")
    parser.add_argument("--top_k", type=int, default=5)
    parser.add_argument("--method", choices=["bm25", "semantic", "hybrid"], default="hybrid")
    args = parser.parse_args()

    q = " ".join(args.query)
    print(f"\n🔍 Query: '{q}'")
    result = search(q, top_k=args.top_k, method=args.method)

    norm = result["normalization"]
    print(f"📌 Normalized → DCI: '{norm.get('dci')}' | ATC: {norm.get('atc')} | "
          f"Match: {norm.get('match_type')} | Score: {norm.get('score')}")
    if norm.get("ambigu"):
        print(f"⚠  Ambiguous! Candidates: {[c['dci'] for c in norm.get('candidats', [])]}")
    if result["query_expanded"] != q:
        print(f"🔄 Expanded query: '{result['query_expanded']}'")

    if result["results_bm25"]:
        print(f"\n── BM25 Top {args.top_k} ──")
        for i, r in enumerate(result["results_bm25"], 1):
            print(f"  [{i}] score={r['score_bm25']:.3f} | dci={r.get('dci','')} | "
                  f"type={r.get('doc_type', r.get('document_type',''))} | "
                  f"page={r.get('page','')}")
            print(f"       {r['text'][:120]}...")

    if result["results_semantic"]:
        print(f"\n── SEMANTIC Top {args.top_k} ──")
        for i, r in enumerate(result["results_semantic"], 1):
            print(f"  [{i}] score={r['score_semantic']:.3f} | dci={r.get('dci','')} | "
                  f"type={r.get('doc_type', r.get('document_type',''))} | "
                  f"page={r.get('page','')}")
            print(f"       {r['text'][:120]}...")
