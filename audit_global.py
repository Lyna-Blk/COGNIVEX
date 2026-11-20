"""
audit_global.py  --  COGNIVEX Audit Global
Etape 1 : Scan filesystem (retourne metadata en memoire, source = corpus_unified.json)
Etape 2 : Audit PDF (extractabilite, bruit, doublons)
Etape 3 : Validation croisee avec corpus_medicaments.md
Etape 4 : Ecrit rapport TXT + corpus_audit_report.json

Note: corpus_metadata.json est SUPPRIME. L'unique source de verite est corpus_unified.json.
"""
import os, sys, json, hashlib, re, mimetypes
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        sys.exit("[ERROR] PyMuPDF non installe. Lancez: pip install pymupdf")

CORPUS_ROOT   = Path(__file__).parent / "data" / "corpus"
MARKDOWN_FILE = Path(__file__).parent / "data" / "corpus_medicaments.md"
UNIFIED_JSON  = Path(__file__).parent / "data" / "corpus_unified.json"
AUDIT_JSON    = Path(__file__).parent / "data" / "corpus_audit_report.json"
AUDIT_TXT     = Path(__file__).parent / "data" / "corpus_audit_report.txt"

MIN_CHARS_TOTAL    = 100
MIN_CHARS_PER_PAGE = 200
NOISE_REPEAT       = 5
IMG_RATIO_WARN     = 0.5

mimetypes.add_type("application/pdf", ".pdf")
mimetypes.add_type("text/csv",        ".csv")
mimetypes.add_type("image/png",       ".png")

EXPECTED_DCIS = {
    "amlodipine":  {"atc":"C08CA01","miph":"oui","anpp_found":True},
    "losartan":    {"atc":"C09CA01","miph":"oui","anpp_found":True},
    "clindamycine":{"atc":"J01FF01","miph":"oui","anpp_found":False},
    "enalapril":   {"atc":"C09AA02","miph":"oui","anpp_found":False},
    "gentamicine": {"atc":"J01GB03","miph":"oui","anpp_found":False},
    "nifedipine":  {"atc":"C08CA05","miph":"non","anpp_found":False},
    "perindopril": {"atc":"C09AA04","miph":"oui","anpp_found":False},
    "ramipril":    {"atc":"C09AA05","miph":"oui","anpp_found":False},
}

REQUIRED_FILES = {
    "amlodipine":  ["source-amdolipine rcp.pdf",
                    "source-amdolipine-daily med -rcp.pdf",
                    "source-amlodopine-notice.pdf",
                    "Source-info -amlodipline.pdf",
                    "mibral/RCP-MIBRL.pdf"],
    "losartan":    ["LOSartan anpp.pdf","rcp-losartan.pdf",
                    "dailymed-losartan.pdf","notice-losartan.pdf","info-losartan.pdf"],
    "clindamycine":["source_ansm-rcp.pdf","source-ansm-notice.pdf","source-ansm_info.pdf"],
    "enalapril":   ["rcp-enalapril.pdf","notice-enalapril.pdf","info-enalapril.pdf","dwa--dz.pdf"],
    "gentamicine": ["daily med genta.pdf","genta_80/source_ansm_rcp.pdf",
                    "genta_80/source_ansm_noticc.pdf","genta_80/source_ansm_fiche_info.pdf"],
    "nifedipine":  ["dailymed-nifedipine.pdf"],
    "perindopril": ["perindopril/source rcp. prindoprile.pdf",
                    "coversyl/source-generique-.pdf","perindopril/generique.pdf"],
    "ramipril":    ["rcpramplir.pdf","notice-ramplir.pdf","ramplir-dailymed.pdf","info.pdf"],
}

# ==========================================================================
# HELPERS
# ==========================================================================
def infer_type(p):
    mime, _ = mimetypes.guess_type(str(p))
    if not mime: return "unknown"
    if mime=="application/pdf": return "pdf"
    if mime.startswith("image/"): return mime.split("/")[-1]
    if mime in ("text/csv","application/csv"): return "csv"
    return mime

def file_entry(fp, base):
    return {"filename": fp.name,
            "relative_path": fp.relative_to(base).as_posix(),
            "absolute_path": fp.resolve().as_posix(),
            "type": infer_type(fp),
            "extension": fp.suffix.lower().lstrip(".") or "none",
            "size_bytes": fp.stat().st_size}

def sha256(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(65536), b""): h.update(chunk)
    return h.hexdigest()

# ==========================================================================
# ETAPE 1 : METADATA
# ==========================================================================
def scan_brand(bdir, root):
    files = [file_entry(f,root) for f in sorted(bdir.rglob("*")) if f.is_file()]
    return {"brand_name": bdir.name,
            "relative_path": bdir.relative_to(root).as_posix(),
            "absolute_path": bdir.resolve().as_posix(),
            "file_count": len(files),
            "files": files}

def scan_dci(ddir, root):
    brands, sources = [], []
    for item in sorted(ddir.iterdir()):
        if item.is_dir(): brands.append(scan_brand(item, root))
        elif item.is_file(): sources.append(file_entry(item, root))
    total = len(sources) + sum(b["file_count"] for b in brands)
    return {"dci": ddir.name, "relative_path": ddir.relative_to(root).as_posix(),
            "absolute_path": ddir.resolve().as_posix(),
            "brand_count": len(brands), "total_files": total,
            "source_files": sources, "brands": brands}

def step_metadata():
    print("\n[ETAPE 1] Scan filesystem -> mise a jour de corpus_unified.json ...")
    dcis = [scan_dci(d, CORPUS_ROOT) for d in sorted(CORPUS_ROOT.iterdir()) if d.is_dir()]
    # Build a lightweight meta dict (same shape as before for compatibility)
    meta = {"_meta": {"generated_at": datetime.now(timezone.utc).isoformat(),
                       "corpus_root": CORPUS_ROOT.resolve().as_posix(),
                       "total_dci_count": len(dcis),
                       "total_brands": sum(d["brand_count"] for d in dcis),
                       "total_files": sum(d["total_files"]  for d in dcis)},
            "corpus": dcis}
    m = meta["_meta"]
    print(f"  DCIs={m['total_dci_count']}  Brands={m['total_brands']}  Fichiers={m['total_files']}")
    for d in dcis:
        brands_str = ", ".join(b["brand_name"] for b in d["brands"]) or "(aucune)"
        print(f"    {d['dci']:15s}  brands={d['brand_count']}  files={d['total_files']}  [{brands_str}]")

    # Patch corpus_unified.json with fresh filesystem data
    if UNIFIED_JSON.exists():
        try:
            unified = json.loads(UNIFIED_JSON.read_text(encoding="utf-8"))
            dci_lookup = {entry["dci"]: entry for entry in unified.get("corpus", [])}
            for d in dcis:
                if d["dci"] in dci_lookup:
                    dci_lookup[d["dci"]]["corpus_metadata"] = {
                        "relative_path": d["relative_path"],
                        "absolute_path": d["absolute_path"],
                        "total_files":   d["total_files"],
                        "source_files":  d["source_files"],
                        "brand_folders": d["brands"],
                    }
            unified["_meta"]["last_audit_scan"] = datetime.now(timezone.utc).isoformat()
            unified["_meta"]["total_corpus_files"] = m["total_files"]
            UNIFIED_JSON.write_text(json.dumps(unified, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  --> corpus_unified.json mis a jour : {UNIFIED_JSON}")
        except Exception as e:
            print(f"  [WARN] Impossible de patcher corpus_unified.json : {e}")
    else:
        print(f"  [WARN] corpus_unified.json introuvable - lancez d'abord generate_unified_corpus.py")
    return meta

# ==========================================================================
# ETAPE 2 : AUDIT PDF
# ==========================================================================
def analyze_pdf(path):
    r = {"status":"ok","page_count":0,"total_chars":0,
         "image_only_pages":0,"short_pages":0,
         "has_noise":False,"noise_samples":[],"issues":[]}
    try:
        doc = fitz.open(str(path))
    except Exception as e:
        r.update({"status":"corrupt","issues":[f"Impossible d'ouvrir: {e}"]}); return r
    r["page_count"] = len(doc)
    if not len(doc):
        r.update({"status":"empty","issues":["0 pages"]}); doc.close(); return r
    bc = defaultdict(int)
    for page in doc:
        text = page.get_text("text").strip()
        chars = len(text)
        r["total_chars"] += chars
        if chars==0: r["image_only_pages"]+=1
        elif chars<MIN_CHARS_PER_PAGE: r["short_pages"]+=1
        for blk in page.get_text("blocks"):
            bt = blk[4].strip() if len(blk)>4 else ""
            if 5<len(bt)<120: bc[bt]+=1
    doc.close()
    noisy = {t:n for t,n in bc.items() if n>=NOISE_REPEAT}
    if noisy:
        r["has_noise"] = True
        r["noise_samples"] = ['"{}" (x{})'.format(t[:80],n)
                               for t,n in sorted(noisy.items(),key=lambda x:-x[1])[:5]]
    total=r["total_chars"]; ip=r["image_only_pages"]; np_=r["page_count"]
    ratio=ip/np_ if np_ else 0
    if total<MIN_CHARS_TOTAL:
        r["status"]="needs_ocr" if ip else "empty"
        r["issues"].append(f"Seulement {total} caracteres extraits - PDF image")
    elif ratio>=IMG_RATIO_WARN:
        r["status"]="needs_ocr"
        r["issues"].append(f"{ip}/{np_} pages ({ratio:.0%}) sans texte extractible")
    if r["has_noise"]:
        r["issues"].append(f"Bruit repete detecte ({len(noisy)} blocs uniques)")
    if r["short_pages"] and r["status"]=="ok":
        r["issues"].append(f"{r['short_pages']} page(s) < {MIN_CHARS_PER_PAGE} caracteres")
    return r

def step_audit():
    print("\n[ETAPE 2] Audit qualite PDF ...")
    all_files = sorted(p for p in CORPUS_ROOT.rglob("*") if p.is_file())
    print(f"  Fichiers trouves : {len(all_files)}")
    size_map = defaultdict(list)
    for p in all_files: size_map[p.stat().st_size].append(p)
    cand = {p for ps in size_map.values() if len(ps)>1 for p in ps}
    file_hashes, hash_map = {}, defaultdict(list)
    for p in all_files:
        if p in cand:
            h=sha256(p); file_hashes[p]=h; hash_map[h].append(p)
        else: file_hashes[p]=None
    dup_groups = {h:ps for h,ps in hash_map.items() if len(ps)>1}
    dupe_files = {p for ps in dup_groups.values() for p in ps[1:]}
    file_results=[];valid=[]; needs_ocr=[]; errors=[]; noisy=[]; non_pdf=[]
    for path in all_files:
        rel=path.relative_to(CORPUS_ROOT).as_posix(); ext=path.suffix.lower()
        entry={"path":rel,"absolute":path.resolve().as_posix(),
               "extension":ext.lstrip("."),"size_bytes":path.stat().st_size,
               "hash_sha256":file_hashes.get(path),"is_duplicate":path in dupe_files}
        if ext==".pdf":
            info=analyze_pdf(path); entry.update(info)
            if info["status"]=="ok" and path not in dupe_files: valid.append(rel)
            elif info["status"]=="needs_ocr": needs_ocr.append(rel)
            elif info["status"] in ("empty","corrupt"): errors.append(rel)
            if info.get("has_noise"): noisy.append(rel)
        else:
            entry["status"]="non_pdf"; non_pdf.append(rel)
        file_results.append(entry)
    dup_rep=[{"hash":h,"files":[p.relative_to(CORPUS_ROOT).as_posix() for p in ps],
              "size_bytes":ps[0].stat().st_size} for h,ps in dup_groups.items()]
    report={"_meta":{"generated_at":datetime.now(timezone.utc).isoformat(),
                      "corpus_root":CORPUS_ROOT.resolve().as_posix(),
                      "total_files":len(all_files),
                      "total_pdf":sum(1 for f in file_results if f["extension"]=="pdf"),
                      "valid_for_rag":len(valid),"needs_ocr":len(needs_ocr),
                      "empty_or_corrupt":len(errors),"noisy":len(noisy),
                      "non_pdf":len(non_pdf),"duplicate_groups":len(dup_groups)},
            "valid_for_rag":valid,"needs_ocr":needs_ocr,"empty_or_corrupt":errors,
            "noisy_files":noisy,"non_pdf_files":non_pdf,"duplicate_groups":dup_rep,
            "files":file_results}
    AUDIT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    m=report["_meta"]
    print(f"  READY={m['valid_for_rag']}  OCR={m['needs_ocr']}  "
          f"ERROR={m['empty_or_corrupt']}  NOISE={m['noisy']}  "
          f"NON-PDF={m['non_pdf']}  DUPES={m['duplicate_groups']}")
    print(f"  --> Ecrit : {AUDIT_JSON}")
    return report

# ==========================================================================
# ETAPE 3 : VALIDATION CROISEE MARKDOWN
# ==========================================================================
def extract_dci_section(md, dci):
    variants=[dci.upper()]
    if dci=="enalapril": variants.append("ENALAPRIL"); variants.append("ÉNALAPRIL")
    if dci=="perindopril": variants.append("PÉRINDOPRIL")
    if dci=="nifedipine": variants.append("NIFÉDIPINE")
    for v in variants:
        m=re.search(rf'# DCI : {re.escape(v)}(.*?)(?=\n# DCI :|\Z)',md,re.DOTALL|re.IGNORECASE)
        if m: return m.group(1)
    return ""

def step_validate(metadata):
    print("\n[ETAPE 3] Validation croisee corpus_medicaments.md ...")
    issues=[]
    if not MARKDOWN_FILE.exists():
        issues.append({"level":"CRITICAL","msg":f"corpus_medicaments.md introuvable : {MARKDOWN_FILE}"})
        return issues
    md=MARKDOWN_FILE.read_text(encoding="utf-8")

    # 1. Headings DCI
    for dci in EXPECTED_DCIS:
        variants=[dci.upper(),"ÉNALAPRIL" if dci=="enalapril" else "",
                  "PÉRINDOPRIL" if dci=="perindopril" else "",
                  "NIFÉDIPINE" if dci=="nifedipine" else ""]
        found=any(v and v in md for v in variants)
        if not found:
            issues.append({"level":"ERROR","dci":dci,"msg":f"Titre DCI '{dci.upper()}' absent du markdown"})
        else:
            print(f"  [OK] Titre '{dci.upper()}' present")

    # 2. Codes ATC
    for dci,info in EXPECTED_DCIS.items():
        atc=info["atc"]
        if atc not in md:
            issues.append({"level":"ERROR","dci":dci,"msg":f"Code ATC '{atc}' absent du markdown"})
        else:
            print(f"  [OK] ATC {atc} ({dci})")

    # 3. Regles ANPP
    for dci,info in EXPECTED_DCIS.items():
        sec=extract_dci_section(md,dci)
        if info["anpp_found"]:
            if "document ANPP non trouvé" in sec or "document ANPP non trouve" in sec:
                issues.append({"level":"ERROR","dci":dci,
                               "msg":f"ANPP section de {dci} dit 'non trouvé' mais devrait dire 'trouvé'"})
            elif "RCP trouvé" in sec or "Notice trouvée" in sec or "RCP trouve" in sec:
                print(f"  [OK] ANPP trouvé pour {dci}")
            else:
                issues.append({"level":"WARN","dci":dci,
                               "msg":f"Section ANPP de {dci}: 'RCP trouvé'/'Notice trouvée' non clairement indiqué"})
        else:
            if "document ANPP non trouvé" not in sec and "document ANPP non trouve" not in sec:
                issues.append({"level":"WARN","dci":dci,
                               "msg":f"Section ANPP de {dci}: 'document ANPP non trouvé' absent"})
            else:
                print(f"  [OK] ANPP non trouvé correctement indiqué pour {dci}")

    # 4. Fichiers requis sur disque
    for dci,req_list in REQUIRED_FILES.items():
        for req in req_list:
            fp=(CORPUS_ROOT/dci/req)
            if not fp.exists():
                issues.append({"level":"ERROR","dci":dci,
                               "msg":f"Fichier requis manquant : corpus/{dci}/{req}"})
            else:
                print(f"  [OK] Fichier present : {dci}/{req}")

    # 5. Sections Sources consultees (>= 3 entrees chacune)
    secs=re.findall(r'## Sources consultées\n(.*?)(?=\n##|\n---|\Z)',md,re.DOTALL)
    for i,sec in enumerate(secs):
        entries=[l for l in sec.strip().splitlines() if l.strip().startswith("- [")]
        if len(entries)<3:
            issues.append({"level":"WARN",
                           "msg":f"'Sources consultées' #{i+1} : {len(entries)} entree(s) (min 3)"})
        else:
            print(f"  [OK] Sources consultées #{i+1} : {len(entries)} entrees")

    # 6. Sections Precision (>= 2 puces chacune)
    precs=re.findall(r'## Précision\n(.*?)(?=\n##|\n---|\Z)',md,re.DOTALL)
    for i,sec in enumerate(precs):
        bullets=[l for l in sec.strip().splitlines() if l.strip().startswith("- ")]
        if len(bullets)<2:
            issues.append({"level":"WARN",
                           "msg":f"'Précision' #{i+1} : {len(bullets)} puce(s) (min 2)"})
        else:
            print(f"  [OK] Precision #{i+1} : {len(bullets)} puces")

    # 7. Verification sections obligatoires presentes pour chaque DCI
    required_sections=["## Documents de référence","## Recherche ANPP",
                       "## Sources consultées","## Précision"]
    for dci in EXPECTED_DCIS:
        sec=extract_dci_section(md,dci)
        for section in required_sections:
            if section not in sec:
                issues.append({"level":"WARN","dci":dci,
                               "msg":f"Section '{section}' absente ou mal formee pour {dci}"})

    # 8. Nifedipine : verifier "Non" pour MIPH
    nif_sec=extract_dci_section(md,"nifedipine")
    if "Non" not in nif_sec and "non" not in nif_sec:
        issues.append({"level":"WARN","dci":"nifedipine",
                       "msg":"MIPH 'Non' non clairement indique pour nifedipine"})
    else:
        print("  [OK] Nifedipine : MIPH 'Non' indique")

    print(f"\n  Problemes detectes : {len(issues)}")
    return issues

# ==========================================================================
# ETAPE 4 : RAPPORT TXT
# ==========================================================================
def write_txt(audit, errors, metadata):
    lines=[]; sep="="*72; thin="-"*72
    def h1(t): lines.append(f"\n{sep}\n  {t}\n{sep}")
    def h2(t): lines.append(f"\n{thin}\n  {t}\n{thin}")
    def li(t): lines.append(f"    {t}")
    def blank(): lines.append("")

    h1("COGNIVEX — AUDIT GLOBAL COMPLET")
    li(f"Generated : {datetime.now(timezone.utc).isoformat()}")
    li(f"Corpus    : {CORPUS_ROOT.resolve()}")
    li(f"Markdown  : {MARKDOWN_FILE}")
    blank()

    h2("METADONNEES CORPUS")
    m=metadata["_meta"]
    li(f"DCIs catalogues   : {m['total_dci_count']}")
    li(f"Brands catalogues : {m['total_brands']}")
    li(f"Total fichiers    : {m['total_files']}")
    blank()
    for d in metadata["corpus"]:
        bnames=", ".join(b["brand_name"] for b in d["brands"]) or "(aucune)"
        li(f"{d['dci']:15s}  brands={d['brand_count']}  files={d['total_files']}  [{bnames}]")

    h2("AUDIT PDF — BILAN")
    am=audit["_meta"]
    li(f"Total fichiers scannes      : {am['total_files']}")
    li(f"Total PDFs analyses         : {am['total_pdf']}")
    blank()
    li(f"[READY]  Valides pour RAG       : {am['valid_for_rag']}")
    li(f"[OCR]    Necessitent OCR        : {am['needs_ocr']}")
    li(f"[ERROR]  Vides / Corrompus      : {am['empty_or_corrupt']}")
    li(f"[NOISE]  Bruit en-tete/pied     : {am['noisy']}")
    li(f"[IMAGE]  Non-PDF (CSV/PNG...)   : {am['non_pdf']}")
    li(f"[DUPE]   Groupes doublons       : {am['duplicate_groups']}")

    h2("FICHIERS VALIDES POUR RAG")
    for f in audit["valid_for_rag"]: li(f"[OK]    {f}")
    if not audit["valid_for_rag"]: li("(aucun)")

    h2("FICHIERS NECESSITANT OCR")
    for f in audit["needs_ocr"]:
        entry=next((e for e in audit["files"] if e["path"]==f),{})
        issues="; ".join(entry.get("issues",[]))
        li(f"[OCR]  {f}")
        li(f"       => {issues}")

    h2("FICHIERS VIDES OU CORROMPUS")
    for f in audit["empty_or_corrupt"]:
        entry=next((e for e in audit["files"] if e["path"]==f),{})
        li(f"[ERR]  {f} => {'; '.join(entry.get('issues',[]))}")
    if not audit["empty_or_corrupt"]: li("(aucun)")

    h2("BRUIT EN-TETE / PIED DE PAGE")
    for f in audit["noisy_files"]:
        entry=next((e for e in audit["files"] if e["path"]==f),{})
        li(f"[NOISE]  {f}")
        for s in entry.get("noise_samples",[])[:3]: li(f"         Bloc repete : {s}")
    if not audit["noisy_files"]: li("(aucun)")

    h2("DOUBLONS")
    for grp in audit["duplicate_groups"]:
        li(f"Hash: {grp['hash'][:16]}...  Taille: {grp['size_bytes']:,} octets")
        for fp in grp["files"]: li(f"  - {fp}")
        blank()
    if not audit["duplicate_groups"]: li("(aucun)")

    h2("FICHIERS NON-PDF")
    for f in audit["non_pdf_files"]:
        entry=next((e for e in audit["files"] if e["path"]==f),{})
        li(f"[{entry.get('extension','?').upper():>4}]  {f}  ({entry.get('size_bytes',0):,} octets)")

    h2("VALIDATION CROISEE — corpus_medicaments.md")
    crit=[e for e in errors if e.get("level")=="CRITICAL"]
    errs=[e for e in errors if e.get("level")=="ERROR"]
    warns=[e for e in errors if e.get("level")=="WARN"]
    if not errors:
        li("[PARFAIT] Aucune erreur detectee. Le markdown est coherent avec le corpus.")
    else:
        li(f"CRITICAL : {len(crit)}")
        li(f"ERROR    : {len(errs)}")
        li(f"WARN     : {len(warns)}")
        blank()
        for e in errors:
            dci_tag=f"  ({e.get('dci','')})" if e.get("dci") else ""
            li(f"[{e.get('level','?'):8s}]{dci_tag}  {e['msg']}")

    h1("FIN DU RAPPORT")
    AUDIT_TXT.write_text("\n".join(lines), encoding="utf-8")
    print(f"  --> Ecrit : {AUDIT_TXT}")

# ==========================================================================
# MAIN
# ==========================================================================
def main():
    print("\n"+"="*60)
    print("   COGNIVEX — AUDIT GLOBAL")
    print("="*60)
    metadata = step_metadata()
    audit    = step_audit()
    errors   = step_validate(metadata)
    write_txt(audit, errors, metadata)

    print("\n"+"="*60)
    print("  BILAN FINAL")
    print("="*60)
    am=audit["_meta"]; mm=metadata["_meta"]
    print(f"  Metadata  : {mm['total_dci_count']} DCIs | {mm['total_brands']} brands | {mm['total_files']} fichiers")
    print(f"  Audit PDF : {am['valid_for_rag']} READY | {am['needs_ocr']} OCR | "
          f"{am['empty_or_corrupt']} ERROR | {am['noisy']} NOISE | {am['duplicate_groups']} DUPES")
    crit=sum(1 for e in errors if e.get("level")=="CRITICAL")
    errcnt=sum(1 for e in errors if e.get("level")=="ERROR")
    warns=sum(1 for e in errors if e.get("level")=="WARN")
    print(f"  Validation: {crit} CRITICAL | {errcnt} ERROR | {warns} WARN")
    if errors:
        print("\n  Problemes detectes :")
        for e in errors:
            dci=f"({e.get('dci','')})" if e.get("dci") else ""
            print(f"    [{e.get('level','?'):8s}] {dci:18s} {e['msg']}")
    print(f"\n  Rapports ecrits :")
    print(f"    corpus_unified.json (mis a jour)  -> {UNIFIED_JSON}")
    print(f"    corpus_audit_report.json          -> {AUDIT_JSON}")
    print(f"    corpus_audit_report.txt           -> {AUDIT_TXT}")
    print("="*60)

if __name__=="__main__":
    main()
