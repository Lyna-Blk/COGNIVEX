
import csv
import difflib
import json
import re
import sys
from pathlib import Path

from rag_config import (
    CORPUS_DIR,
    PRODUITS_FILE,
    REFERENCE_XLSX,
    TABLE_NOMS_FILE,
    canon_dci,
    normalize,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ============================================================
# CONFIGURATION
# ============================================================

COLONNES = [
    "nom_commercial", "nom_normalise", "dci", "dci_normalisee",
    "code_atc", "classe", "formes_dosages", "laboratoire",
    "numero_enregistrement", "type_nom", "niveau_source",
    "sources", "remarques",
]

LASA_FILE = TABLE_NOMS_FILE.parent / "paires_noms_proches_lasa.csv"

LASA_COLONNES = [
    "nom_a", "dci_a", "nom_b", "dci_b", "similarite"
]

SEUIL_LASA = 0.82

NIVEAUX = {
    "MIPH": "officielle (nomenclature MIPH)",
    "FICHE": "fiche produit",
    "PHARMNET": "secondaire (Pharm'Net / DwaDZ)"
}

_DOSAGE = re.compile(
    r"^\d+([.,]\d+)?(mg|g|ml|ui|mcg|ug|mui|%)?$"
)

_DOSAGE_COLLE = re.compile(
    r"^([a-z]{4,})\d+(mg|g|ml)?$"
)

_UNITES = {
    "mg", "g", "ml", "ui", "mcg", "ug", "mui", "l", "kg"
}

# MOTS COURANTS

_MOTS_COURANTS = set("""
dans pour avec sans quel quelle quels quelles comment peut peuvent
dose doses jour jours adulte adultes enfant enfants patient patients
forme formes dosage dosages liste sont etre avoir cette cet ces
medicament medicaments pharmacie nomenclature algerienne generique
generiques stock rupture enceinte grossesse precautions emploi
posologie anti inflammatoire antibiotique douleur depuis hier soir
fievre joue gonflement dentaire legere forte
""".split())

# NORMALISATION DES NOMS

def nom_base(nom: str) -> str:
    """
    Supprime les dosages d'un nom commercial.

    Exemples:
    PANADOL 1G -> panadol
    FLOCINE500 -> flocine
    BYZOLEX 5 -> byzolex
    """

    jetons = normalize(nom).split()
    garde = []

    for j in jetons:

        if _DOSAGE.match(j) or j in _UNITES:
            continue

        m = _DOSAGE_COLLE.match(j)

        garde.append(m.group(1) if m else j)

    return " ".join(garde) or normalize(nom)


def type_nom(nom_norm: str, dci_norm: str) -> str:
    """
    Heuristique non officielle :
    dci+labo ou marque.
    """

    premier = dci_norm.split()[0] if dci_norm else ""

    return (
        "dci+labo"
        if premier and premier[:6] in nom_norm
        else "marque"
    )

# LECTURE DES SOURCES

def _lire_xlsx() -> list[dict]:

    from openpyxl import load_workbook

    if not REFERENCE_XLSX.is_file():

        print(
            f"[AVERTISSEMENT] Nomenclature introuvable : "
            f"{REFERENCE_XLSX}"
        )

        return []

    wb = load_workbook(
        REFERENCE_XLSX,
        read_only=True,
        data_only=True
    )

    lignes = list(wb.active.iter_rows(values_only=True))

    wb.close()

    if not lignes:
        return []

    en_tete = [
        str(c).strip() if c else ""
        for c in lignes[0]
    ]

    def col(*noms):

        for n in noms:

            if n in en_tete:
                return en_tete.index(n)

        raise ValueError(
            f"Colonne introuvable dans l'Excel : {noms}"
        )

    i_dci = col("DCI (nom de la substance)")
    i_nom = col("N,C", "N.C", "Nom commercial")

    i_atc = col("Code ATC (indicatif)")
    i_classe = col("Classe")

    i_forme = col("Forme")
    i_dosage = col("Dosage")
    i_rem = col("Remarques")

    out = []

    for numero, l in enumerate(lignes[1:], start=2):

        if not l[i_dci] or not l[i_nom]:
            continue

        out.append({

            "nom": str(l[i_nom]).strip(),

            "dci": str(l[i_dci]).strip(),

            "atc": str(l[i_atc] or "").strip(),

            "classe": str(l[i_classe] or "").strip(),

            "forme": str(l[i_forme] or "").strip().lower(),

            "dosage": str(l[i_dosage] or "").strip().lower(),

            "remarque": str(l[i_rem] or "").strip(),

            "ligne": numero,
        })

    return out


def _lire_produits() -> list[dict]:

    if not PRODUITS_FILE.is_file():
        return []

    return json.loads(
        PRODUITS_FILE.read_text(encoding="utf-8")
    )


def _lire_csv_pharmnet() -> list[dict]:

    out = []

    for chemin in sorted(
        CORPUS_DIR.rglob("Commercialname-*.csv")
    ):

        with chemin.open(
            encoding="utf-8-sig",
            newline=""
        ) as f:

            for r in csv.reader(f):

                if (
                    not r
                    or r[0].strip().lower() == "commercial name"
                    or len(r) < 2
                ):
                    continue

                out.append({

                    "nom": r[0].strip(),

                    "dci": r[1].strip(),

                    "forme_dosage": (
                        r[2] if len(r) > 2 else ""
                    ).replace("pharmnet-dz", "").strip(),

                    "labo": (
                        r[3] if len(r) > 3 else ""
                    ).replace("pharmnet-dz", "").strip(),

                    "fichier": chemin.relative_to(
                        CORPUS_DIR
                    ).as_posix(),
                })

    return out

# CONSTRUCTION DE LA TABLE DES NOMS COMMERCIAUX

def construire_table() -> list[dict]:

    table: dict[str, dict] = {}

    def entree(nom, dci, source):

        cle = normalize(nom)

        e = table.get(cle)

        if e is None:

            e = table[cle] = {

                "nom_commercial": nom.strip().upper(),

                "nom_normalise": cle,

                "dci": dci.strip(),

                "dci_normalisee": canon_dci(dci),

                "code_atc": "",

                "classe": "",

                "_fd": [],

                "laboratoire": "",

                "numero_enregistrement": "",

                "niveau_source": source,

                "_sources": [],

                "_rem": [],
            }

        return e

    # NOMENCLATURE MIPH
    
    for r in _lire_xlsx():

        e = entree(r["nom"], r["dci"], "MIPH")

        e["code_atc"] = e["code_atc"] or r["atc"]

        e["classe"] = e["classe"] or r["classe"]

        fd = f"{r['forme']} {r['dosage']}".strip()

        if fd and fd not in e["_fd"]:
            e["_fd"].append(fd)

        s = f"MIPH:ligne {r['ligne']}"

        if s not in e["_sources"]:
            e["_sources"].append(s)

        if (
            r["remarque"]
            and r["remarque"] not in e["_rem"]
        ):
            e["_rem"].append(r["remarque"])

    # FICHES PRODUIT
    
    for p in _lire_produits():

        nom = p.get("nom_commercial")

        if not nom:
            continue

        dci = (
            p.get("dci_fiche")
            or p.get("dci")
            or ""
        )

        e = table.get(normalize(nom))

        if e is None:

            e = entree(nom, dci, "FICHE")

        e["laboratoire"] = (
            e["laboratoire"]
            or (p.get("laboratoire") or "")
        )

        e["numero_enregistrement"] = (
            e["numero_enregistrement"]
            or (p.get("numero_enregistrement") or "")
        )

        fd = " ".join(

            x for x in (
                p.get("forme") or "",
                p.get("dosage") or ""
            ) if x

        ).lower()

        if fd and not e["_fd"]:
            e["_fd"].append(fd)

        source = f"FICHE:{p.get('fichier', '')}"

        if source not in e["_sources"]:
            e["_sources"].append(source)

    # PHARM'NET / DWADZ
    
    for r in _lire_csv_pharmnet():

        e = table.get(normalize(r["nom"]))

        if e is None:

            e = entree(
                r["nom"],
                r["dci"],
                "PHARMNET"
            )

        e["laboratoire"] = (
            e["laboratoire"] or r["labo"]
        )

        if r["forme_dosage"] and not e["_fd"]:

            e["_fd"].append(
                r["forme_dosage"].lower()
            )

        source = f"PHARMNET:{r['fichier']}"

        if source not in e["_sources"]:
            e["_sources"].append(source)

    # PREPARATION DU RESULTAT

    lignes = []

    for e in sorted(
        table.values(),
        key=lambda x: (
            x["dci_normalisee"],
            x["nom_normalise"]
        )
    ):

        lignes.append({

            "nom_commercial": e["nom_commercial"],

            "nom_normalise": e["nom_normalise"],

            "dci": e["dci"],

            "dci_normalisee": e["dci_normalisee"],

            "code_atc": e["code_atc"],

            "classe": e["classe"],

            "formes_dosages": " | ".join(e["_fd"]),

            "laboratoire": e["laboratoire"],

            "numero_enregistrement": e["numero_enregistrement"],

            "type_nom": type_nom(
                e["nom_normalise"],
                e["dci_normalisee"]
            ),

            "niveau_source": NIVEAUX[e["niveau_source"]],

            "sources": " ; ".join(
                dict.fromkeys(e["_sources"])
            ),

            "remarques": " | ".join(e["_rem"]),
        })

    return lignes

# DETECTION DES PAIRES LASA

def paires_lasa(
    lignes: list[dict],
    seuil: float = SEUIL_LASA
) -> list[dict]:

    """
    Recherche les paires de noms commerciaux proches
    appartenant à des DCI différentes.

    Exemple :
    Deux noms proches orthographiquement peuvent être
    signalés pour vérification pharmaceutique.
    """

    noms_uniques = {}

    for r in lignes:

        base = nom_base(r["nom_commercial"])

        dci = r["dci_normalisee"]

        if not base or len(base) < 5 or not dci:
            continue

        cle = (base, dci)

        if cle not in noms_uniques:

            noms_uniques[cle] = {

                "nom_base": base,

                "nom_commercial": r["nom_commercial"],

                "dci": r["dci"],
            }

    noms = list(noms_uniques.values())

    resultat = []

    for i in range(len(noms)):

        for j in range(i + 1, len(noms)):

            a = noms[i]

            b = noms[j]

            
            if canon_dci(a["dci"]) == canon_dci(b["dci"]):
                continue

            similarite = difflib.SequenceMatcher(
                None,
                a["nom_base"],
                b["nom_base"]
            ).ratio()

            if similarite >= seuil:

                resultat.append({

                    "nom_a": a["nom_commercial"],

                    "dci_a": a["dci"],

                    "nom_b": b["nom_commercial"],

                    "dci_b": b["dci"],

                    "similarite": round(similarite, 2),
                })

    return sorted(
        resultat,
        key=lambda x: x["similarite"],
        reverse=True
    )


def ecrire_paires_lasa(paires: list[dict]) -> None:

    LASA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with LASA_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=LASA_COLONNES
        )

        writer.writeheader()

        writer.writerows(paires)

# ECRITURE DE LA TABLE CSV

def ecrire_table(lignes: list[dict]) -> None:

    TABLE_NOMS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with TABLE_NOMS_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        w = csv.DictWriter(
            f,
            fieldnames=COLONNES
        )

        w.writeheader()

        w.writerows(lignes)

# CHARGEMENT DE LA TABLE

def charger_table() -> list[dict]:

    """
    Charge la table.
    La construit si elle n'existe pas encore.
    """

    if not TABLE_NOMS_FILE.is_file():

        ecrire_table(
            construire_table()
        )

    with TABLE_NOMS_FILE.open(
        encoding="utf-8-sig",
        newline=""
    ) as f:

        return list(
            csv.DictReader(f)
        )

# INDEX DES NOMS

class IndexNoms:

    """
    Index prêt à l'emploi :
    nom normalisé (avec ou sans dosage) -> lignes de la table.
    """

    def __init__(self, table: list[dict]):

        self.table = table

        self.index: dict[str, dict] = {}

        for r in table:

            for cle in {
                r["nom_normalise"],
                nom_base(r["nom_commercial"])
            }:

                if (
                    cle
                    and len(cle) >= 4
                    and cle not in self.index
                ):

                    self.index[cle] = r

        self.longueur_max = max(
            (
                len(c.split())
                for c in self.index
            ),
            default=1
        )

        self.noms_uniques = sorted({

            c for c in self.index
            if " " not in c

        })


_CACHE: dict[int, IndexNoms] = {}


def _index(table):

    if id(table) not in _CACHE:

        _CACHE[id(table)] = IndexNoms(table)

    return _CACHE[id(table)]

# RECHERCHE DES NOMS EXACTS

def trouver_noms(
    question: str,
    table: list[dict]
) -> list[dict]:

    """
    Recherche les noms commerciaux présents dans la question.
    Utilise les n-grammes du plus long au plus court.
    """

    idx = _index(table)

    jetons = normalize(question).split()

    trouves = []

    i = 0

    while i < len(jetons):

        for n in range(
            min(
                idx.longueur_max,
                len(jetons) - i
            ),
            0,
            -1
        ):

            cle = " ".join(
                jetons[i:i + n]
            )

            r = idx.index.get(cle)

            if r and cle not in _MOTS_COURANTS:

                trouves.append({

                    "mot": cle,

                    "nom": r["nom_commercial"],

                    "dci": r["dci"],

                    "dci_normalisee": r["dci_normalisee"],

                    "niveau_source": r["niveau_source"]
                })

                i += n

                break

        else:

            i += 1

    return trouves

# DETECTION DES NOMS PROCHES

def _mots_candidats(
    question: str,
    seuil: float
) -> list[tuple[str, float]]:

    """
    Détecte les mots qui ressemblent à des noms commerciaux.
    """

    out = []

    for m in re.finditer(
        r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9'’-]*",
        question
    ):

        mot = m.group(0)

        avant = question[:m.start()].rstrip()

        debut_phrase = (
            (not avant)
            or avant[-1] in ".?!:;"
        )

        if (
            mot.isupper()
            and len(mot) > 3
            or (
                mot[0].isupper()
                and not debut_phrase
            )
        ):

            out.append(
                (normalize(mot), seuil)
            )

        elif (
            mot[0].isupper()
            and debut_phrase
            and len(mot) >= 7
        ):

            out.append(
                (normalize(mot), 0.85)
            )

    return out


def noms_proches(
    question: str,
    table: list[dict],
    seuil: float = 0.78
) -> list[dict]:

    """
    Recherche les noms commerciaux proches d'un mot inconnu.
    Ne transforme jamais un nom inconnu en DCI.
    """

    idx = _index(table)

    connus = {
        t["mot"]
        for t in trouver_noms(question, table)
    }

    mots_dci = {

        m

        for r in table

        for m in r["dci_normalisee"].split()
    }

    sortie = []

    for mot, seuil_mot in _mots_candidats(
        question,
        seuil
    ):

        if (
            len(mot) < 6
            or mot in idx.index
            or mot in connus
            or mot in _MOTS_COURANTS
            or mot in mots_dci
        ):

            continue

        candidats = difflib.get_close_matches(
            mot,
            idx.noms_uniques,
            n=2,
            cutoff=seuil_mot
        )

        for cand in candidats:

            r = idx.index[cand]

            sortie.append({

                "mot": mot,

                "proche_de": r["nom_commercial"],

                "dci": r["dci"],

                "similarite": round(
                    difflib.SequenceMatcher(
                        None,
                        mot,
                        cand
                    ).ratio(),
                    2
                )
            })

    return sortie

# EXTENSION DE LA QUESTION

def etendre_question(
    question: str,
    table: list[dict] | None = None
) -> dict:

    """
    Retourne :
    question
    question_etendue
    correspondances
    proches
    """

    table = (
        table
        if table is not None
        else charger_table()
    )

    corr = trouver_noms(
        question,
        table
    )

    ajouts = []

    deja = normalize(question)

    for c in corr:

        c["ajoute"] = not (

            c["dci_normalisee"]
            and c["dci_normalisee"] in deja

        )

        if c["ajoute"]:

            ajouts.append(
                f"{c['nom']} = DCI {c['dci']}"
            )

    etendue = (

        f"{question} (DCI : {' ; '.join(ajouts)})"

        if ajouts

        else question
    )

    return {

        "question": question,

        "question_etendue": etendue,

        "correspondances": corr,

        "proches": noms_proches(
            question,
            table
        )
    }

# PROGRAMME PRINCIPAL

def main():

    lignes = construire_table()

    ecrire_table(lignes)

    paires = paires_lasa(
        lignes,
        seuil=SEUIL_LASA
    )

    ecrire_paires_lasa(paires)

    dcis = {
        l["dci_normalisee"]
        for l in lignes
    }

    print("\n ANALYSE Noms ")

    print(
        f"Table écrite : {TABLE_NOMS_FILE}"
    )

    print(
        f"{len(lignes)} noms commerciaux"
    )

    print(
        f"{len(dcis)} DCI"
    )

    par_niveau = {}

    for l in lignes:

        niveau = l["niveau_source"]

        par_niveau[niveau] = (
            par_niveau.get(niveau, 0) + 1
        )

    for niveau, nombre in par_niveau.items():

        print(
            f" - {niveau} : {nombre}"
        )

    print("\n ANALYSE LASA ")

    print(
        f"Paires de noms proches : {len(paires)}"
    )

    print(
        f"Fichier LASA : {LASA_FILE}"
    )

    if paires:

        print("\nExemples de paires :")

        for p in paires[:10]:

            print(
                f" {p['nom_a']} ({p['dci_a']})"
                f" <-> {p['nom_b']} ({p['dci_b']})"
                f" | Similarité : {p['similarite']}"
            )

    # 6. Test de l'extension de question
    if (
        len(sys.argv) > 2
        and sys.argv[1] == "--test"
    ):

        r = etendre_question(
            " ".join(sys.argv[2:]),
            lignes
        )

        print("\n========== TEST EXTENSION ==========")

        print(
            json.dumps(
                r,
                ensure_ascii=False,
                indent=2
            )
        )


if __name__ == "__main__":
    main()
