import json
import os
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

CORPUS_DIR = ROOT / "data" / "corpus"
OCR_DIR = ROOT / "data" / "processed_corpus"
SEMAINE = os.getenv("COGNIVEX_SEMAINE", "semaine 2")
EVAL_DIR = ROOT / "docs" / "evaluation" / SEMAINE
QUESTIONS_FILE = EVAL_DIR / "questions_llm.md"

COLLECTION_NAME = "cognivex_chunks"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
TOP_K = 5

# Experience de decoupage
EXPERIENCE = int(os.getenv("COGNIVEX_EXP", "2"))

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

REFERENCE_XLSX = ROOT / "data" / "reference" / "Liste 40 medicaments final.xlsx"
PRODUITS_FILE = ROOT / "data" / "processed" / "produits_details.json"
METADATA_FILE = ROOT / "data" / "processed" / "corpus_metadata.json"
TABLE_NOMS_FILE = ROOT / "data" / "processed" / "table_noms_commerciaux.csv"
REFERENCES_FILE = EVAL_DIR / "references_hit_at_3.json"

NETTOYER_BRUIT = True
MIN_CHUNK_CHARS = 30

# Recherche hybride
POOL_HYBRIDE = 30
RRF_K = 60


def motif_ocr(expression: str) -> str:
    """Construit un motif tolerant aux espaces inseres par l'OCR."""
    caracteres = [
        re.escape(caractere)
        for caractere in expression
        if not caractere.isspace()
    ]
    return r"\s*".join(caracteres)


_DATE = r"\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}\s*[AP]M"

# NETTOYAGE DU BRUIT OCR

_BRUIT = [
    re.compile(
        r'---\s*source:\s*"[^"]*"\s*dci:\s*"[^"]*"\s*brand:\s*"[^"]*"\s*'
        r'method:\s*"[^"]*"\s*processed:\s*"[^"]*"\s*chars:\s*\d+\s*---',
        re.I,
    ),

    re.compile(
        r'\bdoc:\s*"[^"]*"\s+processed:\s*"[^"]*"\s+'
        r'chars:\s*\d+\s*---',
        re.I,
    ),

    re.compile(
        r"<!--\s*(?:Start|End) of picture text\s*-->",
        re.I,
    ),

    re.compile(
        r"\b\d{1,2}/\d{1,2}/\d{4},?\s*"
        r"\d\s*\d\s*:\s*\d\s*\d\b",
        re.I,
    ),

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

    re.compile(motif_ocr("pharmaveille-dz.vercel.app"), re.I),
    re.compile(motif_ocr("dzair-pharma.net"), re.I),
    re.compile(
        motif_ocr("base-donnees-publique.medicaments.gouv.fr"),
        re.I,
    ),

    re.compile(
        _DATE + r"\s+Base de Données Publique des Médicaments",
        re.I,
    ),

    re.compile(
        r"Base de Données Publique(?: des(?: Médicaments)?)?",
        re.I,
    ),

    re.compile(
        r"Fiche info RCP Notice(?: Bon usage)?",
        re.I,
    ),

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

    re.compile(
        r"\bCode\s*:\s*[A-Z0-9./-]+\s+Version\s*:\s*\d+\s+"
        r"Page\s*\d+\s+sur\s*\d+\s+Version\s*:\s*\d+",
        re.I,
    ),

    re.compile(r"<br\s*/?>", re.I),
]


def passage_prefix() -> str:
    """Prefixe demande par les modeles E5 pour les passages."""
    return "passage: " if "e5" in EMBEDDING_MODEL.lower() else ""


def query_prefix() -> str:
    """Prefixe demande par les modeles E5 pour les questions."""
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
    """Met en minuscules et enleve accents et ponctuation."""
    text = unicodedata.normalize("NFKD", str(text))

    text = "".join(
        caractere
        for caractere in text
        if not unicodedata.combining(caractere)
    )

    text = re.sub(r"[^a-z0-9]+", " ", text.casefold())

    return " ".join(text.split())


def canon_dci(nom: str) -> str:
    """Normalise le nom de la DCI."""
    return normalize(re.sub(r"\(.*?\)", " ", str(nom)))

# FONCTION DE NETTOYAGE UTILISEE DANS BUILD_CHUNKS

def nettoyer_texte(texte: str) -> str:
    # Retire les marqueurs de texte barre parfois ajoutes par l'OCR.
    texte = texte.replace("~~", "")

    for motif in _BRUIT:
        texte = motif.sub(" ", texte)

    return " ".join(texte.split())

# CHARGEMENT DES CHUNKS

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

# PROVENANCE DES DOCUMENTS

TYPES_SOURCE = {
    "dz_official": "Algérie — officielle (ANPP / MIPH)",
    "label_country_unverified": "RCP / notice de produit (pays non vérifié)",
    "nomenclature_export": "Export de nomenclature (Pharm'Net)",
    "fr_institutional": "France — institutionnelle (ANSM / base publique)",
    "us_dailymed": "États-Unis — DailyMed",
    "dz_professional_site": "Algérie — site professionnel (DwaDZ...)",
    "complementary_non_reference": "Complémentaire (hors référence)",
    "scientific_article": "Article scientifique",
    "product_image": "Image de produit (OCR)",
    "non_classe": "Non classé",
}

_PROVENANCE: dict[str, tuple[str, int]] | None = None


def _cle_chemin(chemin: str) -> str:
    """Normalise le chemin du document."""
    p = unicodedata.normalize("NFC", chemin).replace("\\", "/")

    for prefixe in ("data/corpus/", "data/processed_corpus/"):
        if p.startswith(prefixe):
            p = p[len(prefixe):]

    return os.path.splitext(p)[0].lower()


def _charger_provenance() -> dict[str, tuple[str, int]]:
    global _PROVENANCE

    if _PROVENANCE is None:
        _PROVENANCE = {}

        if METADATA_FILE.is_file():
            meta = json.loads(
                METADATA_FILE.read_text(encoding="utf-8")
            )

            for entree in meta.get("corpus", []):
                fichiers = list(entree.get("source_files", []))

                for marque in entree.get("brands", []):
                    fichiers += marque.get("files", [])

                for f in fichiers:
                    _PROVENANCE[_cle_chemin(f["relative_path"])] = (
                        f.get("source_type", "non_classe"),
                        int(f.get("authority_tier", 9)),
                    )

    return _PROVENANCE


def provenance(chunk: dict) -> tuple[str, int]:
    """Retourne le type de source et son niveau d'autorite."""

    if chunk.get("doc_type") == "Nomenclature":
        return "Algérie — nomenclature MIPH (août 2026)", 1

    type_source, niveau = _charger_provenance().get(
        _cle_chemin(chunk.get("fichier", "")),
        (None, 9),
    )

    if type_source is None:
        nom = chunk.get("fichier", "").lower()

        if "anpp" in nom:
            type_source, niveau = "dz_official", 1

        elif any(
            m in nom
            for m in ("dwadz", "dwa-", "dwa_", "dzair", "source")
        ):
            type_source, niveau = "dz_professional_site", 4

        elif "dailymed" in nom:
            type_source, niveau = "us_dailymed", 3

        elif "ansm" in nom:
            type_source, niveau = "fr_institutional", 3

        else:
            type_source = "non_classe"

    return TYPES_SOURCE.get(type_source, type_source), niveau