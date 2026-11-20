"""
Configuration COMMUNE pour la Semaine 2 (recherche par le sens).

TOUTE l'équipe doit garder les mêmes valeurs ici (surtout EMBEDDING_MODEL) et utiliser
le même build_chunks.py, pour que les résultats soient comparables.
Si quelqu'un change une valeur, il doit le dire au groupe.
"""
import json
import re
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------- chemins
# Ce fichier est dans src/  ->  parent.parent = racine du projet COGNIVEX/
ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "data" / "corpus"
CHUNKS_FILE = ROOT / "data" / "processed" / "chunks.jsonl"
VECTOR_DB_DIR = ROOT / "data" / "vectordb"
EVAL_DIR = ROOT / "docs" / "evaluation"
QUESTIONS_FILE = EVAL_DIR / "questions_llm.md"
COLLECTION_NAME = "cognivex_chunks"

# ---------------------------------------------------------------- découpage
# Le découpage est fait par src/build_chunks.py (MAX_WORDS=120, OVERLAP_WORDS=20).
# Les étapes 2 et 3 lisent simplement data/processed/chunks.jsonl.

# ---------------------------------------------------------------- embeddings
# Modèle multilingue (français OK), accepte jusqu'à 512 tokens => pas de troncature
# avec des chunks de 1000 caractères (contrairement à paraphrase-multilingual-MiniLM : 128 tokens).
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
TOP_K = 5

# Nettoyage du bruit d'impression du navigateur (en-têtes / pieds de page) au chargement.
# Ne modifie PAS chunks.jsonl : le nettoyage est appliqué en mémoire par charger_chunks().
NETTOYER_BRUIT = True
MIN_CHUNK_CHARS = 30      # un chunk qui ne contient plus que du bruit est ignoré


def passage_prefix() -> str:
    """Les modèles E5 demandent un préfixe 'passage: ' côté documents."""
    return "passage: " if "e5" in EMBEDDING_MODEL.lower() else ""


def query_prefix() -> str:
    """... et 'query: ' côté question."""
    return "query: " if "e5" in EMBEDDING_MODEL.lower() else ""


def texte_indexe(chunk: dict) -> str:
    """
    Texte réellement indexé (embedding ET recherche par mots-clés).
    On ajoute le contexte (DCI / produit / type de doc / section) devant le texte,
    ça aide beaucoup quand un chunk seul ne dit pas de quel médicament il parle.
    """
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
    """Retire en-têtes/pieds de page d'impression. Garde les vrais liens (ex. pharmacovigilance)."""
    for motif in _BRUIT:
        texte = motif.sub(" ", texte)
    return " ".join(texte.split())


def charger_chunks() -> list[dict]:
    """
    Lit data/processed/chunks.jsonl (produit par build_chunks.py) et le met au format
    interne utilisé par les étapes 2 et 3 :
        chunk_id, dci, produit, doc_type, fichier, page, section, text

    - accepte les noms de champs de build_chunks.py (brand, document_type, file_path)
    - nettoie le bruit d'impression (voir nettoyer_texte)
    - rend les chunk_id UNIQUES : dans build_chunks.py l'id est DCI_marque_page_n, donc
      le RCP et la Notice d'une même marque (ou deux articles) ont le MÊME id -> ChromaDB
      refuserait l'ajout (DuplicateIDError).
    """
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
