"""
Outils communs de la semaine 2 : découpage, BM25 et embeddings sémantiques.

Les embeddings sont des vecteurs sémantiques latents : TF-IDF du corpus,
puis décomposition en valeurs singulières (SVD). Ils sont calculés localement
avec numpy, sans télécharger de modèle.
"""

import json
import math
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed_corpus"
FICHES_ROOT = PROJECT_ROOT / "data" / "fiches_dci"
STORE_DIR = PROJECT_ROOT / "data" / "processed" / "vector_store"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
MIN_CHARS = 80
EMBED_DIM = 192
MAX_CONTENT_TERMS = 10000
MAX_NAME_TERMS = 5000
MAX_DF_RATIO = 0.55

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
PAGE_SPLIT = re.compile(r"(?=^## Page \d+\s*$)", re.MULTILINE)
HEADING_SPLIT = re.compile(r"(?=^## )", re.MULTILINE)
PAGE_NUM = re.compile(r"^## Page (\d+)", re.MULTILINE)

STOPWORDS = {
    "a", "au", "aux", "avec", "ce", "ces", "cet", "cette", "dans", "de", "des",
    "du", "elle", "en", "et", "eu", "il", "je", "la", "le", "les", "leur", "lui",
    "ma", "mais", "me", "mes", "mon", "ne", "nos", "notre", "nous", "on", "ou",
    "par", "pas", "pour", "qu", "que", "qui", "sa", "se", "ses", "son", "sur",
    "ta", "te", "tes", "ton", "tu", "un", "une", "vos", "votre", "vous", "y",
    "est", "sont", "etre", "ete", "fait", "peut", "plus", "tout", "tous",
    "toute", "toutes", "comme", "si", "sans", "sous", "chez", "entre", "apres",
    "avant", "lors", "doit", "doivent", "quel", "quelle", "quels", "quelles",
    "comment", "donc", "car", "ou", "où", "dont", "aussi", "très", "tres",
    "été", "etre", "être", "cette", "ces", "dans", "aux", "des",
}


def rel_path(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.casefold()


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", fold(text))
        if token not in STOPWORDS and len(token) > 2
    ]


def parse_front_matter(text: str) -> tuple[dict, str]:
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip().strip('"')
    return meta, text[match.end():]


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_long(text: str, size: int) -> list[str]:
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    parts = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            cut = text.rfind("\n", start + size // 2, end)
            if cut == -1:
                cut = text.rfind(" ", start + size // 2, end)
            if cut > start:
                end = cut
        piece = text[start:end].strip()
        if len(piece) >= MIN_CHARS:
            parts.append(piece)
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return parts


def document_kind(path: Path) -> str:
    if "fiches_dci" in path.parts:
        return "fiche"
    blob = " ".join(path.parts).casefold()
    name = path.name.casefold()
    if "documents_complementaires" in blob or "non_reference" in blob:
        return "complementaire"
    if "notice" in name:
        return "notice"
    if "rcp" in name:
        return "rcp"
    if "article" in name:
        return "article"
    return "document"


def dci_of(path: Path, meta: dict) -> str:
    if meta.get("dci"):
        return meta["dci"]
    if "fiches_dci" in path.parts:
        return path.stem
    try:
        return path.relative_to(PROCESSED_ROOT).parts[0]
    except ValueError:
        return ""


def passages_of(text: str, kind: str) -> list[tuple[str | None, str]]:
    text = clean_text(text)
    if not text:
        return []
    if kind == "fiche":
        blocks = [block.strip() for block in HEADING_SPLIT.split(text) if block.strip()]
        limit = 3500
    elif PAGE_SPLIT.search(text):
        blocks = [block.strip() for block in PAGE_SPLIT.split(text) if block.strip()]
        limit = CHUNK_SIZE
    else:
        blocks = [text]
        limit = CHUNK_SIZE

    passages = []
    for block in blocks:
        page_match = PAGE_NUM.search(block)
        page = page_match.group(1) if page_match else None
        pieces = [block] if len(block) <= limit else split_long(block, limit)
        for piece in pieces:
            if len(piece) >= MIN_CHARS:
                passages.append((page, piece))
    return passages


def with_context(dci: str, kind: str, passage: str) -> str:
    """Keep the drug name on every passage, including pages that never repeat it."""
    if not dci:
        return passage
    return f"DCI : {dci}. Type de document : {kind}.\n{passage}"


def iter_markdown() -> list[Path]:
    files = []
    if PROCESSED_ROOT.exists():
        files.extend(PROCESSED_ROOT.rglob("*.md"))
    if FICHES_ROOT.exists():
        files.extend(FICHES_ROOT.glob("*.md"))
    return sorted(path for path in files if path.is_file() and not path.name.startswith("."))


def build_chunks() -> list[dict]:
    chunks = []
    for path in iter_markdown():
        raw = path.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_front_matter(raw)
        kind = document_kind(path)
        dci = dci_of(path, meta)
        for page, passage in passages_of(body, kind):
            chunks.append(
                {
                    "id": f"c{len(chunks):04d}",
                    "source": rel_path(path),
                    "dci": dci,
                    "kind": kind,
                    "page": page,
                    "text": with_context(dci, kind, passage),
                }
            )
    return chunks


class BM25:
    """BM25 Okapi, même formule que la bibliothèque rank_bm25."""

    def __init__(self, documents: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.n = len(documents)
        self.doc_len = np.asarray([len(doc) for doc in documents], dtype=np.float64)
        self.avgdl = float(self.doc_len.mean()) if self.n else 0.0
        self.tfs = [Counter(doc) for doc in documents]
        df: dict[str, int] = {}
        for counts in self.tfs:
            for term in counts:
                df[term] = df.get(term, 0) + 1
        self.idf = {
            term: math.log((self.n - freq + 0.5) / (freq + 0.5) + 1.0)
            for term, freq in df.items()
        }

    def scores(self, query_tokens: list[str]) -> np.ndarray:
        result = np.zeros(self.n, dtype=np.float64)
        if not self.n or self.avgdl == 0:
            return result
        for term in query_tokens:
            idf = self.idf.get(term)
            if idf is None:
                continue
            for index, counts in enumerate(self.tfs):
                tf = counts.get(term)
                if not tf:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * self.doc_len[index] / self.avgdl)
                result[index] += idf * (tf * (self.k1 + 1)) / denom
        return result


def _mostly_digits(term: str) -> bool:
    digits = sum(character.isdigit() for character in term)
    return digits >= max(2, len(term) // 2)


def select_vocabulary(tokenized: list[list[str]]) -> list[str]:
    """Keep frequent medical words and rare names. Rarest-only vocab dropped both."""
    n_docs = len(tokenized)
    df: Counter = Counter()
    cf: Counter = Counter()
    for tokens in tokenized:
        cf.update(tokens)
        df.update(set(tokens))

    max_df = max(2, int(MAX_DF_RATIO * n_docs))
    content = []
    names = []
    for term, freq in df.items():
        if _mostly_digits(term) or freq > max_df:
            continue
        if freq >= 2:
            content.append(term)
        elif len(term) >= 6 and term.isalpha():
            names.append(term)

    content.sort(key=lambda term: cf[term], reverse=True)
    content = content[:MAX_CONTENT_TERMS]
    names.sort(key=lambda term: cf[term], reverse=True)
    chosen = set(content)
    rare_names = []
    for term in names:
        if term in chosen:
            continue
        rare_names.append(term)
        if len(rare_names) >= MAX_NAME_TERMS:
            break
    return content + rare_names


def fit_embeddings(texts: list[str]) -> dict:
    tokenized = [tokenize(text) for text in texts]
    n_docs = len(tokenized)
    df: dict[str, int] = {}
    for tokens in tokenized:
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1

    vocabulary = select_vocabulary(tokenized)
    index = {term: position for position, term in enumerate(vocabulary)}
    idf = np.asarray(
        [math.log((n_docs + 1) / (df[term] + 1)) + 1.0 for term in vocabulary],
        dtype=np.float64,
    )

    matrix = np.zeros((n_docs, len(vocabulary)), dtype=np.float64)
    for row, tokens in enumerate(tokenized):
        if not tokens:
            continue
        for term, count in Counter(tokens).items():
            column = index.get(term)
            if column is None:
                continue
            matrix[row, column] = (1.0 + math.log(count)) * idf[column]
        norm = np.linalg.norm(matrix[row])
        if norm:
            matrix[row] /= norm

    k = min(EMBED_DIM, n_docs - 1, len(vocabulary) - 1)
    if k < 2:
        raise SystemExit("Corpus trop petit pour calculer des embeddings.")

    rng = np.random.default_rng(0)
    oversample = min(matrix.shape[1], k + 16)
    sketch = matrix @ rng.standard_normal((matrix.shape[1], oversample))
    for _ in range(3):
        sketch, _ = np.linalg.qr(sketch, mode="reduced")
        sketch = matrix @ (matrix.T @ sketch)
    basis, _ = np.linalg.qr(sketch, mode="reduced")
    small = basis.T @ matrix
    left, singular, vt = np.linalg.svd(small, full_matrices=False)
    documents = basis @ left[:, :k]
    documents *= singular[:k]
    doc_norms = np.linalg.norm(documents, axis=1, keepdims=True)
    usable = doc_norms[:, 0] > 1e-8
    doc_norms[~usable] = 1.0
    documents = (documents / doc_norms).astype(np.float32)
    documents[~usable] = 0.0
    print(f"Passages sans vecteur : {int((~usable).sum())} / {n_docs}")

    return {
        "embeddings": documents,
        "vocabulary": vocabulary,
        "idf": idf.astype(np.float32),
        "components": vt[:k].astype(np.float32),
        "dimension": int(k),
    }


def embed_queries(texts: list[str], vocabulary: list[str], idf: np.ndarray, components: np.ndarray) -> np.ndarray:
    index = {term: position for position, term in enumerate(vocabulary)}
    queries = np.zeros((len(texts), len(vocabulary)), dtype=np.float64)
    idf64 = idf.astype(np.float64)
    for row, text in enumerate(texts):
        counts = Counter(tokenize(text))
        for term, count in counts.items():
            column = index.get(term)
            if column is None:
                continue
            queries[row, column] = (1.0 + math.log(count)) * idf64[column]
        norm = np.linalg.norm(queries[row])
        if norm:
            queries[row] /= norm
    vectors = queries @ components.astype(np.float64).T
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)


def save_store(chunks: list[dict], model: dict) -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    chunks_path = STORE_DIR / "chunks.jsonl"
    with chunks_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    np.save(STORE_DIR / "embeddings.npy", model["embeddings"])
    np.save(STORE_DIR / "idf.npy", model["idf"])
    np.save(STORE_DIR / "components.npy", model["components"])
    (STORE_DIR / "vocabulary.json").write_text(
        json.dumps(model["vocabulary"], ensure_ascii=False),
        encoding="utf-8",
    )
    by_kind: dict[str, int] = {}
    dcis = set()
    for chunk in chunks:
        by_kind[chunk["kind"]] = by_kind.get(chunk["kind"], 0) + 1
        if chunk["dci"]:
            dcis.add(chunk["dci"])
    manifest = {
        "method": "tfidf-svd",
        "description": "Embeddings sémantiques latents (TF-IDF + SVD), vecteurs normalisés",
        "created": datetime.now(timezone.utc).isoformat(),
        "n_chunks": len(chunks),
        "n_terms": len(model["vocabulary"]),
        "dimension": model["dimension"],
        "normalized": True,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "by_kind": by_kind,
        "n_dci": len(dcis),
    }
    (STORE_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_store() -> dict:
    chunks_path = STORE_DIR / "chunks.jsonl"
    required = [
        chunks_path,
        STORE_DIR / "embeddings.npy",
        STORE_DIR / "idf.npy",
        STORE_DIR / "components.npy",
        STORE_DIR / "vocabulary.json",
    ]
    if any(not path.exists() for path in required):
        raise SystemExit("Base vectorielle absente. Lancer d'abord src/build_vector_store.py.")
    chunks = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    embeddings = np.load(STORE_DIR / "embeddings.npy")
    if len(chunks) != len(embeddings):
        raise SystemExit("chunks.jsonl et embeddings.npy n'ont pas le même nombre de lignes.")
    return {
        "chunks": chunks,
        "embeddings": embeddings,
        "idf": np.load(STORE_DIR / "idf.npy"),
        "components": np.load(STORE_DIR / "components.npy"),
        "vocabulary": json.loads((STORE_DIR / "vocabulary.json").read_text(encoding="utf-8")),
    }
