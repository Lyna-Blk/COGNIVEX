import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
excel_path = os.path.join(BASE_DIR, "Liste 40 medicaments.xlsx")
fiches_dir = os.path.join(BASE_DIR, "fiches_dci")

df = pd.read_excel(excel_path)
df.columns = [c.strip() for c in df.columns]

col_dci = 'DCI (nom de la substance)'
col_atc = 'Code ATC (indicatif)'
col_nc = 'N,C'
col_forme = 'Forme'
col_dosage = 'Dosage'
col_present = 'Présent dans la nomenclature algérienne ?'

for filename in os.listdir(fiches_dir):
    if not filename.endswith(".md"):
        continue

    dci_name = filename.replace(".md", "").strip().lower()
    df_filtered = df[df[col_dci].astype(str).str.strip().str.lower() == dci_name]

    if df_filtered.empty:
        print(f"DCI non trouvé: {dci_name}")
        continue

    commercial_lines = []
    seen = set()
    for _, row in df_filtered.iterrows():
        nc = str(row.get(col_nc, '')).strip()
        forme = str(row.get(col_forme, '')).strip()
        dosage = str(row.get(col_dosage, '')).strip()
        key = (nc, forme, dosage)
        if key not in seen and nc and nc.lower() != 'nan':
            seen.add(key)
            commercial_lines.append(f"  - {nc} — {forme} — {dosage}")

    commercial_block = "\n".join(commercial_lines) if commercial_lines else "  - Aucune spécialité listée"
    
    atc_val = str(df_filtered.iloc[0].get(col_atc, 'À vérifier')).strip()
    if atc_val.lower() == 'nan' or not atc_val:
        atc_val = 'À vérifier'
        
    presence_val = str(df_filtered.iloc[0].get(col_present, 'oui')).strip()

    nouveau_contenu = f"""# DCI : {dci_name.upper()}

- **Code ATC :** {atc_val}

- Présence dans la nomenclature MIPH : {presence_val}

- Version consultée et date : Nomenclature MIPH (août 2026)

- Noms commerciaux, laboratoires, formes et dosages :
{commercial_block}


## Documents de référence
- RCP : [produit, source/pays, date, nom du fichier]

- Notice : [produit, source/pays, date, nom du fichier]


## Recherche ANPP
- Requêtes en majuscules : {dci_name.upper()}

- Méthode et date : [...]

- Résultat : [RCP trouvé / « document ANPP non trouvé »]


## Sources consultées
Au moins 3 sources distinctes, dont au moins une officielle.
- [Source — information utilisée — pays — lien — date]

- [Source — information utilisée — pays — lien — date]

- [Source — information utilisée — pays — lien — date]


## Précision
- Une source étrangère complète la source algérienne et ne la remplace pas.

- En cas de différence, la source algérienne prévaut : [...]
"""

    file_path = os.path.join(fiches_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(nouveau_contenu)

    print(f"Mis à jour avec succès: {filename} (ATC: {atc_val})")