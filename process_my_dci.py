"""
process_my_dci.py
-----------------
Convertit les 8 DCI "antibiotiques" (dossier PHARMEAZOR_MY_8_DCI) vers le MEME
format que celui utilise pour les 8 DCI antihypertenseurs :

    data/fiches_dci/<dci>.md                      (fiche au format du modele)
    data/corpus/<dci>/<dci>_RCP_<SOURCE>.pdf      (RCP de reference)
    data/corpus/<dci>/<dci>_Notice_<SOURCE>.pdf   (notice de reference)
    data/documents_complementaires_non_reference/<dci>/...   (articles, fiches produit, notes)
    data/processed/produits_details.json          (labo, n° d'enregistrement, ... par produit)
    data/processed/corpus_metadata.json           (regenere par generate_corpus_metadata.py)
    data/processed/rapport_qualite_8_dci.md       (controles qualite)

Usage (depuis la racine du depot) :
    python process_my_dci.py --src "chemin/vers/PHARMEAZOR_MY_8_DCI"

Le script est rejouable : il ecrase ses propres sorties sans creer de doublons.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FICHES_DIR = DATA / "fiches_dci"
CORPUS_DIR = DATA / "corpus"
COMPL_DIR = DATA / "documents_complementaires_non_reference"  # ignore par generate_corpus_metadata.py
PROCESSED = DATA / "processed"
EXCEL = DATA / "liste_40_medicament_complete.xlsx"

COLLECT_DATE_FALLBACK = "18/11/2026"
NOMENCLATURE_VERSION = "Nomenclature MIPH (août 2026)"

# N° dans "Liste 40 medicaments.xlsx" -> nom de fiche (minuscule, accentue, comme les fiches du groupe)
MY_DCIS = {
    17: "ceftriaxone",
    18: "azithromycine",
    19: "clarithromycine",
    20: "ciprofloxacine",
    21: "lévofloxacine",
    22: "doxycycline",
    23: "cotrimoxazole",
    24: "métronidazole",
}

COL_N = "N°"
COL_DCI = "DCI (nom de la substance)"
COL_ATC = "Code ATC (indicatif)"
COL_NC = "N,C"
COL_FORME = "Forme"
COL_DOSAGE = "Dosage"
COL_PRESENT = "Présent dans la nomenclature algérienne ?"


# --------------------------------------------------------------------------- utils
def decode_mangled(name):
    """'L#U00c9VOFLOXACINE' -> 'LÉVOFLOXACINE' (nom abime par certains dezippeurs)."""
    return re.sub(r"#U([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), name)


def normalize(value):
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", decode_mangled(str(value)))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def strengths(text):
    """Ensemble des dosages (en mg) cites dans un libelle de produit."""
    return {int(x) for x in re.findall(r"(\d+)\s*mg", str(text).replace(" ", " ").lower())}


def pdf_first_page_text(pdf):
    try:
        return subprocess.run(
            ["pdftotext", "-l", "1", str(pdf), "-"],
            capture_output=True, text=True, timeout=60,
        ).stdout
    except Exception:
        return ""


def pdf_info(pdf):
    """(nb_pages, a_une_couche_texte)"""
    pages, has_text = None, False
    try:
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, timeout=60).stdout
        m = re.search(r"Pages:\s+(\d+)", out)
        pages = int(m.group(1)) if m else None
        fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True, timeout=60).stdout
        has_text = len(fonts.strip().splitlines()) > 2
    except Exception:
        pass
    return pages, has_text


# --------------------------------------------------------------------------- PDF identification
def identify_pdf(pdf):
    """Detecte source (eMC / ANSM), pays, produit et date de collecte a partir de la 1re page."""
    txt = pdf_first_page_text(pdf)
    info = {"source": "INCONNUE", "pays": "?", "produit": "inconnu", "date": COLLECT_DATE_FALLBACK,
            "organisme": "Source non identifiee", "lien": ""}

    m = re.search(r"^(\d{2})/(\d{2})/(\d{2}),", txt, flags=re.MULTILINE)  # entete impression navigateur (mm/dd/yy)
    if m:
        info["date"] = f"{m.group(2)}/{m.group(1)}/20{m.group(3)}"

    if "(emc)" in txt.lower() or "medicines.org.uk" in txt.lower():
        info.update(source="EMC", pays="Royaume-Uni",
                    organisme="eMC — Electronic Medicines Compendium (MHRA)")
        t = re.search(r"^(.+?)\s+-\s+(?:Summary of Product Characteristics|Patient Information Leaflet)",
                      txt, flags=re.MULTILINE)
        if t:
            info["produit"] = t.group(1).strip()
        pid = re.search(r"\(emc\)\s*\|\s*(\d+)", txt)
        if pid:
            info["lien"] = f"https://www.medicines.org.uk/emc/product/{pid.group(1)}/" + (
                "smpc" if "RCP" in pdf.name.upper() else "pil")
    elif "mhra.gov.uk" in txt.lower() or "package leaflet" in txt.lower():
        # notice patient britannique (PIL) telechargee en PDF, sans entete de navigateur
        info.update(source="EMC", pays="Royaume-Uni",
                    organisme="eMC — Electronic Medicines Compendium (MHRA)",
                    lien="https://www.medicines.org.uk/emc")
        head = [l.strip() for l in txt.splitlines() if l.strip()][:12]
        t = [l for l in head if re.search(r"\d\s*mg", l)]
        if t:  # une notice couvre souvent plusieurs dosages (250 / 500 / 750 mg)
            info["produit"] = " ; ".join(t)
        rev = re.search(r"last revised in (\d{2}/\d{4})", txt)
        if rev:
            info["revision"] = rev.group(1)
    elif "base de donn" in txt.lower() and "m\u00e9dicaments" in txt.lower():
        info.update(source="ANSM", pays="France",
                    organisme="ANSM — Base de données publique des médicaments",
                    lien="https://base-donnees-publique.medicaments.gouv.fr")
        t = re.search(r"(?:Notice patient|R[ée]sum[ée] des caract[ée]ristiques du produit)\s+-\s+(.+?)\s+-\s+Base de donn",
                      txt)
        if t:
            info["produit"] = t.group(1).strip()
        else:  # ex. RCP DOXYCYCLINE : le titre suit "Dernière mise à jour le ..."
            t2 = re.search(r"Derni[èe]re mise à jour le [^\n]+\n+([^\n]+)", txt)
            if t2:
                info["produit"] = t2.group(1).strip()
    return info


# --------------------------------------------------------------------------- lecture des dossiers sources
def find_dci_folders(src):
    """Retourne {nom_fiche: dossier_source} en comparant les noms normalises."""
    # le zip contient parfois un niveau de dossier en double
    candidates = [p for p in src.rglob("*") if p.is_dir() and (p / "Produit").is_dir()]
    out = {}
    for c in candidates:
        n = normalize(c.name)
        for dci in MY_DCIS.values():
            if normalize(dci) == n:
                out[dci] = c
    return out


def parse_product_file(path):
    """Extrait les champs cle : valeur d'une fiche produit (formats heterogenes)."""
    txt = read_text(path)
    fields = {}
    for line in txt.splitlines():
        m = re.match(r"^\s*(?:[-*]\s*)?\**\s*([^:*\n]{2,60}?)\s*\**\s*:\s*\**\s*(.+?)\s*\**\s*$", line)
        if m:
            key = normalize(m.group(1))
            if key not in fields:
                fields[key] = m.group(2).strip()

    def pick(*prefixes):
        for p in prefixes:
            for k, v in fields.items():
                if k.startswith(p):
                    return v or None
        return None

    for k, v in list(fields.items()):
        if normalize(v).startswith(("a confirmer", "non confirme", "non verifie")):
            fields[k] = ""
    title = re.search(r"^#\s*(.+)$", txt, flags=re.MULTILINE)
    return {
        "fichier": Path(path).name,
        "titre": title.group(1).strip() if title else None,
        "nom_commercial": pick("nom commercial"),
        "dci": pick("dci"),
        "dosage": pick("dosage"),
        "forme": pick("forme pharmaceutique"),
        "conditionnement": pick("conditionnement"),
        "laboratoire": pick("laboratoire titulaire", "laboratoire", "fabricant"),
        "pays": pick("pays"),
        "code_dci": pick("code dci"),
        "numero_enregistrement": pick("numero d enregistrement"),
        "date_enregistrement_initial": pick("date d enregistrement initial"),
        "date_enregistrement_final": pick("date d enregistrement final", "dernier renouvellement"),
    }


def mentions(text, *needles):
    n = normalize(text)
    return any(normalize(x) in n for x in needles)


# --------------------------------------------------------------------------- generation des fiches
def excel_rows(df, n):
    return df[df[COL_N] == n]


def build_fiche(dci, rows, docs, src_text, article_found):
    atc = str(rows.iloc[0].get(COL_ATC, "")).strip()
    atc = "À vérifier" if atc.lower() in ("", "nan") else atc
    present = str(rows.iloc[0].get(COL_PRESENT, "")).strip() or "oui"

    lines, seen = [], set()
    for _, r in rows.iterrows():
        nc, forme, dosage = (str(r.get(c, "")).strip() for c in (COL_NC, COL_FORME, COL_DOSAGE))
        key = (nc, forme, dosage)
        if nc and nc.lower() != "nan" and key not in seen:
            seen.add(key)
            lines.append(f"  - {nc} — {forme} — {dosage}")
    commercial = "\n".join(lines) if lines else "  - Aucune spécialité listée"

    rcp, notice = docs.get("RCP"), docs.get("Notice")
    fname = lambda d, kind: f"{dci}_{kind}_{d['source']}.pdf"
    rcp_line = (f"- RCP : {rcp['produit']} ({rcp['organisme']}), {rcp['pays']}, collecté le {rcp['date']}, "
                f"`{fname(rcp, 'RCP')}`") if rcp else "- RCP : Aucun document disponible / non trouvé"
    notice_line = (f"- Notice : {notice['produit']} ({notice['organisme']}), {notice['pays']}, "
                   f"collectée le {notice['date']}, `{fname(notice, 'Notice')}`") if notice \
        else "- Notice : Aucun document disponible / non trouvé"

    d_ref = (rcp or notice or {}).get("date", COLLECT_DATE_FALLBACK)

    sources = [
        f"- MIPH (Ministère de l'Industrie Pharmaceutique) — Nomenclature nationale des produits pharmaceutiques "
        f"(noms commerciaux, formes, dosages, codes DCI) — Algérie — "
        f"https://www.miph.gov.dz/fr/nomenclature-nationale-des-produits-pharmaceutiques/ — {d_ref}",
        f"- ANPP (Agence Nationale des Produits Pharmaceutiques) — Recherche de RCP algérien par DCI et par nom commercial — "
        f"Algérie — https://rcp.anpp.dz — {d_ref}",
    ]
    if mentions(src_text, "joradp", "journal officiel"):
        sources.append("- Journal officiel de la République algérienne n° 75 du 13/11/2025 — Codes DCI, formes et dosages "
                       "enregistrés — Algérie — https://www.joradp.dz/FTP/jo-francais/2025/F2025075.pdf — "
                       f"{d_ref}")
    for kind, d in (("RCP", rcp), ("Notice", notice)):
        if d:
            sources.append(f"- {d['organisme']} — {kind} de référence ({d['produit']}) — {d['pays']} — "
                           f"{d['lien'] or 'lien à compléter'} — {d['date']}")
    if mentions(src_text, "atcddd"):
        sources.append("- WHO Collaborating Centre for Drug Statistics Methodology — Vérification du code ATC "
                       f"({atc}) — International — https://atcddd.fhi.no/atc_ddd_index/?code={atc} — {d_ref}")
    if len(sources) < 3:
        sources.append("- [Source à compléter]")

    # Le resultat ANPP n'est affirme que si les notes sources le documentent (jamais par defaut).
    s = normalize(src_text)
    anpp_negative = any(k in s for k in ("aucun resultat", "en l absence d un rcp algerien", "aucun rcp algerien"))
    if anpp_negative:
        anpp_result = "document ANPP non trouvé"
        anpp_method = (f"Recherche par DCI et par nom commercial sur le portail ANPP (rcp.anpp.dz) et consultation de la "
                       f"nomenclature MIPH, le {d_ref}.")
    else:
        anpp_result = "non vérifié — recherche ANPP à effectuer et à consigner (rcp.anpp.dz)"
        anpp_method = "Aucune recherche ANPP documentée dans les notes sources."
    precision = [
        "- Une source étrangère complète la source algérienne et ne la remplace pas.",
    ]
    if rcp or notice:
        used = " / ".join(sorted({d["organisme"] for d in (rcp, notice) if d}))
        prod = (rcp or notice)["produit"]
        precision.append(
            f"- En cas de différence, la source algérienne prévaut : aucun RCP algérien (ANPP) n'a pu être récupéré ; "
            f"le RCP/notice de {prod} ({used}) sert de référence documentaire étrangère complémentaire. "
            f"Les spécialités et dosages commercialisés en Algérie proviennent de la nomenclature MIPH.")
    else:
        precision.append("- Aucun document officiel (RCP ou notice) n'a été retrouvé.")

    return f"""# DCI : {dci.upper()}

- **Code ATC :** {atc}

- Présence dans la nomenclature MIPH : {present}

- Version consultée et date : {NOMENCLATURE_VERSION}

- Noms commerciaux, laboratoires, formes et dosages :
{commercial}


## Documents de référence
{rcp_line}

{notice_line}

## Recherche ANPP
- Requêtes en majuscules : {dci.upper()}

- Méthode et date : {anpp_method}

- Résultat : {anpp_result}


## Sources consultées
Au moins 3 sources distinctes, dont au moins une officielle.
""" + "\n\n".join(sources) + "\n\n\n## Précision\n" + "\n\n".join(precision) + "\n"


# --------------------------------------------------------------------------- patch de generate_corpus_metadata.py
def ensure_source_levels_patch():
    """eMC (UK) et Journal officiel n'etaient pas reconnus dans SOURCE_LEVELS -> authority_level = 0."""
    path = ROOT / "generate_corpus_metadata.py"
    code = path.read_text(encoding="utf-8")
    if "electronic medicines compendium" in code:
        return False
    code = code.replace(
        '"dailymed": 3,',
        '"dailymed": 3,\n    "electronic medicines compendium": 3,\n    "journal officiel": 3,',
    )
    path.write_text(code, encoding="utf-8")
    return True


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="dossier PHARMEAZOR_MY_8_DCI (dezippe)")
    args = ap.parse_args()
    src = Path(args.src)

    df = pd.read_excel(EXCEL)
    df.columns = [c.strip() for c in df.columns]

    folders = find_dci_folders(src)
    missing = [d for d in MY_DCIS.values() if d not in folders]
    if missing:
        sys.exit(f"Dossiers introuvables pour : {missing}")

    for d in (FICHES_DIR, CORPUS_DIR, COMPL_DIR, PROCESSED):
        d.mkdir(parents=True, exist_ok=True)

    qa = defaultdict(list)          # dci -> messages
    all_products = []
    article_hashes = defaultdict(list)

    for n, dci in MY_DCIS.items():
        folder = folders[dci]
        rows = excel_rows(df, n)
        if rows.empty:
            qa[dci].append(f"ERREUR : N°{n} absent du fichier Excel")
            continue

        # ---- 1. PDF -> corpus
        docs = {}
        out_corpus = CORPUS_DIR / dci
        if out_corpus.exists():
            shutil.rmtree(out_corpus)
        out_corpus.mkdir(parents=True)
        for pdf in sorted((folder / "RCP_et_notice").glob("*.pdf")):
            kind = "RCP" if pdf.name.upper().startswith("RCP") else "Notice"
            meta = identify_pdf(pdf)
            pages, has_text = pdf_info(pdf)
            meta.update(pages=pages, has_text=has_text)
            docs[kind] = meta
            shutil.copy2(pdf, out_corpus / f"{dci}_{kind}_{meta['source']}.pdf")
            if meta["source"] == "INCONNUE":
                qa[dci].append(f"{kind} : source non identifiee automatiquement ({pdf.name})")
            if not has_text:
                qa[dci].append(f"{kind} : PDF sans couche texte -> OCR necessaire ({pdf.name})")
        if "RCP" in docs and "Notice" in docs:
            r, nt = docs["RCP"], docs["Notice"]
            sr, sn = strengths(r["produit"]), strengths(nt["produit"])
            if sr and sn and not (sr <= sn or sn <= sr):
                qa[dci].append(f"RCP et Notice : dosages differents (RCP = « {r['produit']} » / Notice = « {nt['produit']} »)")
            elif normalize(r["produit"]) != normalize(nt["produit"]) and not (r["source"] == nt["source"] == "EMC"):
                qa[dci].append(f"INFO : RCP = « {r['produit']} » et Notice = « {nt['produit']} » sont deux "
                               f"specialites differentes (meme DCI/dosage) : acceptable mais a signaler")
        for kind in ("RCP", "Notice"):
            if kind not in docs:
                qa[dci].append(f"{kind} manquant")

        # ---- 2. produits
        for pf in sorted((folder / "Produit").glob("*.txt")):
            if pf.stat().st_size == 0:
                qa[dci].append(f"Fiche produit VIDE : {pf.name} (a remplir)")
                continue
            rec = parse_product_file(pf)
            rec["dci_fiche"] = dci
            all_products.append(rec)
            if not rec["laboratoire"]:
                qa[dci].append(f"Fiche produit sans laboratoire : {pf.name}")
            if not rec["numero_enregistrement"]:
                qa[dci].append(f"Fiche produit sans n° d'enregistrement : {pf.name}")

        # ---- 3. documents complementaires (non reference)
        out_c = COMPL_DIR / dci
        if out_c.exists():
            shutil.rmtree(out_c)
        out_c.mkdir(parents=True)
        src_text = ""
        for f in folder.glob("*.txt"):
            shutil.copy2(f, out_c / f.name)
            src_text += read_text(f) + "\n"
            if f.stat().st_size == 0:
                qa[dci].append(f"Fichier VIDE : {f.name}")
        art = next((folder / "ARTICLE").glob("*.txt"), None)
        article_found = bool(art and art.stat().st_size > 0)
        if art:
            shutil.copy2(art, out_c / art.name)
            if art.stat().st_size == 0:
                qa[dci].append("ARTICLE_SCIENTIFIQUE.txt VIDE")
            else:
                article_hashes[hashlib.md5(art.read_bytes()).hexdigest()].append(dci)
        prod_out = out_c / "Produit"
        prod_out.mkdir()
        for pf in (folder / "Produit").glob("*.txt"):
            if pf.stat().st_size:
                shutil.copy2(pf, prod_out / pf.name)

        # ---- 4. fiche
        fiche = build_fiche(dci, rows, docs, src_text, article_found)
        (FICHES_DIR / f"{dci}.md").write_text(fiche, encoding="utf-8")
        nb_src = len(re.findall(r"^- (?!\[)", fiche.split("## Sources consultées")[1].split("## Précision")[0],
                                flags=re.MULTILINE))
        if nb_src < 3:
            qa[dci].append("Moins de 3 sources consultees dans la fiche")
        print(f"[OK] {dci:<16} ATC={rows.iloc[0][COL_ATC]}  produits Excel={rows[COL_NC].nunique():>2}  "
              f"RCP={docs.get('RCP', {}).get('source', '-')}  Notice={docs.get('Notice', {}).get('source', '-')}")

    for h, names in article_hashes.items():
        if len(names) > 1:
            for dci in names:
                qa[dci].append("ARTICLE_SCIENTIFIQUE identique a celui de : " + ", ".join(x for x in names if x != dci)
                               + " (copier-coller -> a remplacer par des articles propres a cette DCI)")

    # ---- 5. details produits
    (PROCESSED / "produits_details.json").write_text(
        json.dumps(all_products, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- 6. regeneration du JSON global
    patched = ensure_source_levels_patch()
    subprocess.run([sys.executable, str(ROOT / "generate_corpus_metadata.py")], check=True)

    # ---- 7. rapport qualite
    report = ["# Rapport qualité — 8 DCI antibiotiques", ""]
    meta = json.loads((PROCESSED / "corpus_metadata.json").read_text(encoding="utf-8"))
    by_dci = {m["dci"].casefold(): m for m in meta}
    report.append("| DCI | Produits (fiche) | Produits liés à un PDF | authority_level | Alertes |")
    report.append("|---|---|---|---|---|")
    for n, dci in MY_DCIS.items():
        m = by_dci.get(dci.upper().casefold())
        if not m:
            report.append(f"| {dci} | ? | ? | ? | absente du JSON |")
            continue
        linked = sum(1 for p in m["produits"] if p.get("file_paths"))
        report.append(f"| {dci} | {len(m['produits'])} | {linked} | {m['authority_level']} | {len(qa[dci])} |")
    report.append("")
    for dci in MY_DCIS.values():
        if qa[dci]:
            report.append(f"## {dci}")
            report += [f"- {x}" for x in qa[dci]]
            report.append("")
    (PROCESSED / "rapport_qualite_8_dci.md").write_text("\n".join(report), encoding="utf-8")
    print(f"\nPatch SOURCE_LEVELS applique : {patched}")
    print(f"Rapport : {PROCESSED / 'rapport_qualite_8_dci.md'}")


if __name__ == "__main__":
    main()
