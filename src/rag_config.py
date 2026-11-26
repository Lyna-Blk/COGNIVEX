import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

CORPUS_DIR = ROOT / "data" / "corpus"
OCR_DIR = ROOT / "data" / "processed_corpus"
EVAL_DIR = ROOT / "docs" / "evaluation"
QUESTIONS_FILE = EVAL_DIR / "questions_llm.md"

COLLECTION_NAME = "cognivex_chunks"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
TOP_K = 5

EXPERIENCE = 3

CHUNK_SETTINGS = {
    1: {"max_words": 120, "overlap_words": 20},
    2: {"max_words": 240, "overlap_words": 40},
    3: {"max_words": 500, "overlap_words": 75},
}

MAX_WORDS = CHUNK_SETTINGS[EXPERIENCE]["max_words"]
OVERLAP_WORDS = CHUNK_SETTINGS[EXPERIENCE]["overlap_words"]

CHUNKS_FILE = ROOT / "data" / "processed" / f"chunks_exp{EXPERIENCE}.jsonl"
EMBEDDINGS_FILE = (
    ROOT / "data" / "processed" / "embeddings"
    / f"embeddings_exp{EXPERIENCE}.npy"
)
VECTOR_DB_DIR = ROOT / "data" / "processed" / f"vectordb_exp{EXPERIENCE}"

NETTOYER_BRUIT = True
MIN_CHUNK_CHARS = 30


def motif_ocr(expression: str) -> str:
    """Construit un motif tolérant aux espaces insérés par l'OCR."""
    caracteres = [
        re.escape(caractere)
        for caractere in expression
        if not caractere.isspace()
    ]
    return r"\s*".join(caracteres)


_DATE = r"\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}\s*[AP]M"

_BRUIT = [
    # Métadonnées techniques ajoutées par l'OCR
    re.compile(
        r'\bdoc:\s*"[^"]*"\s+processed:\s*"[^"]*"\s+'
        r'chars:\s*\d+\s*---',
        re.I,
    ),
    re.compile(
        r"<!--\s*(?:Start|End) of picture text\s*-->",
        re.I,
    ),

    # Horodatage des pages web récupérées, y compris chiffres espacés par l'OCR
    re.compile(
        r"\b\d{1,2}/\d{1,2}/\d{4},?\s*"
        r"\d\s*\d\s*:\s*\d\s*\d\b",
        re.I,
    ),

    # Boutons et menus répétitifs de DwaDZ
    re.compile(
        r"Voir\s*la\s*bo[iî]te\s*\(\s*Google\s*[)）]",
        re.I,
    ),
   re.compile(
    r"Tous\s*les\s*m[eé]dicaments\s*avec\s*cette\s*DC[I1l]"
    r"\s*(?:Retour\s*←?)?",
    re.I,
),
    re.compile(
        motif_ocr("Toutes les presentations de")
        + r"\s*[A-Z0-9_-]+\s*"
        + motif_ocr("Retour"),
        re.I,
    ),
    re.compile(motif_ocr("Voir plus"), re.I),
    re.compile(motif_ocr("Trouver une pharma"), re.I),
    re.compile(motif_ocr("Cartes du monde"), re.I),
    re.compile(motif_ocr("Lire l'histoire"), re.I),
    re.compile(motif_ocr("Lire I'histoire"), re.I),
    re.compile(motif_ocr("Copier le lien WhatsApp"), re.I),
    re.compile(motif_ocr("Partager cette fiche"), re.I),
    re.compile(motif_ocr("Suivre la page"), re.I),

    # Domaines répétés : on enlève le domaine, pas les informations du médicament
    re.compile(
        motif_ocr("pharmaveille-dz.vercel.app"),
        re.I,
    ),
    re.compile(
        motif_ocr("dzair-pharma.net"),
        re.I,
    ),
    re.compile(
        motif_ocr("base-donnees-publique.medicaments.gouv.fr"),
        re.I,
    ),

    # En-têtes et onglets répétitifs de la base française
    re.compile(
        _DATE + r"\s+Base de Données Publique des Médicaments",
        re.I,
    ),
    re.compile(
        r"Base de Données Publique(?: des(?: Médicaments)?)?",
        re.I,
    ),
    re.compile(r"Fiche info RCP Notice(?: Bon usage)?", re.I),

    # Liens de navigation et pied de page de Légifrance
    re.compile(
        r"legifrance\s*\.\s*gouv\s*\.\s*fr"
        r"[\s\S]{0,350}?Nos\s*partenaires",
        re.I,
    ),
    re.compile(
        r"Sauf\s*mention\s*contraire\s*,?\s*tous\s*les\s*contenus\s*"
        r"de\s*ce\s*site\s*sont\s*sous\s*licence\s*"
        r"etal\s*a?\s*b\s*[-–]\s*2\s*[.,]\s*[0oO]"
        r"(?:\s*\d+\s*/\s*\d+)?",
        re.I,
    ),

    # Références répétées du code, de la version et de la pagination des RCP
    re.compile(
        r"\bCode\s*:\s*[A-Z0-9./-]+\s+Version\s*:\s*\d+\s+"
        r"Page\s*\d+\s+sur\s*\d+\s+Version\s*:\s*\d+",
        re.I,
    ),

    # Balises HTML laissées par l'extraction OCR
    re.compile(r"<br\s*/?>", re.I),
]


def passage_prefix() -> str:
    """Préfixe demandé par les modèles E5 pour les passages."""
    return "passage: " if "e5" in EMBEDDING_MODEL.lower() else ""


def query_prefix() -> str:
    """Préfixe demandé par les modèles E5 pour les questions."""
    return "query: " if "e5" in EMBEDDING_MODEL.lower() else ""


def texte_indexe(chunk: dict) -> str:
    contexte = " | ".join(
        valeur
        for valeur in (
            chunk.get("dci", ""),
            chunk.get("produit", ""),
            chunk.get("doc_type", ""),
            chunk.get("section", ""),
        )
        if valeur
    )
    return f"{contexte}\n{chunk['text']}"


def normalize(text: str) -> str:
    """Met en minuscules et enlève accents et ponctuation."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(
        caractere
        for caractere in text
        if not unicodedata.combining(caractere)
    )
    text = re.sub(r"[^a-z0-9]+", " ", text.casefold())
    return " ".join(text.split())


def nettoyer_texte(texte: str) -> str:
    # Retire les marqueurs de texte barré parfois ajoutés par l'OCR.
    texte = texte.replace("~~", "")

    for motif in _BRUIT:
        texte = motif.sub(" ", texte)

    return " ".join(texte.split())


def charger_chunks() -> list[dict]:
    if not CHUNKS_FILE.is_file():
        raise FileNotFoundError(
            f"{CHUNKS_FILE} introuvable. "
            "Lance d'abord python src/build_chunks.py."
        )

    chunks = []

    with CHUNKS_FILE.open(encoding="utf-8") as fichier:
        for numero, ligne in enumerate(fichier):
            if not ligne.strip():
                continue

            chunk_brut = json.loads(ligne)
            texte = chunk_brut["text"]

            if NETTOYER_BRUIT:
                texte = nettoyer_texte(texte)

            if len(texte) < MIN_CHUNK_CHARS:
                continue

            produit = chunk_brut.get(
                "brand",
                chunk_brut.get("produit", ""),
            ) or ""

            if normalize(produit) == normalize("À vérifier"):
                produit = ""

            chunks.append({
                "chunk_id": f"{numero:05d}-{chunk_brut['chunk_id']}",
                "dci": chunk_brut.get("dci", ""),
                "produit": produit,
                "doc_type": chunk_brut.get(
                    "document_type",
                    chunk_brut.get("doc_type", ""),
                ),
                "fichier": chunk_brut.get(
                    "file_path",
                    chunk_brut.get("fichier", ""),
                ),
                "page": chunk_brut.get("page", ""),
                "section": chunk_brut.get("section", ""),
                "text": texte,
            })

    return chunks