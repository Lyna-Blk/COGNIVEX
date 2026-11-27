"""
normalize_names.py
------------------
Normalise un nom de médicament (commercial, DCI, variante, faute de frappe)
et retourne la DCI canonique + informations associées.

Usage en ligne de commande :
    python src/normalize_names.py "dolipranee"
    python src/normalize_names.py "AMOXIL 500"
    python src/normalize_names.py --eval        # génère le tableau d'évaluation

Usage en import :
    from src.normalize_names import normalize_query
    result = normalize_query("dolipranee")
"""

import json
import re
import sys
import unicodedata
import csv
from pathlib import Path

# ── Chemins ───────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DICT_PATH = ROOT / "data" / "knowledge_graph" / "dci_dict.json"
EVAL_PATH = ROOT / "data" / "evaluation" / "normalisation_eval.csv"

# ── Alias manuels (noms commerciaux connus mais absents de l'Excel algérien) ──
# Format : "nom_normalized" -> "dci_key" (doit correspondre à une clé de dci_dict)
MANUAL_ALIASES: dict[str, str] = {
    # cotrimoxazole (long DCI name → short folder name used in corpus)
    "cotrimoxazole":      "cotrimoxazole (sulfaméthoxazole + triméthoprime)",
    "cotrimoxazol":       "cotrimoxazole (sulfaméthoxazole + triméthoprime)",
    "sulfamethoxazole":   "cotrimoxazole (sulfaméthoxazole + triméthoprime)",
    "trimethoprime":      "cotrimoxazole (sulfaméthoxazole + triméthoprime)",
    # amoxicilline + acide clavulanique
    "augmentin":          "amoxicilline + acide clavulanique",
    "augmentin 1g":       "amoxicilline + acide clavulanique",
    "augmentin 625":      "amoxicilline + acide clavulanique",
    "clavulin":           "amoxicilline + acide clavulanique",
    # losartan
    "coaprovel":          "losartan",
    "hyzaar":             "losartan",
    "fortzaar":           "losartan",
    # bisoprolol
    "lodoz":              "bisoprolol",
    "concor":             "bisoprolol",
    "emcor":              "bisoprolol",
    # amlodipine
    "amlor":              "amlodipine",
    "norvasc":            "amlodipine",
    # aténolol
    "tenormine":          "aténolol",
    # nébivolol
    "temerit":            "nébivolol",
    "nebilet":            "nébivolol",
    # nifédipine
    "adalate":            "nifédipine",
    "adalat":             "nifédipine",
    # périndopril
    "coversyl":           "périndopril",
    "aceon":              "périndopril",
}


# ── Chargement du dictionnaire ────────────────────────────────────────────────
def _load_dict() -> dict:
    if not DICT_PATH.exists():
        raise FileNotFoundError(
            f"dci_dict.json introuvable. Lancez d'abord :\n"
            f"  python src/build_dci_dict.py"
        )
    with open(DICT_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Normalisation de chaîne ───────────────────────────────────────────────────
def normalize_str(s: str) -> str:
    """Minuscules, sans accents, sans ponctuation superflue."""
    if not s:
        return ""
    s = str(s).strip()
    nfkd = unicodedata.normalize("NFKD", s)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    ascii_str = re.sub(r"[^a-z0-9\s\+]", " ", ascii_str.lower())
    return re.sub(r"\s+", " ", ascii_str).strip()


def _strip_dosage(s: str) -> str:
    """Supprime les dosages (500mg, 1g, 250 mg…) pour faciliter le matching."""
    return re.sub(r"\b\d+\s*(mg|g|ml|mcg|µg|ui|iu)\b", "", s, flags=re.IGNORECASE).strip()


# ── Similarité rapide : Levenshtein normalisé ─────────────────────────────────
try:
    from rapidfuzz.distance import Levenshtein
    from rapidfuzz import fuzz

    def _lev_ratio(a: str, b: str) -> float:
        return fuzz.ratio(a, b) / 100.0

except ImportError:
    # Fallback pur Python si rapidfuzz non installé
    def _levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return _levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                curr.append(min(prev[j + 1] + 1, curr[j] + 1,
                                prev[j] + (0 if c1 == c2 else 1)))
            prev = curr
        return prev[-1]

    def _lev_ratio(a: str, b: str) -> float:
        max_len = max(len(a), len(b), 1)
        return 1.0 - _levenshtein(a, b) / max_len


# ── Index plat pour la recherche ──────────────────────────────────────────────
def _build_index(dci_dict: dict) -> list[dict]:
    """
    Construit une liste plate de candidats :
    chaque entrée = (texte_normalized, dci_key, type, nom_original)
    """
    index = []
    for dci_key, entry in dci_dict.items():
        # DCI elle-même
        index.append({
            "normalized": entry["dci_normalized"],
            "original": entry["dci"],
            "dci_key": dci_key,
            "type": "DCI"
        })
        # Noms commerciaux (dédupliqués)
        seen = set()
        for gen in entry["generiques"]:
            nc = gen["nom_commercial"]
            nc_norm = gen["nom_normalized"]
            if nc_norm not in seen:
                seen.add(nc_norm)
                index.append({
                    "normalized": nc_norm,
                    "original": nc,
                    "dci_key": dci_key,
                    "type": "NOM_COMMERCIAL"
                })
                # Variante sans dosage
                stripped = normalize_str(_strip_dosage(nc))
                if stripped and stripped != nc_norm:
                    index.append({
                        "normalized": stripped,
                        "original": nc,
                        "dci_key": dci_key,
                        "type": "NOM_COMMERCIAL_SANS_DOSAGE"
                    })
    return index


# ── Fonction principale ───────────────────────────────────────────────────────
def normalize_query(query: str, dci_dict: dict = None, top_k: int = 3) -> dict:
    """
    Normalise une requête et retourne le meilleur match DCI.

    Retourne :
    {
        "query_original": "dolipranee",
        "query_normalized": "dolipranee",
        "found": True,
        "match_type": "NOM_COMMERCIAL",   # DCI | NOM_COMMERCIAL | FUZZY
        "dci": "paracétamol",
        "atc": "N02BE01",
        "classe": "Antalgiques et anti-inflammatoires",
        "noms_commerciaux": [...],
        "score": 0.94,
        "ambigu": False,
        "candidats": [...]   # top_k alternatives si ambigu
    }
    """
    if dci_dict is None:
        dci_dict = _load_dict()

    index = _build_index(dci_dict)
    q_norm = normalize_str(query)
    q_stripped = normalize_str(_strip_dosage(query))

    # ── 0. Alias manuel (noms commerciaux internationaux non présents dans l'Excel)
    if q_norm in MANUAL_ALIASES:
        dci_key = MANUAL_ALIASES[q_norm]
        if dci_key in dci_dict:
            entry = dci_dict[dci_key]
            return _build_result(query, q_norm, entry, dci_key,
                                 match_type="ALIAS_MANUEL", score=1.0,
                                 ambigu=False, candidats=[])
    # Essai avec version sans dosage
    if q_stripped in MANUAL_ALIASES:
        dci_key = MANUAL_ALIASES[q_stripped]
        if dci_key in dci_dict:
            entry = dci_dict[dci_key]
            return _build_result(query, q_norm, entry, dci_key,
                                 match_type="ALIAS_MANUEL", score=1.0,
                                 ambigu=False, candidats=[])

    # ── 1. Exact match (normalisé) ────────────────────────────────────────────
    exact_hits = [c for c in index if c["normalized"] == q_norm]
    if not exact_hits and q_stripped:
        exact_hits = [c for c in index if c["normalized"] == q_stripped]

    if exact_hits:
        # Dédupliquer par DCI
        dci_keys_hit = list(dict.fromkeys(h["dci_key"] for h in exact_hits))
        best_key = dci_keys_hit[0]
        entry = dci_dict[best_key]
        return _build_result(
            query, q_norm, entry, best_key,
            match_type=exact_hits[0]["type"],
            score=1.0,
            ambigu=(len(dci_keys_hit) > 1),
            candidats=[dci_dict[k] for k in dci_keys_hit[:top_k]]
        )

    # ── 2. Fuzzy match ────────────────────────────────────────────────────────
    scored = []
    for c in index:
        s = _lev_ratio(q_norm, c["normalized"])
        # Bonus si l'un commence par l'autre
        if c["normalized"].startswith(q_norm[:4]) or q_norm.startswith(c["normalized"][:4]):
            s = min(1.0, s + 0.08)
        scored.append((s, c))

    scored.sort(key=lambda x: -x[0])
    top = scored[:top_k]

    if not top or top[0][0] < 0.45:
        # Aucun résultat satisfaisant
        return {
            "query_original": query,
            "query_normalized": q_norm,
            "found": False,
            "match_type": None,
            "dci": None,
            "atc": None,
            "classe": None,
            "noms_commerciaux": [],
            "score": 0.0,
            "ambigu": False,
            "candidats": []
        }

    best_score, best_cand = top[0]
    best_key = best_cand["dci_key"]
    entry = dci_dict[best_key]

    # Ambiguïté : si 2ème candidat a un score très proche (< 0.05 d'écart) ET DCI différente
    second_different = [c for s, c in top[1:] if c["dci_key"] != best_key]
    ambigu = bool(second_different and (best_score - top[1][0]) < 0.05)

    candidats = []
    seen_dci = set()
    for s, c in top:
        if c["dci_key"] not in seen_dci:
            seen_dci.add(c["dci_key"])
            candidats.append(dci_dict[c["dci_key"]])

    return _build_result(
        query, q_norm, entry, best_key,
        match_type="FUZZY",
        score=round(best_score, 3),
        ambigu=ambigu,
        candidats=candidats
    )


def _build_result(query, q_norm, entry, dci_key, match_type, score, ambigu, candidats):
    return {
        "query_original": query,
        "query_normalized": q_norm,
        "found": True,
        "match_type": match_type,
        "dci": entry["dci"],
        "atc": entry["atc"],
        "classe": entry["classe"],
        "noms_commerciaux": entry["tous_noms_commerciaux"],
        "score": score,
        "ambigu": ambigu,
        "candidats": [
            {"dci": c["dci"], "atc": c["atc"]} for c in candidats
        ] if ambigu else []
    }


# ── Tableau d'évaluation (40 noms exigés par le CDC) ─────────────────────────
EVAL_QUERIES = [
    # (query_saisie, dci_attendue, description)
    # --- Noms commerciaux exacts ---
    ("DOLIPRANE",         "paracétamol",          "nom_commercial_exact"),
    ("AMOXIL",            "amoxicilline",          "nom_commercial_exact"),
    ("AUGMENTIN",         "amoxicilline + acide clavulanique", "nom_commercial_exact"),
    ("VOLTARENE",         "diclofénac",            "nom_commercial_exact"),
    ("BRUFEN",            "ibuprofène",            "nom_commercial_exact"),
    ("ZITHROMAX",         "azithromycine",         "nom_commercial_exact"),
    ("AMLOR",             "amlodipine",            "nom_commercial_exact"),
    ("TENORMINE",         "aténolol",              "nom_commercial_exact"),
    ("COAPROVEL",         "losartan",              "nom_commercial_approximate"),
    ("LODOZ",             "bisoprolol",            "nom_commercial_approximate"),

    # --- DCI exactes ---
    ("paracétamol",       "paracétamol",           "dci_exact"),
    ("amoxicilline",      "amoxicilline",          "dci_exact"),
    ("ibuprofen",         "ibuprofène",            "dci_exact_sans_accent"),
    ("ciprofloxacine",    "ciprofloxacine",        "dci_exact"),
    ("losartan",          "losartan",              "dci_exact"),
    ("metronidazole",     "métronidazole",         "dci_exact_sans_accent"),
    ("spironolactone",    "spironolactone",        "dci_exact"),
    ("tramadol",          "tramadol",              "dci_exact"),
    ("valsartan",         "valsartan",             "dci_exact"),
    ("ramipril",          "ramipril",              "dci_exact"),

    # --- Fautes de frappe ---
    ("paracetamoll",      "paracétamol",           "faute_frappe_doublée"),
    ("amoxiciline",       "amoxicilline",          "faute_frappe_simple"),
    ("dolipranee",        "paracétamol",           "faute_via_nom_commercial"),
    ("ibuprofene",        "ibuprofène",            "faute_accent"),
    ("atenolol",          "aténolol",              "faute_accent"),
    ("azythromycine",     "azithromycine",         "faute_frappe"),
    ("ciprofloxacin",     "ciprofloxacine",        "faute_finale_manquante"),
    ("metronidazol",      "métronidazole",         "faute_finale_manquante"),
    ("ceftriaxon",        "ceftriaxone",           "faute_finale_manquante"),
    ("bisoprololl",       "bisoprolol",            "faute_frappe_doublée"),

    # --- Avec dosage dans la requête ---
    ("paracetamol 500mg", "paracétamol",           "avec_dosage"),
    ("amoxicilline 500",  "amoxicilline",          "avec_dosage_partiel"),
    ("ibuprofen 400mg",   "ibuprofène",            "avec_dosage"),
    ("losartan 50",       "losartan",              "avec_dosage_partiel"),

    # --- Variantes casse ---
    ("PARACETAMOL",       "paracétamol",           "majuscules_sans_accent"),
    ("Amoxicilline",      "amoxicilline",          "casse_mixte"),
    ("VALSARTAN",         "valsartan",             "majuscules"),

    # --- Cas ambigus (à signaler) ---
    ("PARACETAMOL CODEINE", "paracétamol + codéine", "dci_combinee"),
    ("cotrimoxazole",     "cotrimoxazole (sulfaméthoxazole + triméthoprime)", "dci_longue"),
    ("acide acetylsalicylique", "ACIDE ACETYLSALICYLIQUE",                    "dci_majuscules"),
]


def run_evaluation(dci_dict: dict):
    """Génère le tableau d'évaluation CSV sur 40 noms."""
    EVAL_PATH.parent.mkdir(parents=True, exist_ok=True)

    results = []
    correct = 0
    found_total = 0
    ambigu_total = 0

    print(f"\n{'Requête':<30} {'DCI attendue':<42} {'DCI obtenue':<42} {'Score':>6} {'OK':>3} {'Ambigu':>7}")
    print("-" * 140)

    for query, expected_dci, desc in EVAL_QUERIES:
        res = normalize_query(query, dci_dict)
        obtained = res["dci"] or "—"
        score = res["score"]
        is_ok = (
            res["found"] and
            normalize_str(obtained) == normalize_str(expected_dci)
        )
        if res["found"]:
            found_total += 1
        if is_ok:
            correct += 1
        if res["ambigu"]:
            ambigu_total += 1

        flag = "✓" if is_ok else "✗"
        ambigu_flag = "⚠" if res["ambigu"] else ""

        print(f"{query:<30} {expected_dci:<42} {obtained:<42} {score:>6.3f} {flag:>3} {ambigu_flag:>7}")

        results.append({
            "query": query,
            "description": desc,
            "dci_attendue": expected_dci,
            "dci_obtenue": obtained,
            "match_type": res["match_type"] or "",
            "score": score,
            "correct": "oui" if is_ok else "non",
            "found": "oui" if res["found"] else "non",
            "ambigu": "oui" if res["ambigu"] else "non",
            "candidats": "; ".join(c["dci"] for c in res["candidats"]) if res["ambigu"] else ""
        })

    # Écriture CSV
    fieldnames = ["query", "description", "dci_attendue", "dci_obtenue",
                  "match_type", "score", "correct", "found", "ambigu", "candidats"]
    with open(EVAL_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    n = len(EVAL_QUERIES)
    print(f"\n{'─'*140}")
    print(f"Résultat : {correct}/{n} corrects ({100*correct/n:.1f}%) | "
          f"{found_total}/{n} trouvés | {ambigu_total} cas ambigus signalés")
    print(f"Tableau CSV → {EVAL_PATH}")
    return results


# ── Entrée CLI ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    dci_dict = _load_dict()

    if "--eval" in sys.argv:
        run_evaluation(dci_dict)
    elif len(sys.argv) > 1:
        query = " ".join(a for a in sys.argv[1:] if not a.startswith("--"))
        result = normalize_query(query, dci_dict)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage :")
        print("  python src/normalize_names.py \"dolipranee\"")
        print("  python src/normalize_names.py --eval")
