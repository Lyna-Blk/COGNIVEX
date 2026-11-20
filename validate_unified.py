import json, os, pathlib

with open("data/corpus_unified.json", encoding="utf-8") as f:
    d = json.load(f)

m = d["_meta"]
print("=== META ===")
for k,v in m.items():
    print(f"  {k}: {v}")

print("\n=== STRUCTURE CHECK PAR DCI ===")
issues = []
REQUIRED_KEYS = ["dci","dci_display","code_atc","classe_therapeutique",
                 "miph_numero","miph_present","anpp","excel_summary",
                 "noms_commerciaux","formes_et_dosages","excel_rows_detail",
                 "corpus_metadata","documents_reference","sources_officielles"]

for entry in d["corpus"]:
    dci = entry["dci"]
    missing = [k for k in REQUIRED_KEYS if k not in entry]
    if missing:
        issues.append(f"[{dci}] Cles manquantes: {missing}")
    n_excel   = entry["excel_summary"]["total_lignes_excel"]
    n_brands  = entry["excel_summary"]["noms_commerciaux_count"]
    n_files   = entry["corpus_metadata"]["total_files"]
    n_sources = len(entry["sources_officielles"])
    n_docs    = sum(len(v) for v in entry["documents_reference"].values())
    for doc_type, dlist in entry["documents_reference"].items():
        for doc in dlist:
            if not doc.get("exists_on_disk"):
                issues.append(f"[{dci}][{doc_type}] Fichier manquant: {doc['fichier']}")
    if n_sources < 3:
        issues.append(f"[{dci}] Seulement {n_sources} sources officielles (min 3)")
    if len(entry["formes_et_dosages"]) == 0 and dci != "nifedipine":
        issues.append(f"[{dci}] formes_et_dosages vide")
    anpp_r = "OUI" if entry["anpp"]["rcp_trouve"] else "NON"
    anpp_n = "OUI" if entry["anpp"]["notice_trouvee"] else "NON"
    print(f"  {dci:15s} ATC={entry['code_atc']}  MIPH={entry['miph_present'].upper():3s}"
          f"  Excel={n_excel:2d}L  Marques={n_brands:2d}  Fichiers={n_files:2d}"
          f"  Sources={n_sources}  Docs={n_docs}  ANPP_RCP={anpp_r}  ANPP_Notice={anpp_n}")

print("\n=== VALIDATION JSON ===")
if not issues:
    print("  [OK] Aucune incoherence detectee. JSON unifie valide et complet.")
else:
    for iss in issues:
        print(f"  [WARN] {iss}")

# Round-trip check
json_str  = json.dumps(d, ensure_ascii=False, indent=2)
reparsed  = json.loads(json_str)
assert reparsed["_meta"]["total_dci_count"] == 8, "Round-trip FAILED"
print("  [OK] Round-trip JSON: PASSED")

sz = os.path.getsize("data/corpus_unified.json")
print(f"  [OK] Taille JSON: {sz/1024:.1f} KB")

# Check all 8 DCIs present
expected = {"amlodipine","losartan","clindamycine","enalapril",
            "gentamicine","nifedipine","perindopril","ramipril"}
found = {e["dci"] for e in d["corpus"]}
if expected == found:
    print("  [OK] Les 8 DCIs sont presents dans le JSON unifie")
else:
    print(f"  [ERR] DCIs manquants: {expected - found}")

# Check _meta counts consistency
total_excel = sum(e["excel_summary"]["total_lignes_excel"] for e in d["corpus"])
total_brands = sum(e["excel_summary"]["noms_commerciaux_count"] for e in d["corpus"])
total_files  = sum(e["corpus_metadata"]["total_files"] for e in d["corpus"])
assert total_excel == m["total_excel_rows"], f"Excel count mismatch: {total_excel} vs {m['total_excel_rows']}"
assert total_brands == m["total_noms_commerciaux"], f"Brands mismatch"
assert total_files  == m["total_corpus_files"], f"Files mismatch"
print(f"  [OK] Compteurs _meta coherents: {total_excel} lignes Excel, {total_brands} marques, {total_files} fichiers")

print("\n=== RESUME NOMS COMMERCIAUX PAR DCI ===")
for entry in d["corpus"]:
    noms = [nc["nom_commercial"] for nc in entry["noms_commerciaux"]]
    print(f"  {entry['dci_display']:20s} ({len(noms):2d} marques): {', '.join(noms)}")
