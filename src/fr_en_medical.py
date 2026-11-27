"""
fr_en_medical.py
----------------
French → English medical term dictionary for BM25 query expansion.

Purpose:
    BM25 is keyword-based and language-blind. When a French query is asked
    but the document (RCP/Notice) is in English, BM25 scores 0 because the
    words don't match. This dictionary expands the French query with its
    English equivalents so BM25 can match English documents too.

Usage:
    from src.fr_en_medical import translate_query_fr_to_en, expand_query_bilingual
    expanded = expand_query_bilingual("précautions femme enceinte ciprofloxacine")
    # → "précautions femme enceinte ciprofloxacine precautions pregnant woman pregnancy"
"""

import re
import unicodedata

# ── FR → EN medical dictionary ────────────────────────────────────────────────
# Key   = French term (lowercase, no accents needed — matching is normalized)
# Value = list of English equivalents to append to the query

FR_EN_DICT = {
    # General medical / safety
    "precaution": ["precaution", "warning", "caution"],
    "precautions": ["precautions", "warnings", "cautions"],
    "contre-indication": ["contraindication", "contraindicated"],
    "contre-indications": ["contraindications", "contraindicated"],
    "contre-indique": ["contraindicated"],
    "effet secondaire": ["side effect", "adverse effect", "adverse reaction"],
    "effets secondaires": ["side effects", "adverse effects", "adverse reactions"],
    "effet indesirable": ["adverse effect", "adverse reaction", "undesirable effect"],
    "effets indesirables": ["adverse effects", "adverse reactions"],
    "interaction": ["interaction", "drug interaction"],
    "interactions": ["interactions", "drug interactions"],
    "surdosage": ["overdose", "overdosage"],
    "posologie": ["dosage", "dose", "dosing", "administration"],
    "indication": ["indication", "indicated"],
    "indications": ["indications"],
    "composition": ["composition", "ingredients", "active substance"],
    "conservation": ["storage", "store"],
    "notice": ["leaflet", "patient information leaflet", "PIL"],
    "resume caracteristiques produit": ["summary of product characteristics", "SmPC", "SPC"],
    "rcp": ["SmPC", "SPC", "summary product characteristics"],

    # Patient profiles
    "femme enceinte": ["pregnant woman", "pregnancy", "pregnant"],
    "grossesse": ["pregnancy", "pregnant"],
    "allaitement": ["breastfeeding", "lactation", "nursing"],
    "enfant": ["child", "children", "pediatric", "paediatric"],
    "enfants": ["children", "pediatric"],
    "nourrisson": ["infant", "neonate"],
    "nouveau-ne": ["neonate", "newborn"],
    "personne agee": ["elderly", "geriatric", "older patient"],
    "sujet age": ["elderly", "geriatric"],
    "insuffisance renale": ["renal impairment", "renal failure", "kidney failure"],
    "insuffisance hepatique": ["hepatic impairment", "liver failure"],
    "insuffisance cardiaque": ["heart failure", "cardiac failure"],

    # Dosage / forms
    "comprime": ["tablet", "tablet oral"],
    "comprimes": ["tablets"],
    "gelule": ["capsule"],
    "gelules": ["capsules"],
    "suspension": ["suspension", "oral suspension"],
    "injectable": ["injection", "injectable"],
    "sirop": ["syrup", "oral solution"],
    "dose": ["dose", "dosage"],
    "doses": ["doses"],
    "dose maximale": ["maximum dose", "max dose"],
    "dose journaliere": ["daily dose"],
    "prise": ["dose", "intake"],

    # Therapeutic classes
    "antibiotique": ["antibiotic", "antibacterial"],
    "antibiotiques": ["antibiotics", "antibacterial"],
    "antalgique": ["analgesic", "painkiller", "pain relief"],
    "antalgiques": ["analgesics"],
    "anti-inflammatoire": ["anti-inflammatory", "NSAID"],
    "anti-inflammatoires": ["anti-inflammatory", "NSAIDs"],
    "antihypertenseur": ["antihypertensive", "blood pressure"],
    "antihypertenseurs": ["antihypertensives"],
    "analgesique": ["analgesic", "pain relief"],

    # Conditions / symptoms
    "infection urinaire": ["urinary tract infection", "UTI"],
    "infection": ["infection"],
    "douleur": ["pain"],
    "fievre": ["fever"],
    "inflammation": ["inflammation"],
    "hypertension": ["hypertension", "high blood pressure"],
    "diabete": ["diabetes"],

    # Drug actions
    "traitement": ["treatment", "therapy"],
    "therapeutique": ["therapeutic", "therapy"],
    "efficacite": ["efficacy", "effectiveness"],
    "tolerance": ["tolerability", "tolerance"],
    "absorption": ["absorption"],
    "distribution": ["distribution"],
    "elimination": ["elimination", "excretion"],
    "demi-vie": ["half-life"],
    "biodisponibilite": ["bioavailability"],
}


def _normalize_text(text: str) -> str:
    """Remove accents and lowercase for dictionary lookup."""
    nfkd = unicodedata.normalize("NFKD", text)
    return nfkd.encode("ascii", "ignore").decode("ascii").lower()


def translate_query_fr_to_en(query: str) -> list:
    """
    Find French medical terms in the query and return a list of English equivalents.

    Returns a flat list of English words to append to the query.
    """
    q_norm = _normalize_text(query)
    english_terms = []

    # Try multi-word phrases first (longer matches = more specific)
    for fr_term in sorted(FR_EN_DICT.keys(), key=len, reverse=True):
        fr_norm = _normalize_text(fr_term)
        if fr_norm in q_norm:
            english_terms.extend(FR_EN_DICT[fr_term])

    return english_terms


def expand_query_bilingual(query: str) -> str:
    """
    Return query + English equivalents of any French medical terms found.

    Example:
        "précautions femme enceinte ciprofloxacine"
        → "précautions femme enceinte ciprofloxacine precautions pregnant woman pregnancy contraindicated"
    """
    en_terms = translate_query_fr_to_en(query)
    if not en_terms:
        return query
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for t in en_terms:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return query + " " + " ".join(unique)


# ── Quick self-test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "précautions femme enceinte ciprofloxacine",
        "contre-indications naproxène insuffisance rénale",
        "posologie enfants amoxicilline suspension",
        "effets indésirables lévofloxacine",
        "DOLIPRANE comprimé 1000mg",
    ]
    for t in tests:
        expanded = expand_query_bilingual(t)
        en = translate_query_fr_to_en(t)
        print(f"IN  : {t}")
        print(f"EN+ : {en}")
        print(f"OUT : {expanded[:120]}")
        print()
