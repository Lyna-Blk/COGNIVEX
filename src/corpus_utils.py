"""
corpus_utils.py — fonctions communes aux scripts Cognivex.

Structure attendue du projet :
    COGNIVEX/
      data/
        corpus/<dci>/[<produit>/]fichiers.(pdf|jpg|png|webp)
        fiches_dci/*.md
        Liste 40 medicaments.xlsx
      src/   <- ces scripts
"""
import hashlib
import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path

logging.getLogger("pdfminer").setLevel(logging.ERROR)   # supprime les warnings FontBBox

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CORPUS = DATA / "corpus"
FICHES = DATA / "fiches_dci"
EXCEL = DATA / "Liste 40 medicaments.xlsx"
TEXT_DIR = DATA / "corpus_text"
KEY_DIR = DATA / "key_info"
METADATA = DATA / "metadata.json"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
BDPM_URL = "https://base-donnees-publique.medicaments.gouv.fr/"


# ---------------------------------------------------------------- noms
def decode_name(s: str) -> str:
    """Certains zip décodés sous Linux donnent 'n#U00e9fopam' au lieu de 'néfopam'."""
    return re.sub(r"#U([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)


def norm(s: str) -> str:
    """minuscule, sans accents, sans ponctuation multiple — pour comparer des noms."""
    s = unicodedata.normalize("NFKD", decode_name(str(s)))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9+]+", " ", s).strip()


def slug(s: str) -> str:
    return norm(s).replace("+", "et").replace(" ", "_")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- PDF
HEADER_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2},\s+\d{1,2}:\d{2}\s+[AP]M\b")
FOOTER_RE = re.compile(r"^(https?://\S+)?\s*\d{1,3}/\d{1,3}$")


def read_pdf_pages(path: Path, ocr_fallback: bool = True):
    """Retourne (pages, needs_ocr). pages = liste de textes bruts, un par page PDF."""
    import pdfplumber
    pages, needs_ocr = [], False
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            if len(txt.strip()) < 30 and ocr_fallback:        # page scannée ?
                try:
                    import pytesseract
                    img = page.to_image(resolution=200).original
                    txt = pytesseract.image_to_string(img, lang="fra")
                except Exception:
                    needs_ocr = True
            pages.append(txt)
    return pages, needs_ocr


def clean_page(txt: str):
    """Enlève en-têtes/pieds de page d'impression navigateur (BDPM) et lignes vides."""
    out = []
    for line in txt.splitlines():
        l = line.strip()
        if not l:
            continue
        if HEADER_RE.match(l) or FOOTER_RE.match(l):
            continue
        if l.startswith("Dernière mise à jour le") and len(l) < 40:
            continue
        out.append(l)
    return out


# ---------------------------------------------------------------- classification
def to_iso(d: str):
    """'21/02/2023' -> '2023-02-21'"""
    try:
        return datetime.strptime(d, "%d/%m/%Y").date().isoformat()
    except Exception:
        return None


def print_date_iso(first_page: str):
    """En-tête d'impression 'mm/dd/yy, h:mm PM' -> date de consultation ISO."""
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2}),", first_page.strip())
    if not m:
        return None
    mm, dd, yy = map(int, m.groups())
    try:
        return datetime(2000 + yy, mm, dd).date().isoformat()
    except Exception:
        return None


def classify_pdf(first_page: str, filename: str, full_text: str = ""):
    """Retourne (role, source dict, product_title, doc_date, consulted_date, bdpm_update)."""
    up = norm(first_page[:800])
    fname = filename.lower()
    lines = [l.strip() for l in first_page.splitlines() if l.strip()]

    # ---- rôle
    if "resume des caracteristiques du produit" in up or "1 denomination du medicament" in up:
        role = "rcp"
    elif "veuillez lire attentivement" in norm(first_page[:3000]) or "notice" in up[:200] and "fiche info" in up:
        role = "notice"
    elif fname.startswith("article") or "publie le" in up:
        role = "article"
    elif fname.startswith("rcp"):
        role = "rcp"
    elif fname.startswith("notice"):
        role = "notice"
    else:
        role = "autre"
    # le nom du fichier doit confirmer
    # (si "Notice" dans le contenu mais RCP dans le nom, on garde le contenu et on avertira)

    source = {"name": None, "country": None, "kind": None, "url": None}
    title, doc_date, bdpm_update = None, None, None
    consulted = print_date_iso(first_page)

    if "Base de Données Publique des Médicaments" in first_page[:300]:
        source = {"name": "Base de Données Publique des Médicaments (ANSM)", "country": "France",
                  "kind": "officielle étrangère", "url": BDPM_URL}
        m = re.search(r"ANSM - Mis à jour le\s*:\s*(\d{2}/\d{2}/\d{4})", first_page)
        doc_date = to_iso(m.group(1)) if m else None
        m = re.search(r"Dernière mise à jour le\s+(\d{2}/\d{2}/\d{4})", first_page)
        bdpm_update = to_iso(m.group(1)) if m else None
        # titre = lignes entre "Dernière mise à jour" et "Fiche info"
        buf, on = [], False
        for l in lines:
            if l.startswith("Dernière mise à jour"):
                on = True
                continue
            if l.startswith("Fiche info"):
                break
            if on:
                buf.append(l)
        title = " ".join(buf) or None
    elif "ldmgroupe" in full_text.lower() or "ANNEXE I" in first_page[:40]:
        labo = "LDM (Constantine)" if "ldmgroupe" in full_text.lower() else None
        source = {"name": "RCP au format algérien" + (f" — laboratoire {labo}" if labo else ""),
                  "country": "Algérie", "kind": "à confirmer (ANPP ou site du laboratoire)", "url": None}
        m = re.search(r"Date de mise à jour du texte\s*\n?\s*([A-Za-zéû]+\s+\d{4})", full_text)
        doc_date = m.group(1) if m else None
        m = re.search(r"forme pharmaceutique\s*\n\s*(.+)", first_page)
        title = m.group(1).strip().rstrip(".") if m else None
    elif role == "article":
        m = re.search(r"PUBLIÉ LE\s+(\d{2}/\d{2}/\d{4})", first_page)
        doc_date = to_iso(m.group(1)) if m else None
        title = lines[2] if len(lines) > 2 else None
        source = {"name": "Article « bon usage » (source à préciser)", "country": "France (à confirmer)",
                  "kind": "à confirmer", "url": None}
    return role, source, title, doc_date, consulted, bdpm_update


def brand_in_nomenclature(product_title, brands):
    """True si une marque de la nomenclature (Excel) est un préfixe de mots du titre produit."""
    if not product_title:
        return None
    t = " " + norm(product_title) + " "
    for b in brands:
        nb = norm(b)
        if nb and t.startswith(" " + nb + " "):
            return True
    return False
