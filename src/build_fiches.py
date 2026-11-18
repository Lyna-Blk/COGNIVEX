"""
build_fiches.py — génère data/fiches_dci/*.md selon le modèle officiel du cours.

Usage :
    python src/build_metadata.py      # d'abord (et après pdf_to_text.py)
    python src/build_fiches.py        # fiches des DCI qui ont un dossier dans data/corpus
    python src/build_fiches.py --all  # + une fiche vide pour chaque DCI restante du fichier Excel

Les infos AUTOMATIQUES viennent de : Excel (ATC, noms commerciaux, formes, dosages),
metadata.json (documents, sources, dates) et key_info.json (laboratoires titulaires).
Les infos HUMAINES (résultat de la recherche ANPP, sources supplémentaires, remarques) sont dans
data/fiches_manual.json : modifiez ce fichier puis relancez le script.
"""
import argparse
import json
import re
import unicodedata

from corpus_utils import DATA, FICHES, KEY_DIR, METADATA, decode_name, norm, slug
from build_metadata import load_excel, excel_summary

MANUAL = DATA / "fiches_manual.json"
ACCENTS = {"GELULE": "GÉLULE", "COMPRIME": "COMPRIMÉ", "PELLICULE": "PELLICULÉ", "SECABLE": "SÉCABLE",
           "GRANULES": "GRANULÉS", "LIBERATION": "LIBÉRATION", "EFFERVESCENT": "EFFERVESCENT",
           "SOLUTION": "SOLUTION", "INJECTABLE": "INJECTABLE"}


def accent(txt):
    return " ".join(ACCENTS.get(w, w) for w in txt.split(" "))


def fr_date(iso):
    """'2025-09-12' -> '12/09/2025' ; autre texte ('Avril 2024') inchangé."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso or "")
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else (iso or "date non trouvée")


def titulaire_court(t):
    """'EG LABO - LABORATOIRES EUROGENERICS 21 rue...' -> 1re ligne utile."""
    if not t:
        return None
    t = re.split(r"\s{2,}|\s\d{1,3},?\s|\s\d{1,3}\s(?:rue|avenue|boulevard|place)", t, flags=re.I)[0]
    return t.strip(" ,-")


def build_fiche(dci_key, ex, corpus_entry, key_recs, manual):
    dci = ex["dci"]
    s = (corpus_entry or {}).get("excel") or excel_summary(ex)   # résumé Excel (+ ATC lus dans les RCP)
    man = manual.get(dci_key, {})
    anpp = man.get("anpp", {})
    L = []
    L.append(f"# DCI : {dci.upper()}")
    L.append(f"- **Code ATC :** {s['atc_excel'] or '[à compléter]'}")
    L.append("")
    pres = s["present_nomenclature"]
    L.append(f"- Présence dans la nomenclature MIPH : {pres if pres in ('oui', 'non') else 'à vérifier'}")
    L.append("- Version consultée et date : Nomenclature officielle (août 2026), selon le fichier Excel.")
    L.append("- Noms commerciaux, laboratoires, formes et dosages :")
    L.append("")
    seen = set()
    for l in ex["lignes"]:
        row = f"{l['nom']} — {accent(l['forme'])} — {l['dosage']}"
        if row not in seen:
            seen.add(row)
            L.append(f"  - {row}")
    if not seen:
        L.append("  - [à compléter]")
    labs = []
    for r in key_recs:
        if r["role"] == "rcp":
            t = titulaire_court((r.get("facts") or {}).get("titulaire_amm"))
            if t and t not in labs:
                labs.append(t)
    if labs:
        L.append("")
        L.append(f"  Laboratoires titulaires (d'après les RCP du corpus ; l'Excel ne les indique pas) : {' ; '.join(labs)}")
    L.append("")

    # ---------------------------------------------------------------- documents
    docs = [d for p in (corpus_entry or {}).get("products", []) for d in p["documents"]]
    L.append("## Documents de référence")

    def doc_line(label, d):
        src = d.get("source") or {}
        where = f"{src.get('name')} ({src.get('country')})"
        consulted = f", consulté le {fr_date(d['consulted_date'])}" if d.get("consulted_date") else ""
        return (f"- {label} : {d.get('product') or d['filename']}, {where}, "
                f"date du document : {fr_date(d.get('doc_date'))}{consulted}, fichier : `{d['filename']}`")

    for role, label in (("rcp", "RCP"), ("notice", "Notice")):
        sel = [d for d in docs if d["role"] == role]
        if sel:
            for d in sel:
                L.append(doc_line(label, d))
        else:
            L.append(f"- {label} : aucun document dans le corpus — à rechercher")
    for d in [d for d in docs if d["role"] == "article"]:
        L.append(doc_line("Autre document (article bon usage)", d))
    L.append("")

    # ---------------------------------------------------------------- ANPP
    q = anpp.get("requetes")
    if not q:                                         # DCI en majuscules, avec et sans accents
        plain = unicodedata.normalize("NFKD", dci.upper()).encode("ascii", "ignore").decode()
        q = dci.upper() if plain == dci.upper() else f"{dci.upper()} / {plain}"
    L.append("## Recherche ANPP")
    L.append(f"- Requêtes en majuscules : {q}")
    L.append(f"- Méthode et date : {anpp.get('methode') or '[à compléter : portail ANPP, date]'}")
    L.append(f"- Résultat : {anpp.get('rcp') or '[RCP trouvé / « document ANPP non trouvé »]'}")
    L.append(f"- Résultat : {anpp.get('notice') or '[Notice trouvée / « document ANPP non trouvé »]'}")
    L.append("")

    # ---------------------------------------------------------------- sources
    L.append("## Sources consultées")
    L.append("Au moins 3 sources distinctes, dont au moins une officielle.")
    L.append(f"- Nomenclature nationale des produits pharmaceutiques (MIPH, version août 2026) — présence, noms commerciaux, "
             f"formes, dosages, code ATC (via le fichier Excel du cours) — Algérie — [lien officiel à compléter] — août 2026")
    anpp_date = re.search(r"\d{2}/\d{2}/\d{4}", anpp.get("methode") or "")
    L.append(f"- ANPP — recherche du RCP et de la notice algériens ({anpp.get('rcp') or 'résultat à compléter'}) — Algérie — "
             f"https://anpp.dz — {anpp_date.group(0) if anpp_date else '[date à compléter]'}")
    groups = {}
    for d in docs:
        if d["role"] in ("rcp", "notice") and d.get("product") and d.get("source"):
            k = (d["source"]["name"], d["source"]["country"], d["source"].get("url"), d.get("doc_date"), d.get("consulted_date"))
            groups.setdefault(k, [])
            if d["product"] not in groups[k]:
                groups[k].append(d["product"])
    for (name, country, url, ddate, cdate), prods in groups.items():
        if country == "France":
            L.append(f"- {name} — RCP et notice de {' ; '.join(prods)} (mise à jour ANSM : {fr_date(ddate)}) — France — {url} — "
                     f"consulté le {fr_date(cdate)}")
        else:
            L.append(f"- {name} — RCP de {' ; '.join(prods)} (texte daté : {fr_date(ddate)}) — {country} — "
                     f"[provenance exacte et lien à confirmer : ANPP ou site du laboratoire] — [date de consultation à compléter]")
    for e in man.get("extra_sources", []):
        L.append(f"- {e['source']} — {e['information']} — {e['pays']} — {e['lien']} — {e['date']}")
    L.append("")

    # ---------------------------------------------------------------- précision
    L.append("## Précision")
    L.append("- Une source étrangère complète la source algérienne et ne la remplace pas.")
    dz = [d for d in docs if (d.get("source") or {}).get("country") == "Algérie" and d["role"] == "rcp"]
    fr = [d for d in docs if (d.get("source") or {}).get("country") == "France" and d["role"] == "rcp"]
    if dz:
        L.append(f"- En cas de différence, la source algérienne prévaut : RCP algérien disponible ("
                 f"{', '.join(sorted({d['product'] for d in dz if d.get('product')}))} — {dz[0]['source']['name'].split('— ')[-1]}, "
                 f"{fr_date(dz[0].get('doc_date'))}). Il prévaut sur les RCP français "
                 f"({', '.join(sorted({d['product'] for d in fr if d.get('product')})) or 'aucun'}). "
                 f"Différences à relever rubrique par rubrique : [à compléter après comparaison].")
    else:
        L.append("- En cas de différence, la source algérienne prévaut : aucun RCP ni notice algérien n'a été trouvé à ce jour, "
                 "donc aucune différence n'a pu être établie ; si un document ANPP est trouvé, il prévaudra.")
    L.append("- Les informations commerciales sont reprises du fichier Excel.")
    absent = sorted({d["product"] for d in docs if d["role"] in ("rcp", "notice") and d.get("in_nomenclature_algerienne") is False})
    if absent:
        L.append("- Produits du corpus absents de la nomenclature algérienne du fichier Excel (documents étrangers, "
                 "à titre complémentaire uniquement) : " + " ; ".join(absent) + ".")
    conf = s["atc_confirme"]
    if conf == "non":
        alt = " et ".join(s["atc_alternatif_excel"]) or "un autre code"
        L.append(f"- Code ATC à confirmer : la colonne « ATC confirmé » indique « non » et contient {alt}. Vérification nécessaire.")
    elif conf.startswith("aucun code"):
        L.append("- Le champ « ATC confirmé » indique qu'il n'y a pas de code confirmé.")
    rcp_atc = s.get("atc_dans_les_rcp") or []
    if rcp_atc and s["atc_excel"] not in rcp_atc:
        L.append(f"- Code ATC lu dans les RCP du corpus : {', '.join(rcp_atc)} (différent du code Excel {s['atc_excel']}) — à vérifier.")
    if len({l['nom'] for l in ex['lignes']}) == 1 and ex["lignes"]:
        L.append("- Une seule spécialité commerciale est listée dans le fichier Excel.")
    for n in man.get("notes", []):
        L.append(f"- {n}")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="créer aussi les fiches des DCI sans dossier corpus")
    args = ap.parse_args()

    meta = json.loads(METADATA.read_text(encoding="utf-8"))
    corpus = {norm(c["dci"]): c for c in meta["corpus"]}

    if args.all:
        excel = load_excel()
    else:
        excel = load_excel(set(corpus.keys()))

    manual = json.loads(MANUAL.read_text(encoding="utf-8")) if MANUAL.exists() else {}
    key_all = {}
    kf = KEY_DIR / "key_info.json"
    if kf.exists():
        key_all = {norm(k): v for k, v in json.loads(kf.read_text(encoding="utf-8"))["drugs"].items()}

    # noms de fichiers existants (on les garde pour ne pas casser le dépôt Git)
    names = {}
    for f in FICHES.glob("*.md"):
        m = re.match(r"#\s*DCI\s*:\s*(.+)", f.read_text(encoding="utf-8").splitlines()[0])
        if m:
            names[norm(m.group(1))] = f

    n = 0
    for k, ex in excel.items():
        if k not in corpus and not args.all:
            continue
        ce = corpus.get(k)
        txt = build_fiche(k, ex, ce, key_all.get(k, []), manual)
        old = names.get(k)
        target = FICHES / (decode_name(old.name) if old else f"{slug(ex['dci']).upper()}.md")
        FICHES.mkdir(exist_ok=True)
        target.write_text(txt, encoding="utf-8")
        if old and old.name != target.name and old.exists():
            old.unlink()                         # ancien nom '#U00c9' (artefact du zip) -> vrai nom
        n += 1
        print("  ", target.name)
    print(f"OK : {n} fiches écrites dans data/fiches_dci/")


if __name__ == "__main__":
    main()
