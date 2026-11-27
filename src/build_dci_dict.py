"""
build_dci_dict.py
-----------------
Lit data/reference/Liste 40 medicaments final.xlsx
et construit data/knowledge_graph/dci_dict.json

Structure de sortie :
{
  "paracétamol": {
    "dci": "paracétamol",
    "dci_normalized": "paracetamol",
    "numero": 1,
    "classe": "Antalgiques et anti-inflammatoires",
    "atc": "N02BE01",
    "atc_confirme": true,
    "dans_nomenclature_algerienne": true,
    "source_dictionnaire": "Liste_MIPH_2026",
    "generiques": [
      {
        "nom_commercial": "DOLIPRANE",
        "nom_normalized": "doliprane",
        "forme": "COMPRIME",
        "dosage": "500MG",
        "dans_nomenclature": true
      },
      ...
    ],
    "tous_noms_commerciaux": ["DOLIPRANE", "PARACETAL", ...]
  },
  ...
}
"""

import json
import re
import unicodedata
from pathlib import Path
import openpyxl

# ── Chemins ───────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = ROOT / "data" / "reference" / "Liste 40 medicaments final.xlsx"
OUT_DIR = ROOT / "data" / "knowledge_graph"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "dci_dict.json"


# ── Utilitaires ───────────────────────────────────────────────────────────────
def normalize_str(s: str) -> str:
    """Minuscules, sans accents, sans ponctuation superflue."""
    if not s:
        return ""
    s = str(s).strip()
    # Décomposer les caractères accentués et garder seulement ASCII
    nfkd = unicodedata.normalize("NFKD", s)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    # Minuscules + supprimer caractères non alphanumériques sauf espace et +
    ascii_str = re.sub(r"[^a-z0-9\s\+]", " ", ascii_str.lower())
    return re.sub(r"\s+", " ", ascii_str).strip()


def bool_oui(val) -> bool:
    if val is None:
        return False
    return str(val).strip().lower() in ("oui", "yes", "true", "1")


# ── Lecture Excel ──────────────────────────────────────────────────────────────
print(f"[build_dci_dict] Lecture de {EXCEL_PATH.name} ...")
wb = openpyxl.load_workbook(EXCEL_PATH)
ws = wb.active
rows = list(ws.iter_rows(values_only=True))
headers = rows[0]
data_rows = rows[1:]

# Colonnes :
# 0: N°  1: Classe  2: DCI  3: Code ATC  4: ATC confirmé
# 5: Présent nomenclature  6: N,C (nom commercial)  7: Forme  8: Dosage
# 9: Sources  10: Remarques

dci_dict = {}

for row in data_rows:
    numero       = row[0]
    classe       = str(row[1]).strip() if row[1] else ""
    dci_raw      = str(row[2]).strip() if row[2] else ""
    atc          = str(row[3]).strip() if row[3] else ""
    atc_ok       = bool_oui(row[4])
    nomencl_alg  = bool_oui(row[5])
    nom_comm     = str(row[6]).strip() if row[6] else ""
    forme        = str(row[7]).strip() if row[7] else ""
    dosage       = str(row[8]).strip() if row[8] else ""
    sources_raw  = str(row[9]).strip() if row[9] else ""
    remarques    = str(row[10]).strip() if row[10] else ""

    if not dci_raw:
        continue

    # Créer l'entrée DCI si elle n'existe pas encore
    if dci_raw not in dci_dict:
        dci_dict[dci_raw] = {
            "dci": dci_raw,
            "dci_normalized": normalize_str(dci_raw),
            "numero": numero,
            "classe": classe,
            "atc": atc,
            "atc_confirme": atc_ok,
            "dans_nomenclature_algerienne": nomencl_alg,
            "source_dictionnaire": "Liste_MIPH_2026",
            "generiques": [],
            "tous_noms_commerciaux": []
        }

    # Ajouter le générique s'il y a un nom commercial
    if nom_comm:
        entry = dci_dict[dci_raw]
        generique = {
            "nom_commercial": nom_comm,
            "nom_normalized": normalize_str(nom_comm),
            "forme": forme,
            "dosage": dosage,
            "dans_nomenclature": nomencl_alg,
            "sources": sources_raw,
            "remarques": remarques
        }
        entry["generiques"].append(generique)

        # Mettre à jour la liste dédupliquée des noms commerciaux
        if nom_comm not in entry["tous_noms_commerciaux"]:
            entry["tous_noms_commerciaux"].append(nom_comm)


# ── Sauvegarder ───────────────────────────────────────────────────────────────
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dci_dict, f, ensure_ascii=False, indent=2)

print(f"[build_dci_dict] ✓ {len(dci_dict)} DCI écrites dans {OUT_PATH}")
for dci, entry in sorted(dci_dict.items(), key=lambda x: x[1]["numero"]):
    nb_gen = len(entry["generiques"])
    nb_nc  = len(entry["tous_noms_commerciaux"])
    print(f"  [{entry['numero']:>2}] {dci:<45} → {nb_nc:>3} noms commerciaux, {nb_gen:>3} entrées")
