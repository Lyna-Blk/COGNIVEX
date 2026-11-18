"""
build_metadata.py — génère data/metadata.json à partir des DCI présentes dans le Corpus.

Usage :
    python src/build_metadata.py

Le script :
  1. parcourt uniquement data/corpus/<dci>/[<produit>/]fichiers
  2. lit dans Excel uniquement les lignes correspondant aux DCI du Corpus
  3. extrait les métadonnées des documents
  4. calcule les statistiques uniquement sur les DCI du Corpus
  5. ne génère aucun warning et aucune liste de DCI restantes
"""

import json
import re
from datetime import datetime, timezone

import openpyxl

from corpus_utils import (
    CORPUS, DATA, EXCEL, FICHES, IMAGE_EXT, KEY_DIR, METADATA, TEXT_DIR,
    brand_in_nomenclature, classify_pdf, decode_name, norm, read_pdf_pages,
    sha256, slug,
)

NOMENCLATURE_VERSION = (
    "Nomenclature officielle MIPH (août 2026), selon le fichier Excel"
)
ATC_RE = re.compile(r"[A-Z]\d{2}[A-Z]{2}\d{2}")


# ------------------------------------------------------------------ Excel

def txt(v):
    """Convertit une cellule Excel en texte propre."""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


def load_excel(corpus_dci):
    """
    Lit uniquement les lignes Excel dont la DCI existe dans le Corpus.
    corpus_dci contient les clés normalisées des dossiers du Corpus.
    """
    wb = openpyxl.load_workbook(EXCEL, data_only=True)
    ws = wb.active
    out = {}

    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r[2]:
            continue

        dci = str(r[2]).strip()
        key = norm(dci)

        # Ignore totalement les DCI qui ne sont pas dans le Corpus.
        if key not in corpus_dci:
            continue

        e = out.setdefault(key, {
            "dci": dci,
            "classe": r[1],
            "atc_excel": None,
            "atc_confirme_brut": None,
            "present_nomenclature_brut": None,
            "lignes": [],
            "remarques": set(),
        })

        atc = txt(r[3])
        e["atc_excel"] = e["atc_excel"] or atc or None

        conf = str(r[4]).strip() if r[4] is not None else ""
        e["atc_confirme_brut"] = e["atc_confirme_brut"] or conf or None

        e["present_nomenclature_brut"] = (
            e["present_nomenclature_brut"]
            or (str(r[5]).strip() if r[5] else None)
        )

        if r[6]:
            e["lignes"].append({
                "nom": str(r[6]).strip(),
                "forme": txt(r[7]),
                "dosage": txt(r[8]),
                "sources": r[9],
                "remarque": r[10],
            })

        if r[10]:
            e["remarques"].add(str(r[10]).strip())

    return out


def excel_summary(e):
    """Construit le résumé Excel d'une DCI présente dans le Corpus."""
    conf = (e["atc_confirme_brut"] or "").strip()
    alt = ATC_RE.findall(conf.upper())

    if conf.lower().startswith("oui"):
        statut = "oui"
    elif conf.lower().startswith("non"):
        statut = "non"
    elif not conf:
        statut = "non renseigné"
    else:
        statut = "aucun code (note Excel : " + conf + ")"

    noms = []
    for ligne in e["lignes"]:
        if ligne["nom"] not in noms:
            noms.append(ligne["nom"])

    return {
        "classe": e["classe"],
        "atc_excel": (e["atc_excel"] or "").strip() or None,
        "atc_confirme": statut,
        "atc_alternatif_excel": alt,
        "present_nomenclature": (
            (e["present_nomenclature_brut"] or "").strip().lower() or None
        ),
        "nb_lignes_excel": len(e["lignes"]),
        "noms_commerciaux": noms,
        "formes": sorted({
            ligne["forme"] for ligne in e["lignes"] if ligne["forme"]
        }),
        "dosages": sorted({
            ligne["dosage"] for ligne in e["lignes"] if ligne["dosage"]
        }),
        "remarques_excel": sorted(e["remarques"]),
    }


# ------------------------------------------------------------------ Documents

def doc_record(path, dci_dir, brands):
    """Construit les métadonnées d'un seul fichier du Corpus."""
    rel_parts = [
        decode_name(part)
        for part in path.relative_to(CORPUS).parts
    ]
    ext = path.suffix.lower()

    rec = {
        "filename": decode_name(path.name),
        "relative_path": "corpus/" + "/".join(rel_parts),
        "type": ext.lstrip("."),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }

    if ext in IMAGE_EXT:
        rec.update({
            "role": "image",
            "product": None,
            "source": None,
            "doc_date": None,
            "consulted_date": None,
        })
        return rec

    if ext != ".pdf":
        rec.update({"role": "autre"})
        return rec

    pages, needs_ocr = read_pdf_pages(path, ocr_fallback=False)
    full = "\n".join(pages)

    role, source, title, doc_date, consulted, bdpm_up = classify_pdf(
        pages[0] if pages else "",
        path.name,
        full,
    )

    stem_txt = TEXT_DIR / slug(decode_name(dci_dir.name))
    txt_candidates = (
        list(stem_txt.rglob(decode_name(path.stem) + ".txt"))
        if stem_txt.exists()
        else []
    )

    rec.update({
        "role": role,
        "product": title,
        "pages": len(pages),
        "chars": len(full),
        "needs_ocr": needs_ocr,
        "source": source,
        "doc_date": doc_date,
        "consulted_date": consulted,
        "bdpm_last_update": bdpm_up,
        "text_file": (
            str(txt_candidates[0].relative_to(DATA)).replace("\\", "/")
            if txt_candidates else None
        ),
        "in_nomenclature_algerienne": (
            brand_in_nomenclature(title, brands)
            if role in ("rcp", "notice")
            else None
        ),
    })

    return rec


# ------------------------------------------------------------------ Main

def main():
    # Récupère d'abord uniquement les dossiers DCI réellement présents.
    dci_dirs = sorted(
        p for p in CORPUS.iterdir()
        if p.is_dir()
    )

    corpus_keys = {norm(decode_name(p.name)) for p in dci_dirs}

    # Excel est filtré : les autres médicaments ne sont pas traités.
    excel = load_excel(corpus_keys)

    existing_fiches = {}
    for fiche in FICHES.glob("*.md"):
        first = (
            fiche.read_text(encoding="utf-8").splitlines()[0]
            if fiche.stat().st_size else ""
        )
        match = re.match(r"#\s*DCI\s*:\s*(.+)", first)
        if match:
            key = norm(match.group(1).replace("+", " + "))
            existing_fiches[key] = (
                "fiches_dci/" + decode_name(fiche.name)
            )

    key_info = {}
    key_info_path = KEY_DIR / "key_info.json"
    if key_info_path.exists():
        key_info = json.loads(
            key_info_path.read_text(encoding="utf-8")
        ).get("drugs", {})

    corpus = []

    totals = {
        "documents": 0,
        "rcp": 0,
        "notice": 0,
        "article": 0,
        "image": 0,
        "autre": 0,
        "product_folders": 0,
    }

    for dci_dir in dci_dirs:
        dci = decode_name(dci_dir.name)
        key = norm(dci)

        ex = excel.get(key)
        summ = excel_summary(ex) if ex else {}
        brands = summ.get("noms_commerciaux", [])

        # Regroupe les fichiers par sous-dossier produit.
        groups = {}
        for file_path in sorted(
            p for p in dci_dir.rglob("*") if p.is_file()
        ):
            rel = file_path.relative_to(dci_dir)
            group = (
                decode_name(rel.parts[0])
                if len(rel.parts) > 1
                else None
            )
            groups.setdefault(group, []).append(file_path)

        products = []
        counts = {
            "rcp": 0,
            "notice": 0,
            "article": 0,
            "image": 0,
            "autre": 0,
        }

        for group, files in groups.items():
            docs = [
                doc_record(file_path, dci_dir, brands)
                for file_path in files
            ]

            for doc in docs:
                role = doc["role"]
                counts[role] = counts.get(role, 0) + 1

            products.append({
                "folder": group,
                "documents": docs,
            })

            if group is not None:
                totals["product_folders"] += 1

        all_docs = [
            doc
            for product in products
            for doc in product["documents"]
        ]

        rcps = [doc for doc in all_docs if doc["role"] == "rcp"]
        notices = [doc for doc in all_docs if doc["role"] == "notice"]

        algerian_docs = [
            doc for doc in all_docs
            if doc.get("source")
            and doc["source"].get("country") == "Algérie"
        ]

        foreign_docs = [
            doc for doc in all_docs
            if doc.get("source")
            and doc["source"].get("country") == "France"
        ]

        # Compare l'ATC Excel avec les codes lus dans les RCP.
        atc_rcp = sorted({
            (record.get("facts") or {}).get("code_atc_rcp")
            for record in key_info.get(dci, [])
            if record.get("role") == "rcp"
        } - {None})

        if summ:
            summ["atc_dans_les_rcp"] = atc_rcp
            summ["atc_excel_egal_rcp"] = (
                summ["atc_excel"] in atc_rcp
                if atc_rcp else None
            )

        corpus.append({
            "dci": dci,
            "dci_slug": slug(dci),
            "relative_path": f"corpus/{dci}",
            "fiche_dci": existing_fiches.get(key),
            "excel": summ,
            "counts": counts,
            "coverage": {
                "has_rcp": bool(rcps),
                "has_notice": bool(notices),
                "has_algerian_document": bool(algerian_docs),
                "has_foreign_document": bool(foreign_docs),
                "algerian_documents": [
                    doc["filename"] for doc in algerian_docs
                ],
            },
            "products": products,
        })

        for doc in all_docs:
            totals["documents"] += 1
            role = doc["role"]
            totals[role] = totals.get(role, 0) + 1

    meta = {
        "_meta": {
            "project": "Cognivex — RCR Projet 2",
            "schema_version": "2.1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "src/build_metadata.py",
            "corpus_root": "data/corpus",
            "nomenclature": {
                "file": "data/Liste 40 medicaments.xlsx",
                "version": NOMENCLATURE_VERSION,
            },
            "total_dci_in_corpus": len(corpus),
            "totals": totals,
            "note": (
                "Seules les DCI présentes dans data/corpus sont traitées. "
                "Les autres DCI du fichier Excel sont ignorées."
            ),
        },
        "corpus": corpus,
    }

    METADATA.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA, "w", encoding="utf-8") as file:
        json.dump(meta, file, ensure_ascii=False, indent=2)

    print(
        f"OK : {len(corpus)} DCI dans le Corpus, "
        f"{totals['documents']} fichiers traités."
    )


if __name__ == "__main__":
    main()
