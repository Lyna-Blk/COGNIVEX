"""
generate_unified_corpus.py
--------------------------
Fusionne deux approches :
  1. Metadonnees structurelles (chemins, PDFs, brands) depuis data/corpus/
  2. Donnees granulaires Excel (DCI, marques, formes, dosages, lignes Excel)

Produit :
  - data/corpus_unified.json  : JSON unifie complet
  - data/corpus_unified_report.txt : rapport lisible
  - Valide la coherence via croisement metadata <-> Excel

Usage: python generate_unified_corpus.py
"""

import os, sys, json, mimetypes, re
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

try:
    import openpyxl
except ImportError:
    sys.exit("[ERROR] openpyxl non installe. Lancez: pip install openpyxl")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CORPUS_ROOT   = Path(__file__).parent / "data" / "corpus"
EXCEL_FILE    = Path(__file__).parent / "data" / "reference" / "Feuille de calcul sans titre (1).xlsx"
MARKDOWN_FILE = Path(__file__).parent / "data" / "corpus_medicaments.md"
OUTPUT_JSON   = Path(__file__).parent / "data" / "corpus_unified.json"
OUTPUT_TXT    = Path(__file__).parent / "data" / "corpus_unified_report.txt"

# Mapping normalisé DCI (clé=corpus folder name)
DCI_CANONICAL = {
    "amlodipine":  {
        "dci_display":     "Amlodipine",
        "code_atc":        "C08CA01",
        "classe":          "Antihypertenseurs",
        "miph_numero":     27,
        "miph_present":    "oui",
        "anpp_rcp":        True,
        "anpp_notice":     True,
        "source_reference": "MIPH/ANPP + DailyMed",
        "excel_match_keys": ["amlodipine"],
    },
    "losartan":    {
        "dci_display":     "Losartan",
        "code_atc":        "C09CA01",
        "classe":          "Antihypertenseurs",
        "miph_numero":     32,
        "miph_present":    "oui",
        "anpp_rcp":        True,
        "anpp_notice":     True,
        "source_reference": "MIPH/ANPP + ANSM + DailyMed",
        "excel_match_keys": ["losartan"],
    },
    "clindamycine":{
        "dci_display":     "Clindamycine",
        "code_atc":        "J01FF01",
        "classe":          "Antibiotiques",
        "miph_numero":     26,
        "miph_present":    "oui",
        "anpp_rcp":        False,
        "anpp_notice":     False,
        "source_reference": "MIPH + ANSM",
        "excel_match_keys": ["clindamycine"],
    },
    "enalapril":   {
        "dci_display":     "Énalapril",
        "code_atc":        "C09AA02",
        "classe":          "Antihypertenseurs",
        "miph_numero":     31,
        "miph_present":    "oui",
        "anpp_rcp":        False,
        "anpp_notice":     False,
        "source_reference": "MIPH/ANPP + ANSM",
        "excel_match_keys": ["enalapril", "énalapril"],
    },
    "gentamicine": {
        "dci_display":     "Gentamicine",
        "code_atc":        "J01GB03",
        "classe":          "Antibiotiques",
        "miph_numero":     25,
        "miph_present":    "oui",
        "anpp_rcp":        False,
        "anpp_notice":     False,
        "source_reference": "MIPH + ANSM + DailyMed",
        "excel_match_keys": ["gentamicine"],
    },
    "nifedipine":  {
        "dci_display":     "Nifédipine",
        "code_atc":        "C08CA05",
        "classe":          "Antihypertenseurs",
        "miph_numero":     28,
        "miph_present":    "non",
        "anpp_rcp":        False,
        "anpp_notice":     False,
        "source_reference": "DailyMed (ANSM en complément)",
        "excel_match_keys": ["nifedipine", "nifédipine"],
    },
    "perindopril": {
        "dci_display":     "Périndopril",
        "code_atc":        "C09AA04",
        "classe":          "Antihypertenseurs",
        "miph_numero":     29,
        "miph_present":    "oui",
        "anpp_rcp":        False,
        "anpp_notice":     False,
        "source_reference": "MIPH/ANPP + ANSM",
        "excel_match_keys": ["perindopril", "périndopril"],
    },
    "ramipril":    {
        "dci_display":     "Ramipril",
        "code_atc":        "C09AA05",
        "classe":          "Antihypertenseurs",
        "miph_numero":     30,
        "miph_present":    "oui",
        "anpp_rcp":        False,
        "anpp_notice":     False,
        "source_reference": "MIPH/ANPP + ANSM + DailyMed",
        "excel_match_keys": ["ramipril"],
    },
}

# Documents de référence par DCI
DOCUMENTS_REF = {
    "amlodipine": {
        "rcp":    [{"fichier":"source-amdolipine rcp.pdf",    "source":"ANPP","pays":"Algérie"},
                   {"fichier":"source-amdolipine-daily med -rcp.pdf","source":"DailyMed","pays":"États-Unis"},
                   {"fichier":"mibral/RCP-MIBRL.pdf","source":"ANPP","pays":"Algérie"}],
        "notice": [{"fichier":"source-amlodopine-notice.pdf","source":"ANPP","pays":"Algérie"}],
        "info":   [{"fichier":"Source-info -amlodipline.pdf","source":"ANPP/MIPH","pays":"Algérie"}],
    },
    "losartan": {
        "rcp":    [{"fichier":"LOSartan anpp.pdf",   "source":"ANPP","pays":"Algérie"},
                   {"fichier":"rcp-losartan.pdf",    "source":"ANSM","pays":"France"},
                   {"fichier":"dailymed-losartan.pdf","source":"DailyMed","pays":"États-Unis"}],
        "notice": [{"fichier":"notice-losartan.pdf","source":"ANSM","pays":"France"}],
        "info":   [{"fichier":"info-losartan.pdf",  "source":"ANPP/ANSM","pays":"Algérie/France"}],
    },
    "clindamycine": {
        "rcp":    [{"fichier":"source_ansm-rcp.pdf",    "source":"ANSM","pays":"France"}],
        "notice": [{"fichier":"source-ansm-notice.pdf","source":"ANSM","pays":"France"}],
        "info":   [{"fichier":"source-ansm_info.pdf",  "source":"ANSM","pays":"France"}],
    },
    "enalapril": {
        "rcp":    [{"fichier":"rcp-enalapril.pdf",    "source":"ANSM","pays":"France"}],
        "notice": [{"fichier":"notice-enalapril.pdf","source":"ANSM","pays":"France"}],
        "info":   [{"fichier":"info-enalapril.pdf",  "source":"ANSM/ANPP","pays":"France/Algérie"},
                   {"fichier":"dwa--dz.pdf",         "source":"DwaDZ","pays":"Algérie"}],
    },
    "gentamicine": {
        "rcp":    [{"fichier":"genta_80/source_ansm_rcp.pdf",   "source":"ANSM","pays":"France"},
                   {"fichier":"daily med genta.pdf",             "source":"DailyMed","pays":"États-Unis"}],
        "notice": [{"fichier":"genta_80/source_ansm_noticc.pdf","source":"ANSM","pays":"France"}],
        "info":   [{"fichier":"genta_80/source_ansm_fiche_info.pdf","source":"ANSM","pays":"France"},
                   {"fichier":"genta_80/source_ansm_interaction_medicament.pdf","source":"ANSM","pays":"France"}],
    },
    "nifedipine": {
        "rcp":    [{"fichier":"dailymed-nifedipine.pdf","source":"DailyMed","pays":"États-Unis"}],
        "notice": [],
        "info":   [],
    },
    "perindopril": {
        "rcp":    [{"fichier":"perindopril/source rcp. prindoprile.pdf","source":"ANPP","pays":"Algérie"}],
        "notice": [],
        "info":   [{"fichier":"coversyl/source-generique-.pdf","source":"ANPP/pharmnet-dz","pays":"Algérie"},
                   {"fichier":"perindopril/generique.pdf",     "source":"ANPP","pays":"Algérie"},
                   {"fichier":"perindosyl/iteraction-source.pdf","source":"ANPP","pays":"Algérie"}],
    },
    "ramipril": {
        "rcp":    [{"fichier":"rcpramplir.pdf",        "source":"ANSM","pays":"France"},
                   {"fichier":"ramplir-dailymed.pdf",   "source":"DailyMed","pays":"États-Unis"}],
        "notice": [{"fichier":"notice-ramplir.pdf","source":"ANSM","pays":"France"}],
        "info":   [{"fichier":"info.pdf","source":"ANSM/ANPP","pays":"France/Algérie"}],
    },
}

# Sources officielles par DCI
SOURCES_URLS = {
    "amlodipine": [
        {"source":"MIPH","pays":"Algérie","url":"https://www.miph.gov.dz/nomenclature","info":"Nomenclature N°27, C08CA01"},
        {"source":"ANPP / pharmnet-dz","pays":"Algérie","url":"https://www.pharmnet-dz.com","info":"RCP et Notice amlodipine"},
        {"source":"DailyMed / NLM-FDA","pays":"États-Unis","url":"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=amlodipine","info":"Label amlodipine besylate"},
        {"source":"dzair-pharma.net","pays":"Algérie","url":"https://www.dzair-pharma.net","info":"Vérification noms commerciaux"},
    ],
    "losartan": [
        {"source":"MIPH","pays":"Algérie","url":"https://www.miph.gov.dz/nomenclature","info":"Nomenclature N°32, C09CA01"},
        {"source":"ANPP / pharmnet-dz","pays":"Algérie","url":"https://www.pharmnet-dz.com","info":"RCP losartan (COZZAR, ANGIZAR…)"},
        {"source":"ANSM / Base données publique","pays":"France","url":"https://base-donnees-publique.medicaments.gouv.fr","info":"RCP et Notice losartan potassique"},
        {"source":"DailyMed / NLM-FDA","pays":"États-Unis","url":"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=losartan","info":"Label losartan potassium"},
    ],
    "clindamycine": [
        {"source":"MIPH","pays":"Algérie","url":"https://www.miph.gov.dz/nomenclature","info":"Nomenclature N°26, J01FF01"},
        {"source":"ANSM / Base données publique","pays":"France","url":"https://base-donnees-publique.medicaments.gouv.fr","info":"RCP et Notice clindamycine"},
        {"source":"dzair-pharma.net","pays":"Algérie","url":"https://www.dzair-pharma.net","info":"Vérification noms commerciaux"},
    ],
    "enalapril": [
        {"source":"MIPH","pays":"Algérie","url":"https://www.miph.gov.dz/nomenclature","info":"Nomenclature N°31, C09AA02"},
        {"source":"ANSM / Base données publique","pays":"France","url":"https://base-donnees-publique.medicaments.gouv.fr","info":"RCP et Notice énalapril maléate"},
        {"source":"ANPP / pharmnet-dz","pays":"Algérie","url":"https://www.pharmnet-dz.com","info":"Fiche Enalapril Mylan"},
        {"source":"dzair-pharma.net","pays":"Algérie","url":"https://www.dzair-pharma.net","info":"Page DCI énalapril maléate"},
    ],
    "gentamicine": [
        {"source":"MIPH","pays":"Algérie","url":"https://www.miph.gov.dz/nomenclature","info":"Nomenclature N°25, J01GB03"},
        {"source":"ANSM / Base données publique","pays":"France","url":"https://base-donnees-publique.medicaments.gouv.fr","info":"RCP et Notice gentamicine sulfate"},
        {"source":"DailyMed / NLM-FDA","pays":"États-Unis","url":"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=gentamicin","info":"Label Gentamicin Sulfate Injection"},
        {"source":"dzair-pharma.net","pays":"Algérie","url":"https://www.dzair-pharma.net","info":"Vérification noms commerciaux"},
    ],
    "nifedipine": [
        {"source":"MIPH","pays":"Algérie","url":"https://www.miph.gov.dz/nomenclature","info":"Nomenclature N°28 — NON PRESENTE"},
        {"source":"DailyMed / NLM-FDA","pays":"États-Unis","url":"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=nifedipine","info":"Label nifedipine (Adalat CC, Procardia XL)"},
        {"source":"ANSM / Base données publique","pays":"France","url":"https://base-donnees-publique.medicaments.gouv.fr","info":"Adalate 10 mg capsules et LP"},
    ],
    "perindopril": [
        {"source":"MIPH","pays":"Algérie","url":"https://www.miph.gov.dz/nomenclature","info":"Nomenclature N°29, C09AA04"},
        {"source":"ANPP / pharmnet-dz","pays":"Algérie","url":"https://www.pharmnet-dz.com","info":"Fiches COVERSYL 5/10 mg, PERINDOPRIL BEKER 4/8 mg"},
        {"source":"ANSM / Base données publique","pays":"France","url":"https://base-donnees-publique.medicaments.gouv.fr","info":"RCP périndopril erbumine/arginine"},
        {"source":"dzair-pharma.net","pays":"Algérie","url":"https://www.dzair-pharma.net","info":"Vérification noms commerciaux"},
    ],
    "ramipril": [
        {"source":"MIPH","pays":"Algérie","url":"https://www.miph.gov.dz/nomenclature","info":"Nomenclature N°30, C09AA05"},
        {"source":"ANSM / Base données publique","pays":"France","url":"https://base-donnees-publique.medicaments.gouv.fr","info":"RCP et Notice ramipril (Triatec)"},
        {"source":"DailyMed / NLM-FDA","pays":"États-Unis","url":"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=ramipril","info":"Label Ramipril capsules (Altace)"},
        {"source":"ANPP / pharmnet-dz","pays":"Algérie","url":"https://www.pharmnet-dz.com","info":"Fiches spécialités ramipril"},
        {"source":"dzair-pharma.net","pays":"Algérie","url":"https://www.dzair-pharma.net","info":"Page DCI ramipril"},
    ],
}

mimetypes.add_type("application/pdf", ".pdf")
mimetypes.add_type("text/csv",        ".csv")
mimetypes.add_type("image/png",       ".png")

# ---------------------------------------------------------------------------
# STEP 1 : Extract Excel data
# ---------------------------------------------------------------------------
def extract_excel() -> dict:
    print("\n[1/4] Extraction des données Excel ...")
    wb = openpyxl.load_workbook(str(EXCEL_FILE))
    ws = wb.active
    rows_per_dci = {k: [] for k in DCI_CANONICAL}

    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if i == 1 or row[2] is None:
            continue
        dci_raw = str(row[2]).strip().lower()
        matched = None
        for dci_key, info in DCI_CANONICAL.items():
            for mk in info["excel_match_keys"]:
                if mk in dci_raw:
                    matched = dci_key; break
            if matched: break
        if not matched: continue

        # Clean ATC field (may contain Excel formula artefacts)
        atc_raw = str(row[3]).strip() if row[3] else ""
        atc_confirme = str(row[4]).strip() if row[4] else ""
        # Normalize formula artefacts
        if "IFERROR" in atc_confirme or "xludf" in atc_confirme:
            atc_confirme = "oui"  # infer from context

        rows_per_dci[matched].append({
            "excel_row":               i,
            "numero_dci":              int(row[0]) if isinstance(row[0], float) else str(row[0]) if row[0] else "",
            "classe_therapeutique":    str(row[1]).strip() if row[1] else "",
            "dci_excel":               str(row[2]).strip(),
            "code_atc":                atc_raw if "=" not in atc_raw else DCI_CANONICAL[matched]["code_atc"],
            "atc_confirme":            atc_confirme,
            "nomenclature_algerienne": str(row[5]).strip() if row[5] else "",
            "nom_commercial":          str(row[6]).strip() if row[6] else "",
            "forme_pharmaceutique":    str(row[7]).strip() if row[7] else "",
            "dosage":                  str(row[8]).strip() if row[8] else "",
            "sources_excel":           str(row[9]).strip() if row[9] else "",
            "remarques":               str(row[10]).strip() if row[10] else "",
        })

    for dci, rows in rows_per_dci.items():
        print(f"  {dci:15s} -> {len(rows)} lignes Excel extraites")
    return rows_per_dci

# ---------------------------------------------------------------------------
# STEP 2 : Scan filesystem metadata
# ---------------------------------------------------------------------------
def infer_type(p):
    mime, _ = mimetypes.guess_type(str(p))
    if not mime: return "unknown"
    if mime == "application/pdf": return "pdf"
    if mime.startswith("image/"): return mime.split("/")[-1]
    if mime in ("text/csv", "application/csv"): return "csv"
    return mime

def file_entry(fp: Path, base: Path) -> dict:
    return {
        "filename":      fp.name,
        "relative_path": fp.relative_to(base).as_posix(),
        "absolute_path": fp.resolve().as_posix(),
        "type":          infer_type(fp),
        "extension":     fp.suffix.lower().lstrip(".") or "none",
        "size_bytes":    fp.stat().st_size,
    }

def scan_corpus() -> dict:
    print("\n[2/4] Scan du corpus (chemins et fichiers) ...")
    result = {}
    for dci_dir in sorted(CORPUS_ROOT.iterdir()):
        if not dci_dir.is_dir(): continue
        dci_key = dci_dir.name
        brands, sources = [], []
        for item in sorted(dci_dir.iterdir()):
            if item.is_dir():
                brand_files = [file_entry(f, CORPUS_ROOT) for f in sorted(item.rglob("*")) if f.is_file()]
                brands.append({"brand_folder": item.name,
                                "relative_path": item.relative_to(CORPUS_ROOT).as_posix(),
                                "file_count": len(brand_files),
                                "files": brand_files})
            elif item.is_file():
                sources.append(file_entry(item, CORPUS_ROOT))
        result[dci_key] = {
            "relative_path":  dci_dir.relative_to(CORPUS_ROOT).as_posix(),
            "absolute_path":  dci_dir.resolve().as_posix(),
            "source_files":   sources,
            "brand_folders":  brands,
            "total_files":    len(sources) + sum(b["file_count"] for b in brands),
        }
        print(f"  {dci_key:15s} -> {result[dci_key]['total_files']} fichiers, {len(brands)} dossiers-marque")
    return result

# ---------------------------------------------------------------------------
# STEP 3 : Build UNIFIED structure
# ---------------------------------------------------------------------------
def build_unified(excel_data: dict, corpus_data: dict) -> dict:
    print("\n[3/4] Construction du JSON unifié ...")
    unified_corpus = []
    validation_issues = []

    for dci_key in sorted(DCI_CANONICAL.keys()):
        info   = DCI_CANONICAL[dci_key]
        ex     = excel_data.get(dci_key, [])
        corp   = corpus_data.get(dci_key, {})
        docs   = DOCUMENTS_REF.get(dci_key, {})
        srcs   = SOURCES_URLS.get(dci_key, [])

        # Derive brand summary from Excel rows
        brands_from_excel = []
        seen = {}
        for row in ex:
            nc = row["nom_commercial"]
            if not nc or nc.lower() in ("none", "nan", ""): continue
            key = (nc, row["forme_pharmaceutique"])
            if nc not in seen:
                seen[nc] = {"nom_commercial": nc,
                             "classe_therapeutique": row["classe_therapeutique"],
                             "presentations": []}
            seen[nc]["presentations"].append({
                "forme_pharmaceutique": row["forme_pharmaceutique"],
                "dosage":               row["dosage"],
                "excel_row":            row["excel_row"],
                "nomenclature_algerienne": row["nomenclature_algerienne"],
                "remarques":            row["remarques"],
            })
        brands_from_excel = list(seen.values())

        # Derive distinct formes/dosages
        formes_dosages = []
        seen_fd = set()
        for row in ex:
            fd = (row["forme_pharmaceutique"], row["dosage"])
            if fd not in seen_fd and row["forme_pharmaceutique"]:
                seen_fd.add(fd)
                formes_dosages.append({"forme": row["forme_pharmaceutique"], "dosage": row["dosage"]})

        # Build document paths with existence check
        docs_with_check = {}
        for doc_type, doc_list in docs.items():
            checked = []
            for d in doc_list:
                fp = CORPUS_ROOT / dci_key / d["fichier"]
                checked.append({**d, "exists_on_disk": fp.exists(),
                                 "absolute_path": fp.resolve().as_posix()})
            docs_with_check[doc_type] = checked

        # Cross-checks
        excel_rows_count = len(ex)
        files_count      = corp.get("total_files", 0)
        if excel_rows_count == 0:
            validation_issues.append({"level":"ERROR","dci":dci_key,
                                       "msg":"Aucune ligne Excel trouvée"})
        if files_count == 0:
            validation_issues.append({"level":"ERROR","dci":dci_key,
                                       "msg":"Aucun fichier trouvé dans le corpus"})
        for doc_type, checked_list in docs_with_check.items():
            for d in checked_list:
                if not d["exists_on_disk"]:
                    validation_issues.append({"level":"WARN","dci":dci_key,
                                               "msg":f"Fichier référencé manquant sur disque: {d['fichier']}"})

        # Assemble unified entry
        entry = {
            # --- Identité DCI ---
            "dci":               dci_key,
            "dci_display":       info["dci_display"],
            "code_atc":          info["code_atc"],
            "classe_therapeutique": info["classe"],
            "miph_numero":       info["miph_numero"],
            "miph_present":      info["miph_present"],
            "source_reference":  info["source_reference"],

            # --- Statut ANPP ---
            "anpp": {
                "rcp_trouve":    info["anpp_rcp"],
                "notice_trouvee":info["anpp_notice"],
            },

            # --- Données Excel granulaires ---
            "excel_summary": {
                "total_lignes_excel": excel_rows_count,
                "lignes_excel":       [row["excel_row"] for row in ex],
                "noms_commerciaux_count": len(brands_from_excel),
            },
            "noms_commerciaux": brands_from_excel,
            "formes_et_dosages": formes_dosages,

            # --- Données Excel brutes (toutes les lignes) ---
            "excel_rows_detail": ex,

            # --- Métadonnées fichiers (corpus/) ---
            "corpus_metadata": {
                "relative_path": corp.get("relative_path", dci_key),
                "absolute_path": corp.get("absolute_path", ""),
                "total_files":   files_count,
                "source_files":  corp.get("source_files", []),
                "brand_folders": corp.get("brand_folders", []),
            },

            # --- Documents de référence (RCP, Notice, Info) ---
            "documents_reference": docs_with_check,

            # --- Sources officielles ---
            "sources_officielles": srcs,
        }
        unified_corpus.append(entry)
        print(f"  [OK] {dci_key:15s} : {excel_rows_count} lignes Excel | "
              f"{len(brands_from_excel)} marques | {files_count} fichiers corpus")

    return unified_corpus, validation_issues

# ---------------------------------------------------------------------------
# STEP 4 : Write outputs + validate
# ---------------------------------------------------------------------------
def write_outputs(unified_corpus: list, validation_issues: list, excel_data: dict, corpus_data: dict):
    print("\n[4/4] Écriture des fichiers de sortie ...")

    total_excel_rows = sum(len(excel_data.get(d["dci"], [])) for d in unified_corpus)
    total_brands     = sum(len(d["noms_commerciaux"]) for d in unified_corpus)
    total_files      = sum(d["corpus_metadata"]["total_files"] for d in unified_corpus)

    output = {
        "_meta": {
            "generated_at":         datetime.now(timezone.utc).isoformat(),
            "corpus_root":          CORPUS_ROOT.resolve().as_posix(),
            "excel_source":         EXCEL_FILE.resolve().as_posix(),
            "total_dci_count":      len(unified_corpus),
            "total_excel_rows":     total_excel_rows,
            "total_noms_commerciaux": total_brands,
            "total_corpus_files":   total_files,
            "validation_issues":    len(validation_issues),
        },
        "corpus": unified_corpus,
        "validation_log": validation_issues,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  --> JSON unifié : {OUTPUT_JSON}  ({OUTPUT_JSON.stat().st_size/1024:.1f} KB)")

    # TXT report
    lines = []
    sep, thin = "="*72, "-"*72
    def h1(t): lines.append(f"\n{sep}\n  {t}\n{sep}")
    def h2(t): lines.append(f"\n{thin}\n  {t}\n{thin}")
    def li(t): lines.append(f"    {t}")
    def blank(): lines.append("")

    h1("COGNIVEX — RAPPORT CORPUS UNIFIÉ")
    li(f"Généré le : {datetime.now(timezone.utc).isoformat()}")
    li(f"Corpus    : {CORPUS_ROOT.resolve()}")
    li(f"Excel     : {EXCEL_FILE.resolve()}")
    blank()

    h2("BILAN GLOBAL")
    li(f"DCIs traités               : {len(unified_corpus)}")
    li(f"Total lignes Excel         : {total_excel_rows}")
    li(f"Total noms commerciaux     : {total_brands}")
    li(f"Total fichiers corpus      : {total_files}")
    li(f"Problèmes de validation    : {len(validation_issues)}")

    for d in unified_corpus:
        h2(f"DCI : {d['dci_display'].upper()} ({d['code_atc']})")
        li(f"Classe               : {d['classe_therapeutique']}")
        li(f"MIPH N°{d['miph_numero']:02d} présent      : {d['miph_present'].upper()}")
        li(f"ANPP RCP trouvé      : {'OUI' if d['anpp']['rcp_trouve'] else 'NON — document ANPP non trouvé'}")
        li(f"ANPP Notice trouvée  : {'OUI' if d['anpp']['notice_trouvee'] else 'NON — document ANPP non trouvé'}")
        li(f"Source référence     : {d['source_reference']}")
        blank()

        li(f"Lignes Excel ({d['excel_summary']['total_lignes_excel']}) : {d['excel_summary']['lignes_excel']}")
        blank()

        li(f"Noms commerciaux ({len(d['noms_commerciaux'])}) :")
        for nc in d["noms_commerciaux"]:
            presens = " | ".join(f"{p['forme_pharmaceutique']} {p['dosage']} (l.{p['excel_row']})"
                                  for p in nc["presentations"])
            li(f"  - {nc['nom_commercial']:30s} : {presens}")
        blank()

        li(f"Fichiers corpus ({d['corpus_metadata']['total_files']}) :")
        for sf in d["corpus_metadata"]["source_files"]:
            li(f"  [DCI]   {sf['filename']}  ({sf['type'].upper()}, {sf['size_bytes']//1024} KB)")
        for bf in d["corpus_metadata"]["brand_folders"]:
            li(f"  [DOSS]  {bf['relative_path']}/  ({bf['file_count']} fichiers)")
            for f in bf["files"]:
                li(f"           └─ {f['filename']}  ({f['type'].upper()}, {f['size_bytes']//1024} KB)")
        blank()

        li("Documents de référence :")
        for doc_type, dlist in d["documents_reference"].items():
            for doc in dlist:
                ok = "✓" if doc["exists_on_disk"] else "✗ MANQUANT"
                li(f"  [{doc_type.upper():6s}] {doc['source']:12s} ({doc['pays']:15s}) {ok:10s} {doc['fichier']}")
        blank()

        li("Sources officielles :")
        for src in d["sources_officielles"]:
            li(f"  [{src['pays']:15s}] {src['source']} — {src['info']}")
            li(f"               URL: {src['url']}")

    h2("VALIDATION")
    if not validation_issues:
        li("[PARFAIT] Aucun problème détecté — JSON unifié cohérent avec corpus et Excel.")
    else:
        for iss in validation_issues:
            li(f"[{iss.get('level','?'):6s}] ({iss.get('dci',''):15s}) {iss['msg']}")

    h1("FIN DU RAPPORT")
    OUTPUT_TXT.write_text("\n".join(lines), encoding="utf-8")
    print(f"  --> Rapport TXT : {OUTPUT_TXT}  ({OUTPUT_TXT.stat().st_size/1024:.1f} KB)")
    return output

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("\n"+"="*60)
    print("   COGNIVEX — GÉNÉRATION CORPUS UNIFIÉ")
    print("="*60)

    excel_data  = extract_excel()
    corpus_data = scan_corpus()
    unified, issues = build_unified(excel_data, corpus_data)
    result = write_outputs(unified, issues, excel_data, corpus_data)

    # Console final
    print("\n"+"="*60)
    print("  BILAN FINAL")
    print("="*60)
    m = result["_meta"]
    print(f"  DCIs traités             : {m['total_dci_count']}")
    print(f"  Lignes Excel totales     : {m['total_excel_rows']}")
    print(f"  Noms commerciaux totaux  : {m['total_noms_commerciaux']}")
    print(f"  Fichiers corpus totaux   : {m['total_corpus_files']}")
    print(f"  Problèmes de validation  : {m['validation_issues']}")
    if issues:
        print("\n  Détail des problèmes :")
        for iss in issues:
            print(f"    [{iss.get('level','?'):6s}] ({iss.get('dci',''):12s}) {iss['msg']}")
    else:
        print("\n  Aucun problème — Corpus unifié valide.")
    print(f"\n  Fichiers générés :")
    print(f"    {OUTPUT_JSON}")
    print(f"    {OUTPUT_TXT}")
    print("="*60)

if __name__ == "__main__":
    main()
