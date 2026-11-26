import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

from rag_config import (
    CORPUS_DIR,
    OCR_DIR,
    ROOT,
    REFERENCE_XLSX,
    CHUNKS_FILE as OUTPUT_FILE,
    MAX_WORDS,
    OVERLAP_WORDS,
    canon_dci,
    nettoyer_texte,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

NOMENCLATURE_VERSION = "nomenclature MIPH (août 2026)"
PAGE_OCR_INCONNUE = "OCR — pagination non précisée"

_FRONT_MATTER = re.compile(r"\A\s*---\s*\n.*?\n---\s*\n", re.S)
_TITRE_PAGE = re.compile(r"^##\s*Page\s+(\d+)\s*$", re.M)
_SECTION = re.compile(
    r"^\s*(?:#{1,6}\s*)?(\d{1,2}(?:\.\d{1,2}){0,2})\s*[.)]?\s+([A-Za-zÀ-ÿ][^\n]{2,90}?)\s*$"
)
_MARQUE = "§SEC§"


#  découpage 
def _marquer_sections(texte: str, sections: list[str]) -> str:
    """Insère un jeton sans espace devant chaque titre de section (4.6 Grossesse...).
    Le jeton survit au nettoyage du texte ; il est retiré ensuite par decouper_page()."""
    lignes = []
    for ligne in texte.splitlines():
        m = _SECTION.match(ligne)
        if m and "...." not in ligne:
            numero, titre = m.group(1), m.group(2).strip().rstrip(" :")  
            sous_section = "." in numero
            lettres = [c for c in titre if c.isalpha()]
            majuscules = sum(c.isupper() for c in lettres) / max(len(lettres), 1)
            chiffres = sum(c.isdigit() for c in titre)
            titre_ok = titre[0].isupper() and not titre.endswith((".", ",", ";", ":")) and chiffres <= 3
           
            if titre_ok and len(titre) >= 3 and (
                (sous_section and int(numero.split(".")[0]) <= 12) or
                (not sous_section and len(titre) <= 80 and int(numero) <= 12 and majuscules >= 0.7)
            ):
                sections.append(f"{numero} {titre}"[:90])
                ligne = f"{_MARQUE}{len(sections) - 1}§ {ligne}"
        lignes.append(ligne)
    return "\n".join(lignes)


def decouper_page(texte: str, section_initiale: str = ""):
    """Retourne ([(section, passage), ...], section_finale)."""
    sections: list[str] = []
    texte = re.sub(r"^\s*-{3,}\s*$", " ", texte, flags=re.M)  
    texte = nettoyer_texte(_marquer_sections(texte, sections))

    mots, secs, courante = [], [], section_initiale
    for jeton in texte.split():
        if jeton.startswith(_MARQUE):
            courante = sections[int(jeton[len(_MARQUE):].rstrip("§"))]
            continue
        mots.append(jeton)
        secs.append(courante)

    chunks, debut = [], 0
    while debut < len(mots):
        fin = min(debut + MAX_WORDS, len(mots))
        morceau = " ".join(mots[debut:fin])
        if morceau.strip():
            chunks.append((secs[debut], morceau))
        if fin == len(mots):
            break
        debut = fin - OVERLAP_WORDS
    return chunks, courante


def split_text(text):
    """Compatibilité avec l'ancienne version : liste de passages sans section."""
    return [morceau for _, morceau in decouper_page(text)[0]]


#  lecture des documents
def document_type(filename):
    name = filename.lower()
    if "rcp" in name:
        return "RCP"
    if "notice" in name:
        return "Notice"
    return "Autre document PDF"


def lire_markdown(chemin: Path):
    """Markdown OCR -> [(page, texte)] ; la page vient des titres « ## Page N » si présents."""
    texte = chemin.read_text(encoding="utf-8").replace("\r\n", "\n")
    texte = _FRONT_MATTER.sub("", texte, count=1).strip()
    titres = list(_TITRE_PAGE.finditer(texte))
    if not titres:
        return [(PAGE_OCR_INCONNUE, texte)] if texte else []
    pages = []
    for i, t in enumerate(titres):
        fin = titres[i + 1].start() if i + 1 < len(titres) else len(texte)
        pages.append((t.group(1), texte[t.end():fin].strip()))
    return pages


def lire_pdf(chemin: Path):
    reader = PdfReader(str(chemin))
    return [(str(n), page.extract_text() or "") for n, page in enumerate(reader.pages, start=1)]


def lister_documents():
    """Un document = un fichier source (PDF, ou Markdown sans PDF). Retourne
    {chemin relatif au corpus sans extension: {'pdf': Path|None, 'md': Path|None}}."""
    docs: dict[str, dict] = {}

    def cle(chemin: Path, racine: Path) -> str:
        return chemin.relative_to(racine).with_suffix("").as_posix()

    for pdf in CORPUS_DIR.rglob("*.pdf"):
        docs.setdefault(cle(pdf, CORPUS_DIR), {})["pdf"] = pdf
    for md in CORPUS_DIR.rglob("*.md"):            # sources DwaDZ saisies à la main
        docs.setdefault(cle(md, CORPUS_DIR), {})["md_corpus"] = md
    if OCR_DIR.is_dir():
        for md in OCR_DIR.rglob("*.md"):           # sorties de ocr_pipeline.py
            docs.setdefault(cle(md, OCR_DIR), {})["md"] = md
    return dict(sorted(docs.items()))


#  passages « nomenclature » 
def _empaqueter(entete: str, lignes: list[str]) -> list[str]:
    """Regroupe des lignes en passages de MAX_WORDS mots au plus ; l'en-tête est répété."""
    passages, courant = [], []
    budget = MAX_WORDS - len(entete.split())
    taille = 0
    for ligne in lignes:
        n = len(ligne.split())
        if courant and taille + n > budget:
            passages.append(entete + " " + " ".join(courant))
            courant, taille = [], 0
        courant.append(ligne)
        taille += n
    if courant:
        passages.append(entete + " " + " ".join(courant))
    return passages


def chunks_nomenclature(noms_dci_dossier: dict[str, str]):
    """Passages construits à partir de la table nom commercial -> DCI (noms_commerciaux.py)."""
    from noms_commerciaux import construire_table, ecrire_table

    table = construire_table()
    ecrire_table(table) 
    fichier = REFERENCE_XLSX.relative_to(ROOT).as_posix()
    records = []

    par_dci: dict[str, list[dict]] = {}
    for r in table:
        par_dci.setdefault(r["dci_normalisee"], []).append(r)

    for canon, noms in par_dci.items():
        dci = noms_dci_dossier.get(canon) or noms[0]["dci"].upper()
        atc, classe = noms[0]["code_atc"], noms[0]["classe"]
        officiel = noms[0]["niveau_source"].startswith("officielle")
        source = NOMENCLATURE_VERSION if officiel else "source secondaire (Pharm'Net / DwaDZ)"

        for r in noms:
            labo = f" Laboratoire : {r['laboratoire']}." if r["laboratoire"] else ""
            texte = (
                f"{r['nom_commercial']} est un nom commercial de la DCI {r['dci']} "
                f"(dénomination commune internationale : {r['dci']}). "
                f"Nomenclature pharmaceutique algérienne : {r['nom_commercial']}, DCI {r['dci']}, "
                f"formes et dosages : {r['formes_dosages'] or 'non précisés'}.{labo} "
                f"Code ATC {atc}. Classe : {classe}. Source : {source}."
            )
            records.append({
                "chunk_id": "nomenclature_nom_" + re.sub(r"[^A-Za-z0-9]+", "_", r["nom_normalise"]),
                "dci": dci, "brand": r["nom_commercial"], "document_type": "Nomenclature",
                "file_path": fichier, "page": f"nom commercial {r['nom_commercial']}",
                "section": "Nom commercial → DCI", "text": texte,
            })

        groupes: dict[str, list[str]] = {}
        for r in noms:
            for fd in (r["formes_dosages"].split(" | ") if r["formes_dosages"] else ["non précisé"]):
                groupes.setdefault(fd, []).append(r["nom_commercial"])
        lignes = [f"{fd.upper()} : {', '.join(sorted(set(n)))}." for fd, n in sorted(groupes.items())]
        entete = (
            f"Nomenclature pharmaceutique algérienne — DCI {noms[0]['dci']} (code ATC {atc}, classe {classe}). "
            f"Liste des formes pharmaceutiques, dosages et noms commerciaux enregistrés ({source}) :"
        )
        for numero, texte in enumerate(_empaqueter(entete, lignes), start=1):
            records.append({
                "chunk_id": f"nomenclature_dci_{re.sub(r'[^A-Za-z0-9]+', '_', canon)}_{numero}",
                "dci": dci, "brand": "", "document_type": "Nomenclature",
                "file_path": fichier, "page": f"DCI {noms[0]['dci']}",
                "section": "Formes, dosages et noms commerciaux", "text": texte,
            })
    return records


#  programme principal 
def main():
    if not CORPUS_DIR.is_dir():
        raise FileNotFoundError(f"Dossier corpus introuvable : {CORPUS_DIR}")

    documents = lister_documents()
    if not documents:
        print("Aucun document trouvé dans data/corpus ni data/processed_corpus.")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    noms_dci_dossier = {
        canon_dci(d.name): d.name.upper() for d in CORPUS_DIR.iterdir() if d.is_dir()
    }

    total = 0
    stats = {"markdown": 0, "pdf": 0, "illisibles": 0}

    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        for cle, sources in documents.items():
            parties = Path(cle).parts
            dci = parties[0].upper()
            brand = parties[1] if len(parties) >= 3 else ""
            if brand.lower().startswith("documents_complementaires"):
                brand = ""

            md = sources.get("md") or sources.get("md_corpus")
            pdf = sources.get("pdf")
            try:
                if md is not None:
                    pages = lire_markdown(md)
                    stats["markdown"] += 1
                elif pdf is not None:
                    pages = lire_pdf(pdf)
                    stats["pdf"] += 1
                else:
                    continue
            except Exception as erreur:
                print(f"Document illisible : {cle} — {erreur}")
                stats["illisibles"] += 1
                continue

            fichier = pdf or md
            chemin_relatif = fichier.relative_to(ROOT).as_posix()
            document_id = re.sub(r"[^A-Za-z0-9]+", "_", cle).strip("_")

            section = ""
            nb = 0
            for page, texte in pages:
                if not texte.strip():
                    continue
                morceaux, section = decouper_page(texte, section)
                for numero, (sec, morceau) in enumerate(morceaux, start=1):
                    record = {
                        "chunk_id": f"{document_id}_{page}_{numero}",
                        "dci": dci,
                        "brand": brand,
                        "document_type": document_type(fichier.name),
                        "file_path": chemin_relatif,
                        "page": page,
                        "section": sec,
                        "text": morceau,
                    }
                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                    nb += 1
            total += nb
            print(f"Traité : {chemin_relatif} ({nb} passages)")

        nomenclature = chunks_nomenclature(noms_dci_dossier)
        for record in nomenclature:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nDocuments : {len(documents)} (Markdown : {stats['markdown']}, PDF seul : {stats['pdf']}, "
          f"illisibles : {stats['illisibles']})")
    print(f"Passages de documents : {total}")
    print(f"Passages de nomenclature : {len(nomenclature)}")
    print(f"Passages au total : {total + len(nomenclature)}")
    print(f"Fichier créé : {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
