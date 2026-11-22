import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "data" / "corpus"
CHUNKS_FILE = ROOT / "data" / "processed" / "chunks.jsonl"
VECTOR_DB_DIR = ROOT / "data" / "processed" / "vectordb_LastVersion"
EVAL_DIR = ROOT / "docs" / "evaluation"
QUESTIONS_FILE = EVAL_DIR / "questions_llm.md"
COLLECTION_NAME = "cognivex_chunks"


EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
TOP_K = 5

NETTOYER_BRUIT = True
MIN_CHUNK_CHARS = 30     

def passage_prefix() -> str:
    """Les modèles E5 demandent un préfixe 'passage: ' côté documents."""
    return "passage: " if "e5" in EMBEDDING_MODEL.lower() else ""


def query_prefix() -> str:
    """... et 'query: ' côté question."""
    return "query: " if "e5" in EMBEDDING_MODEL.lower() else ""


def texte_indexe(chunk: dict) -> str:
    contexte = " | ".join(
        x for x in (chunk["dci"], chunk["produit"], chunk["doc_type"], chunk["section"]) if x
    )
    return f"{contexte}\n{chunk['text']}"


def normalize(text: str) -> str:
    """minuscules, sans accents, sans ponctuation (pour comparer des noms)."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text.casefold())
    return " ".join(text.split())


_DATE = r"\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}\s*[AP]M"
_BRUIT = [
    re.compile(_DATE + r"\s+Base de Données Publique des Médicaments", re.I),  # en-tête BDPM
    re.compile(r"https?://\S+\s+\d+/\d+\b"),       # pied de page : URL + compteur "3/12"
    re.compile(_DATE),                                # date d'impression restante (articles)
    re.compile(r"https?://base-donnees-publique\S*"),  # URL BDPM coupée par la limite du chunk
    re.compile(r"Base de Données Publique(?: des(?: Médicaments)?)?", re.I),  # en-tête coupé en 2 chunks
    re.compile(r"Fiche info RCP Notice(?: Bon usage)?", re.I),   # onglets de la page BDPM
]


def nettoyer_texte(texte: str) -> str:
    for motif in _BRUIT:
        texte = motif.sub(" ", texte)
    return " ".join(texte.split())


def charger_chunks() -> list[dict]:
    if not CHUNKS_FILE.is_file():
        raise FileNotFoundError(
            f"{CHUNKS_FILE} introuvable : lancez d'abord  python src/build_chunks.py"
        )
    chunks = []
    with open(CHUNKS_FILE, encoding="utf-8") as f:
        for numero, ligne in enumerate(f):
            if not ligne.strip():
                continue
            c = json.loads(ligne)
            texte = nettoyer_texte(c["text"]) if NETTOYER_BRUIT else c["text"]
            if len(texte) < MIN_CHUNK_CHARS:
                continue  # chunk contenant uniquement du bruit
            produit = c.get("brand", c.get("produit", "")) or ""
            if normalize(produit) == normalize("À vérifier"):
                produit = ""  # valeur "inconnue" de build_chunks.py : on ne l'indexe pas
            chunks.append({
                "chunk_id": f"{numero:05d}-{c['chunk_id']}",
                "dci": c["dci"],
                "produit": produit,
                "doc_type": c.get("document_type", c.get("doc_type", "")),
                "fichier": c.get("file_path", c.get("fichier", "")),
                "page": c["page"],
                "section": c.get("section", ""),
                "text": texte,
            })
    return chunks