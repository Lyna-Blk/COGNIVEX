"""
pdf_to_text.py — PDF (RCP / Notice) -> texte propre + informations clés par médicament.

Usage :
    python src/pdf_to_text.py                       # tout le corpus
    python src/pdf_to_text.py --dci tramadol        # une seule DCI
    python src/pdf_to_text.py --focus amlodipine    # cherche aussi ce mot dans 4.4 / 4.5 / Notice

Sorties (dans data/) :
    corpus_text/<dci>/<produit>/<fichier>.txt            texte nettoyé, marqueurs  === PAGE n ===
    corpus_text/<dci>/<produit>/<fichier>.sections.json  sections + pages
    key_info/<dci>.md                                    fiche "informations clés" lisible
    key_info/key_info.json                               la même chose, en JSON
    chunks_sections.jsonl                                1 ligne = 1 section (prêt pour le chunking / RAG)

Le numéro de page = page du PDF (1 = première page du fichier PDF).
"""
import argparse
import json
import re
from datetime import datetime, timezone

from corpus_utils import (CORPUS, DATA, KEY_DIR, TEXT_DIR, IMAGE_EXT, clean_page, classify_pdf,
                          decode_name, norm, read_pdf_pages, slug)

# ------------------------------------------------------------------ sections RCP
# clé -> (numéro de rubrique, début de titre normalisé)
RCP_SECTIONS = {
    "1":   ["denomination"],
    "2":   ["composition"],
    "3":   ["forme pharmaceutique"],
    "4.1": ["indications"],
    "4.2": ["posologie"],
    "4.3": ["contre"],
    "4.4": ["mises en garde"],
    "4.5": ["interactions"],
    "4.6": ["fertilite"],
    "4.7": ["effets sur l aptitude"],
    "4.8": ["effets indesirables"],
    "4.9": ["surdosage"],
    "5.1": ["proprietes pharmacodynamiques"],
    "5.2": ["proprietes pharmacocinetiques"],
    "5.3": ["donnees de securite"],
    "6.1": ["liste des excipients"],
    "6.2": ["incompatibilites"],
    "6.3": ["duree de conservation"],
    "6.4": ["precautions particulieres de conservation"],
    "6.5": ["nature et contenu"],
    "6.6": ["precautions particulieres d elimination"],
    "7":   ["titulaire", "conditions de delivrance"],          # FR : titulaire AMM / DZ : conditions de délivrance
    "8":   ["numero", "informations administratives"],         # FR : n° AMM / DZ : infos administratives
    "8.1": ["nom et adresse du detenteur"],                    # DZ : détenteur de la décision d'enregistrement
    "8.4": ["numero de la decision"],                          # DZ : n° d'enregistrement
    "8.5": ["date de mise a jour"],                            # DZ : date de mise à jour
    "9":   ["date de premiere"],
    "10":  ["date de mise a jour"],
}
RCP_LABELS = {
    "1": "Dénomination", "2": "Composition", "3": "Forme pharmaceutique",
    "4.1": "Indications thérapeutiques", "4.2": "Posologie et mode d'administration",
    "4.3": "Contre-indications", "4.4": "Mises en garde spéciales et précautions d'emploi",
    "4.5": "Interactions médicamenteuses", "4.6": "Fertilité, grossesse et allaitement",
    "4.7": "Aptitude à conduire", "4.8": "Effets indésirables", "4.9": "Surdosage",
    "5.1": "Propriétés pharmacodynamiques (classe, code ATC)", "5.2": "Propriétés pharmacocinétiques",
    "5.3": "Sécurité préclinique", "6.1": "Excipients", "6.2": "Incompatibilités",
    "6.3": "Durée de conservation", "6.4": "Conditions de conservation", "6.5": "Conditionnement",
    "6.6": "Précautions d'élimination", "7": "Titulaire AMM (FR) / Conditions de délivrance (DZ)", "8": "Numéro(s) d'AMM (FR) / Informations administratives (DZ)",
    "9": "Date de première autorisation", "10": "Date de mise à jour du texte",
    "8.1": "Détenteur de la décision d'enregistrement (RCP algérien)",
    "8.4": "N° de la décision d'enregistrement (RCP algérien)",
    "8.5": "Date de mise à jour du texte (RCP algérien)",
}
# rubriques à mettre dans la fiche "informations clés" (ordre d'affichage)
KEY_RCP = ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.8", "4.9", "5.1", "6.1", "6.4", "7", "8", "8.1", "8.4", "8.5", "10"]
KEY_RCP_REQUIRED = ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.8", "4.9", "5.1", "6.1", "6.4"]

# ------------------------------------------------------------------ sections Notice
NOTICE_SECTIONS = [
    ("1", r"^1\.\s*qu", "1. Qu'est-ce que le médicament et indications"),
    ("2", r"^2\.\s*quelles sont les informations", "2. Avant de prendre (contre-indications, précautions, interactions, grossesse)"),
    ("3", r"^3\.\s*comment (prendre|utiliser|administrer)", "3. Comment prendre (posologie)"),
    ("4", r"^4\.\s*quels sont les effets", "4. Effets indésirables"),
    ("5", r"^5\.\s*comment conserver", "5. Conservation"),
    ("6", r"^6\.\s*contenu", "6. Contenu de l'emballage / titulaire / fabricant"),
]
KEY_NOTICE = ["1", "2", "3", "4", "5"]

PED_WORDS = re.compile(r"(p[ée]diatri|enfant|adolescent|nourrisson|nouveau-n[ée]|\b1[0-8] ans\b|âgé[es]? de moins de)", re.I)


# ------------------------------------------------------------------ extraction
def write_text(pages_clean, out_txt):
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    with open(out_txt, "w", encoding="utf-8") as f:
        for i, lines in enumerate(pages_clean, 1):
            f.write(f"=== PAGE {i} ===\n")
            f.write("\n".join(lines) + "\n\n")


def split_rcp(pages_clean):
    """Découpe un RCP en rubriques. Retourne {clé: {"title","page_start","page_end","text"}}."""
    sections, cur = {}, None
    for pno, lines in enumerate(pages_clean, 1):
        for line in lines:
            m = re.match(r"^(\d{1,2}(?:\.\d{1,2})?)\.?\s+(\S.*)$", line)
            if m:
                num, title = m.group(1), norm(m.group(2))
                key = num if num in RCP_SECTIONS else None
                if key and key not in sections and any(title.startswith(pf) for pf in RCP_SECTIONS[key]):
                    cur = key
                    sections[cur] = {"title": line, "page_start": pno, "page_end": pno, "lines": []}
                    continue
            if cur:
                sections[cur]["lines"].append(line)
                sections[cur]["page_end"] = pno
    for s in sections.values():
        s["text"] = "\n".join(s.pop("lines")).strip()
    return sections


def fold(line):
    """minuscule + sans accents + apostrophes normalisées (on GARDE la ponctuation)."""
    import unicodedata
    t = unicodedata.normalize("NFKD", line.replace("’", "'").replace("\u00a0", " "))
    return "".join(c for c in t if not unicodedata.combining(c)).lower().strip()


def split_notice(pages_clean):
    """Les notices BDPM listent d'abord les 6 titres (table des matières) puis les vrais titres
    en MAJUSCULES : si une section a < 8 lignes quand son titre revient, on la remplace."""
    sections, cur = {}, None
    for pno, lines in enumerate(pages_clean, 1):
        for line in lines:
            nl = fold(line)
            hit = None
            for key, rx, _ in NOTICE_SECTIONS:
                if re.match(rx, nl):
                    hit = key
                    break
            if hit and (hit not in sections or len(sections[hit]["lines"]) < 8):
                cur = hit
                sections[cur] = {"title": line, "page_start": pno, "page_end": pno, "lines": []}
                continue
            if cur:
                sections[cur]["lines"].append(line)
                sections[cur]["page_end"] = pno
    for s in sections.values():
        ls = s.pop("lines")
        for _ in range(2):                                   # titre sur plusieurs lignes : "... ET DANS QUELS / CAS EST-IL UTILISE ?"
            if ls and not s["title"].rstrip().endswith(("?", ".")) and len(ls[0]) < 80:
                s["title"] += " " + ls.pop(0)
        s["text"] = "\n".join(ls).strip()
    return sections


def paragraphs_with(text, regex, max_n=8):
    """Phrases/paragraphes de `text` qui contiennent regex (pour enfants, focus, etc.)."""
    flat = re.sub(r"\n(?![•\-–])", " ", text)
    parts = re.split(r"(?<=[.;:])\s+(?=[A-ZÉÈÀ•\-–])", flat)
    hits = [p.strip() for p in parts if regex.search(p)]
    return hits[:max_n]


def quick_facts(rcp_sections, full_text, first_page):
    facts = {}
    s51 = rcp_sections.get("5.1", {}).get("text", "")
    m = re.search(r"\bATC\s*:?\s*([A-Z]\d{2}[A-Z]{2}\d{2})", s51, re.I) or \
        re.search(r"\bATC\s*:?\s*([A-Z]\d{2}[A-Z]{2}\d{2})", full_text, re.I)
    facts["code_atc_rcp"] = m.group(1).upper() if m else None
    m = re.search(r"Classe pharmaco[- ]?th[ée]rapeutique\s*:?\s*([^\n]+?)(?:,\s*code ATC|\s*-\s*code ATC|$)", s51 or full_text, re.I | re.M)
    facts["classe_pharmacotherapeutique"] = m.group(1).strip(" .,") if m else None
    s2 = rcp_sections.get("2", {}).get("text", "")
    m = re.search(r"Excipients? à effet notoire\s*:?\s*([^\n]+(?:\n[^\n]+)?)", s2)
    facts["excipients_effet_notoire"] = m.group(1).replace("\n", " ").strip() if m else None
    t = rcp_sections.get("8.1", {}).get("text") or rcp_sections.get("7", {}).get("text", "")
    facts["titulaire_amm"] = t.splitlines()[0].strip() if t else None
    facts["titulaire_amm_complet"] = " ".join(t.splitlines()[:3]).strip() if t else None
    n = rcp_sections.get("8.4", {}).get("text") or rcp_sections.get("8", {}).get("text", "")
    facts["numero_amm"] = " ".join(n.splitlines()[:2]).strip() if n else None
    return facts


def process_pdf(path, dci_name, focus_terms):
    rel = path.relative_to(CORPUS)
    parts = [decode_name(p) for p in rel.parts]
    pages_raw, needs_ocr = read_pdf_pages(path)
    pages_clean = [clean_page(p) for p in pages_raw]
    full = "\n".join("\n".join(p) for p in pages_clean)
    role, source, title, doc_date, consulted, bdpm_up = classify_pdf(pages_raw[0] if pages_raw else "",
                                                                      path.name, "\n".join(pages_raw))
    out_dir = TEXT_DIR / slug(dci_name) / "/".join(slug(x) for x in parts[1:-1]) if len(parts) > 2 else TEXT_DIR / slug(dci_name)
    out_txt = out_dir / (decode_name(path.stem) + ".txt")
    write_text(pages_clean, out_txt)

    if role == "rcp":
        sections = split_rcp(pages_clean)
    elif role == "notice":
        sections = split_notice(pages_clean)
    else:
        sections = {}
    with open(out_txt.with_suffix(".sections.json"), "w", encoding="utf-8") as f:
        json.dump({k: {kk: vv for kk, vv in v.items()} for k, v in sections.items()}, f, ensure_ascii=False, indent=1)

    rec = {
        "dci": dci_name, "filename": decode_name(path.name), "role": role, "product": title,
        "source": source, "doc_date": doc_date, "consulted_date": consulted,
        "pages": len(pages_raw), "chars": len(full), "needs_ocr": needs_ocr,
        "text_file": str(out_txt.relative_to(DATA)).replace("\\", "/"),
        "sections_found": sorted(sections, key=lambda x: [int(n) for n in x.split('.')]),
        "relative_path": "corpus/" + "/".join(parts),
    }
    key = {}
    if role == "rcp":
        rec["facts"] = quick_facts(sections, full, pages_raw[0] if pages_raw else "")
        for k in KEY_RCP:
            if k in sections:
                key[k] = {"label": RCP_LABELS[k], **{kk: sections[k][kk] for kk in ("page_start", "page_end", "text")}}
        # points enfants / adolescents
        ped = []
        for k in ("4.2", "4.3", "4.4"):
            if k in sections:
                for h in paragraphs_with(sections[k]["text"], PED_WORDS, 5):
                    ped.append({"rubrique": k, "page": sections[k]["page_start"], "texte": h})
        rec["pediatrie"] = ped
    elif role == "notice":
        for k in KEY_NOTICE:
            if k in sections:
                label = [l for kk, _, l in NOTICE_SECTIONS if kk == k][0]
                key[k] = {"label": label, **{kk: sections[k][kk] for kk in ("page_start", "page_end", "text")}}
        ped = []
        if "2" in sections:
            for h in paragraphs_with(sections["2"]["text"], PED_WORDS, 5):
                ped.append({"rubrique": "2", "page": sections["2"]["page_start"], "texte": h})
        rec["pediatrie"] = ped
    rec["key_sections"] = key

    if focus_terms and sections:
        rx = re.compile("|".join(re.escape(t) for t in focus_terms), re.I)
        hits = []
        for k, s in sections.items():
            for h in paragraphs_with(s["text"], rx, 4):
                hits.append({"rubrique": k, "page": s["page_start"], "texte": h})
        rec["focus_hits"] = hits
    return rec, sections


# ------------------------------------------------------------------ rendu markdown
def render_md(dci, recs):
    L = [f"# Informations clés — {dci.upper()}", "",
         f"_Généré automatiquement le {datetime.now().strftime('%d/%m/%Y')} depuis les PDF du corpus. "
         "Les numéros de page sont ceux du fichier PDF. Toujours vérifier la citation dans le PDF avant de l'utiliser._", ""]
    for r in recs:
        if r["role"] not in ("rcp", "notice"):
            continue
        L += [f"## {r['role'].upper()} — {r.get('product') or r['filename']}", "",
              f"- Fichier : `{r['filename']}` ({r['pages']} p.)",
              f"- Source : {r['source'].get('name')} — {r['source'].get('country')}",
              f"- Date du document : {r.get('doc_date') or 'non trouvée'} | consulté le : {r.get('consulted_date') or 'non trouvé'}"]
        if r.get("needs_ocr"):
            L.append("- ⚠️ Certaines pages n'ont pas de texte : OCR nécessaire (pytesseract).")
        f = r.get("facts")
        if f:
            L.append(f"- Code ATC (RCP 5.1) : {f.get('code_atc_rcp') or 'non trouvé'} | Classe : {f.get('classe_pharmacotherapeutique') or 'non trouvée'}")
            if f.get("excipients_effet_notoire"):
                L.append(f"- Excipient(s) à effet notoire : {f['excipients_effet_notoire']}")
            if f.get("titulaire_amm"):
                L.append(f"- Titulaire AMM : {f['titulaire_amm']}")
            if f.get("numero_amm"):
                L.append(f"- N° AMM : {f['numero_amm']}")
        missing = [k for k in (KEY_RCP_REQUIRED if r["role"] == "rcp" else KEY_NOTICE) if k not in r["key_sections"]]
        if missing:
            L.append(f"- ⚠️ Rubriques non détectées : {', '.join(missing)} (vérifier le fichier .txt)")
        L.append("")
        if r.get("pediatrie"):
            L += ["### Points enfants / adolescents (à relire dans la source)", ""]
            for p in r["pediatrie"]:
                L.append(f"- (rubrique {p['rubrique']}, p. {p['page']}) {p['texte']}")
            L.append("")
        if r.get("focus_hits"):
            L += ["### Mots-clés suivis (--focus)", ""]
            for p in r["focus_hits"]:
                L.append(f"- (rubrique {p['rubrique']}, p. {p['page']}) {p['texte']}")
            L.append("")
        for k, s in r["key_sections"].items():
            pg = f"p. {s['page_start']}" + (f"–{s['page_end']}" if s['page_end'] != s['page_start'] else "")
            head = s["label"] if r["role"] == "notice" else f"{k}. {s['label']}"
            L += [f"### {head}  ({pg})", "", s["text"] or "_(vide)_", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dci", help="traiter une seule DCI (nom du dossier, accents optionnels)")
    ap.add_argument("--focus", nargs="*", default=[], help="mots à repérer (ex: amlodipine Mibral)")
    args = ap.parse_args()

    KEY_DIR.mkdir(parents=True, exist_ok=True)
    all_key, chunks = {}, []
    for dci_dir in sorted(p for p in CORPUS.iterdir() if p.is_dir()):
        dci_name = decode_name(dci_dir.name)
        if args.dci and norm(args.dci) != norm(dci_name):
            continue
        recs = []
        for pdf in sorted(dci_dir.rglob("*.pdf")):
            print(f"  {dci_name:35s} {decode_name(pdf.name)}")
            rec, sections = process_pdf(pdf, dci_name, args.focus)
            recs.append(rec)
            for k, s in sections.items():
                chunks.append({"dci": dci_name, "product": rec["product"], "doc_role": rec["role"],
                               "filename": rec["filename"], "source": rec["source"]["name"],
                               "country": rec["source"]["country"], "doc_date": rec["doc_date"],
                               "consulted_date": rec["consulted_date"], "section": k,
                               "section_title": s["title"], "page_start": s["page_start"],
                               "page_end": s["page_end"], "text": s["text"]})
        all_key[dci_name] = recs
        (KEY_DIR / f"{slug(dci_name)}.md").write_text(render_md(dci_name, recs), encoding="utf-8")

    with open(KEY_DIR / "key_info.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(), "drugs": all_key},
                  f, ensure_ascii=False, indent=1)
    with open(DATA / "chunks_sections.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"\nOK : {sum(len(v) for v in all_key.values())} PDF, {len(chunks)} sections -> data/key_info, data/corpus_text, data/chunks_sections.jsonl")


if __name__ == "__main__":
    main()
