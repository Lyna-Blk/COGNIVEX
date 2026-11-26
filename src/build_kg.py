
import json
import re
import sys
from pathlib import Path
from collections import Counter

import networkx as nx
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from noms_commerciaux import canon_dci
from rag_config import ROOT, normalize

# CHEMINS DES FICHIERS

KG_DIR = ROOT / "data" / "kg"
PROC = ROOT / "data" / "processed_corpus"

TABLE = ROOT / "data" / "processed" / "table_noms_commerciaux.csv"
META = ROOT / "data" / "processed" / "corpus_metadata.json"

# ONTOLOGIE : ENTITES ET RELATIONS

ONTOLOGIE = {
    "classes": {
        "ClasseTherapeutique": "Classe thérapeutique",
        "DCI": "Dénomination commune internationale",
        "CodeATC": "Code de classification ATC",
        "Produit": "Médicament commercialisé : référence ou générique",
        "Presentation": "Forme pharmaceutique et dosage",
        "Laboratoire": "Laboratoire fabricant",
        "Document": "RCP, notice ou autre document",
        "TypeSource": "Type et niveau d'autorité de la source",
        "Partenaire": "Substance ou classe citée dans une interaction"
    },

    "relations": {
        "aPourDCI": ("Produit", "DCI"),
        "aPourATC": ("DCI", "CodeATC"),
        "appartientAClasse": ("DCI", "ClasseTherapeutique"),
        "aPourPresentation": ("Produit", "Presentation"),
        "fabriquePar": ("Produit", "Laboratoire"),
        "decritDCI": ("Document", "DCI"),
        "decritProduit": ("Document", "Produit"),
        "provientDeSource": ("Document", "TypeSource"),
        "interagitAvec": ("DCI", "Partenaire"),
        "partenaireEstDCI": ("Partenaire", "DCI")
    },

    "inferee": {
        "estEquivalentDe": (
            "Produit-Produit : produits ayant la même DCI. "
            "Cette relation est calculée à partir de aPourDCI."
        )
    }
}


NIVEAUX = [
    ("contre indication", "Contre-indication"),
    ("association deconseillee", "Association déconseillée"),
    ("precaution d emploi", "Précaution d'emploi"),
    ("a prendre en compte", "À prendre en compte")
]

# FONCTIONS DE NORMALISATION

def valeur(v):
    """Convertit une valeur CSV en texte propre."""
    if v is None:
        return ""
    return str(v).strip()

def sans_espace(s):
    """Normalise un texte et supprime les espaces."""
    return normalize(valeur(s)).replace(" ", "")


def cle_dci(s):
    """Construit un identifiant stable pour une DCI."""
    s = valeur(s)

    if not s:
        return ""

    try:
        resultat = canon_dci(s)
        if resultat:
            s = resultat
    except Exception:
        pass

    return sans_espace(s)


def lire_csv():
    """Charge le tableau de nomenclature."""
    if not TABLE.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {TABLE}"
        )

    df = pd.read_csv(TABLE, keep_default_na=False)

    colonnes_obligatoires = {
        "nom_commercial",
        "dci",
        "dci_normalisee",
        "code_atc",
        "classe",
        "formes_dosages",
        "laboratoire",
        "type_nom",
        "niveau_source",
        "sources"
    }

    manquantes = colonnes_obligatoires - set(df.columns)

    if manquantes:
        raise ValueError(
            f"Colonnes manquantes dans le CSV : {sorted(manquantes)}"
        )

    return df

# EXTRACTION DES INFORMATIONS DwaDZ

def lire_md(p):
    """Lit un fichier Markdown et retire son front matter."""
    txt = p.read_text(encoding="utf-8")

    return re.sub(
        r"\A---.*?---\s*",
        "",
        txt,
        count=1,
        flags=re.S
    )

def champs_dwadz(txt):
    """Extrait quelques informations des pages DwaDZ."""

    flat = " ".join(txt.split())
    out = {}

    ancre = flat.lower().find("type de produit")

    if ancre >= 0:
        zone = flat[max(0, ancre - 60):ancre + 150]

        m = re.search(
            r"(GENERIQUE|REFERENCE\s?[A-Z]+|BIOSIMILAIRE)",
            zone,
            re.I
        )

        if m:
            out["type_produit"] = re.sub(
                r"\s+",
                " ",
                m.group(1)
            ).strip().lower()

    # Numéro d'enregistrement
    m = re.search(
        r"(\d{3}/\d{2}\s?[A-Z]\s?\d{3}/\d{2}/\d{2})",
        flat
    )

    if m:
        out["n_enregistrement"] = m.group(1)


    m = re.search(
        r"Laboratoire\s+([A-Z][A-Z0-9 '.&()-]{3,60}?)"
        r"\s+(?:Pays|\d+/\d)",
        flat
    )

    if m:
        out["laboratoire"] = m.group(1).strip()

    m = re.search(
        r"\n([A-Z0-9 .'/-]{4,60}?)\s?"
        r"\d+(?:[.,]\d+)?\s?(?:mg|g|%|ui)\s?:\s?[ée]quivalents",
        txt
    )

    if m:
        out["titre_produit"] = m.group(1).strip()

    return out


_MAJ = r"[A-ZÉÈÀÂÊÎÔÛÇ0-9 '()’+/,.-]{3,90}"

_ENTETE = re.compile(
    r"^(Contre-?\s?indication|Association\s?d[ée]conseill[ée]e|"
    r"Pr[ée]caution\s?d.emploi|[ÀA]\s?prendre en compte)"
    r"\s*([\u2460-\u2473\d]*)$",
    re.I
)


def interactions_dwadz(txt):
    """Extrait les interactions depuis les pages OCR."""

    lignes = [l.strip() for l in txt.splitlines()]

    debut = next(
        (
            i for i, l in enumerate(lignes)
            if "Par gravit" in l or "Tout deplier" in l
        ),
        None
    )

    if debut is None:
        return []

    def est_partenaire(i):
        return (
            i + 1 < len(lignes)
            and re.fullmatch(_MAJ, lignes[i]) is not None
            and lignes[i + 1] in ("SUBSTANCE", "CLASSE")
        )

    def niveau_entete(i):
        m = _ENTETE.match(lignes[i])

        if not m:
            return None

        suivant = next(
            (
                j for j in range(i + 1, min(i + 4, len(lignes)))
                if lignes[j]
            ),
            None
        )

        if not (
            m.group(2)
            or (
                suivant is not None
                and est_partenaire(suivant)
            )
        ):
            return None

        n = normalize(m.group(1)).replace(" ", "")

        return next(
            (
                nom for cle, nom in NIVEAUX
                if n.startswith(cle.replace(" ", ""))
            ),
            None
        )

    niveau = None
    resultat = []
    i = debut

    while i < len(lignes):

        nv = niveau_entete(i)

        if nv:
            niveau = nv

        elif niveau and est_partenaire(i):

            bloc = []
            j = i + 2

            while (
                j < len(lignes)
                and not est_partenaire(j)
                and niveau_entete(j) is None
                and not re.match(r"^---|^## Page", lignes[j])
            ):
                bloc.append(lignes[j])
                j += 1

            texte = " ".join(x for x in bloc if x)

            src = re.search(
                r"Source\s?:\s?(.{0,80}?)(?= Source|$)",
                texte
            )

            resultat.append({
                "partenaire": lignes[i],
                "nature": (
                    "classe"
                    if lignes[i + 1] == "CLASSE"
                    else "substance"
                ),
                "niveau": niveau,
                "texte": re.sub(r"\s+", " ", texte)[:400],
                "source_citee": src.group(1).strip() if src else ""
            })

            i = j
            continue

        i += 1

    return resultat


def interactions_dwadz_v2(txt):
    """Variante pour les pages OCR au format #### Niveau."""

    flat = txt.replace("<br>", " ")

    titres = [
        (m.start(), m.group(1))
        for m in re.finditer(
            r"####\s*(Contre-?\s?indication|Association\s?"
            r"d[ée]conseill[ée]e|Pr[ée]caution\s?d.emploi|"
            r"[ÀA]\s?prendre en compte)",
            flat,
            re.I
        )
    ]

    if not titres:
        return []

    def niveau_a(pos):
        courant = None

        for debut, titre in titres:
            if debut <= pos:
                courant = titre

        n = normalize(courant or "")

        return next(
            (
                nom for cle, nom in NIVEAUX
                if n.replace(" ", "").startswith(
                    cle.replace(" ", "")
                )
            ),
            None
        )

    resultat = []

    for m in re.finditer(
        r"([A-ZÉÈÀÂÊÎÔÛÇ][A-ZÉÈÀÂÊÎÔÛÇ0-9 '’()+/,.-]{3,80}?)"
        r"\s?(CLASSE|SUBSTANCE)\b",
        flat
    ):

        niveau = niveau_a(m.start())

        if not niveau:
            continue

        suite = flat[m.end():m.end() + 700]

        fin = re.search(r"Source\s?:?[^S]{0,80}", suite)

        texte = suite[:fin.end()] if fin else suite[:400]

        resultat.append({
            "partenaire": m.group(1).strip(),
            "nature": m.group(2).lower(),
            "niveau": niveau,
            "texte": re.sub(r"\s+", " ", texte)[:400],
            "source_citee": fin.group(0).strip() if fin else ""
        })

    return resultat

# CONSTRUCTION DU KNOWLEDGE GRAPH

def construire():

    t = lire_csv()

    if not META.exists():
        raise FileNotFoundError(
            f"Fichier metadata introuvable : {META}"
        )

    meta = json.loads(
        META.read_text(encoding="utf-8")
    )

    G = nx.MultiDiGraph()

    # Création des noeuds et relations

    def noeud(id_, typ, label, **props):

        if id_ not in G:
            G.add_node(
                id_,
                type=typ,
                label=valeur(label),
                **props
            )
        else:
          
            for k, v in props.items():
                if v not in ("", None) and not G.nodes[id_].get(k):
                    G.nodes[id_][k] = v

        return id_

    def rel(s, p, o, **props):

        if s not in G or o not in G:
            raise ValueError(
                f"Relation impossible : noeud absent ({s}, {o})"
            )

        G.add_edge(
            s,
            o,
            key=f"{p}|{G.number_of_edges()}",
            predicat=p,
            **props
        )

    # DCI, ATC et classes thérapeutiques

    for _, r in t.iterrows():

        dci = valeur(r["dci"])
        dci_norm = valeur(r["dci_normalisee"]) or dci

        if not dci:
            continue

        did = f"dci:{cle_dci(dci_norm)}"

        d = noeud(
            did,
            "DCI",
            dci,
            atc=valeur(r["code_atc"])
        )

        atc = valeur(r["code_atc"])

        if atc:
            aid = noeud(
                f"atc:{normalize(atc)}",
                "CodeATC",
                atc
            )

            if not G.has_edge(d, aid):
                rel(d, "aPourATC", aid)

        classe = valeur(r["classe"])

        if classe:
            cid = noeud(
                f"classe:{normalize(classe)}",
                "ClasseTherapeutique",
                classe
            )

            if not G.has_edge(d, cid):
                rel(d, "appartientAClasse", cid)
  
    # Produits, présentations et laboratoires
    
    prod_idx = {}

    for _, r in t.iterrows():

        nom = valeur(r["nom_commercial"])
        nom_norm = valeur(r["nom_normalise"]) or normalize(nom)

        dci = valeur(r["dci"])
        dci_norm = valeur(r["dci_normalisee"]) or dci

        if not nom or not dci:
            continue

        did = f"dci:{cle_dci(dci_norm)}"

        if did not in G:
            noeud(did, "DCI", dci)

        # Un produit commercial est distinct pour chaque nom + DCI.
        pid = f"prod:{sans_espace(nom_norm)}|{cle_dci(dci_norm)}"

        pid = noeud(
            pid,
            "Produit",
            nom,
            type_nom=valeur(r["type_nom"]),
            n_enregistrement=valeur(r["numero_enregistrement"]),
            source_nomenclature=valeur(r["sources"]),
            niveau_source=valeur(r["niveau_source"])
        )

        prod_idx.setdefault(sans_espace(nom), pid)
        prod_idx.setdefault(sans_espace(nom_norm), pid)

        if not G.has_edge(pid, did):
            rel(
                pid,
                "aPourDCI",
                did,
                source=valeur(r["sources"]),
                niveau_source=valeur(r["niveau_source"])
            )

        presentation = valeur(r["formes_dosages"])

        if presentation:
            pres_id = (
                f"pres:{sans_espace(nom_norm)}|"
                f"{sans_espace(presentation)}"
            )

            pres = noeud(
                pres_id,
                "Presentation",
                presentation,
                forme_dosage=presentation
            )

            if not G.has_edge(pid, pres):
                rel(pid, "aPourPresentation", pres)

        laboratoire = valeur(r["laboratoire"])

        if laboratoire:
            lid = noeud(
                f"labo:{normalize(laboratoire)}",
                "Laboratoire",
                laboratoire
            )

            if not G.has_edge(pid, lid):
                rel(pid, "fabriquePar", lid)

    # Documents du corpus
    
    for d in meta.get("corpus", []):

        dci = valeur(d.get("dci"))

        if not dci:
            continue

        did = f"dci:{cle_dci(dci)}"

        if did not in G:
            noeud(did, "DCI", dci)

        for sf in d.get("source_files", []):

            relative_path = valeur(sf.get("relative_path"))
            filename = valeur(sf.get("filename")) or Path(
                relative_path
            ).name

            doc_id = noeud(
                f"doc:{relative_path}",
                "Document",
                filename,
                doc_type=valeur(sf.get("doc_type")),
                niveau_autorite=valeur(sf.get("authority_tier")),
                qualite_texte=valeur(sf.get("text_quality"))
            )

            rel(doc_id, "decritDCI", did)

            source_type = (
                valeur(sf.get("source_type"))
                or "source_non_precisee"
            )

            source_id = noeud(
                f"src:{normalize(source_type)}",
                "TypeSource",
                source_type,
                rang=valeur(sf.get("authority_tier"))
            )

            if not G.has_edge(doc_id, source_id):
                rel(doc_id, "provientDeSource", source_id)

    # Extraction DwaDZ
    
    n_pages = 0
    n_inter = 0

    details = []
    deja = set()

    for md in sorted(PROC.rglob("*.md")):

        txt = lire_md(md)

        if (
            "DwaDZ" not in txt[:3000]
            and "pharmaveille" not in txt[:3000].lower()
        ):
            continue

        rel_path = md.relative_to(PROC)

        dci_dossier = canon_dci(rel_path.parts[0])
        dci_id = f"dci:{cle_dci(dci_dossier)}"

        n_pages += 1

        if dci_id not in G:
            noeud(
                dci_id,
                "DCI",
                dci_dossier
            )

        ch = champs_dwadz(txt)

        pid = None

        if ch.get("titre_produit"):

            titre = ch["titre_produit"]

            pid = prod_idx.get(sans_espace(titre))

            if pid is None:
                titre_simple = re.sub(
                    r"\d+.*$",
                    "",
                    titre
                ).strip()

                pid = prod_idx.get(sans_espace(titre_simple))

        if pid:

            if ch.get("type_produit"):
                G.nodes[pid]["type_produit"] = ch["type_produit"]

            if ch.get("n_enregistrement"):
                G.nodes[pid]["n_enregistrement"] = (
                    ch["n_enregistrement"]
                )

            if ch.get("laboratoire"):

                labo_id = (
                    f"labo:{normalize(ch['laboratoire'])}"
                )

                labo = noeud(
                    labo_id,
                    "Laboratoire",
                    ch["laboratoire"]
                )

                if not G.has_edge(pid, labo):
                    rel(
                        pid,
                        "fabriquePar",
                        labo,
                        source=str(rel_path)
                    )

        doc_id = noeud(
            f"doc:data/processed_corpus/{rel_path.as_posix()}",
            "Document",
            rel_path.name,
            doc_type="page DwaDZ",
            niveau_autorite="4"
        )

        if not G.has_edge(doc_id, dci_id):
            rel(doc_id, "decritDCI", dci_id)

        source_id = noeud(
            "src:dz_professional_site",
            "TypeSource",
            "dz_professional_site",
            rang="4"
        )

        if not G.has_edge(doc_id, source_id):
            rel(doc_id, "provientDeSource", source_id)

        if pid and not G.has_edge(doc_id, pid):
            rel(doc_id, "decritProduit", pid)

        liste = (
            interactions_dwadz(txt)
            or interactions_dwadz_v2(txt)
        )

        for it in liste:

            partenaire_nom = valeur(it["partenaire"])

            cle_i = (
                dci_id,
                normalize(partenaire_nom),
                it["niveau"]
            )

            if cle_i in deja:
                continue

            deja.add(cle_i)

            part_id = (
                f"part:{normalize(partenaire_nom)}"
            )

            part = noeud(
                part_id,
                "Partenaire",
                partenaire_nom,
                nature=it["nature"]
            )

            cd = cle_dci(partenaire_nom)
            partenaire_dci_id = f"dci:{cd}"

            if (
                partenaire_dci_id in G
                and it["nature"] == "substance"
                and not G.has_edge(part, partenaire_dci_id)
            ):
                rel(
                    part,
                    "partenaireEstDCI",
                    partenaire_dci_id
                )

            rel(
                dci_id,
                "interagitAvec",
                part,
                niveau=it["niveau"],
                risque_et_conduite=it["texte"],
                source_citee=it["source_citee"],
                document=str(rel_path),
                niveau_autorite="4"
            )

            n_inter += 1

        details.append(
            (str(rel_path), ch, len(liste))
        )

    return G, ONTOLOGIE, n_pages, n_inter, details

# VALIDATION DE L'ONTOLOGIE

def verifier_ontologie(G):

    erreurs = []

    for s, o, data in G.edges(data=True):

        predicat = data["predicat"]

        if predicat not in ONTOLOGIE["relations"]:
            erreurs.append(
                (s, predicat, o, "Relation non définie")
            )
            continue

        domaine, codomaine = ONTOLOGIE["relations"][predicat]

        if G.nodes[s]["type"] != domaine:
            erreurs.append(
                (s, predicat, o, "Type source incorrect")
            )

        if G.nodes[o]["type"] != codomaine:
            erreurs.append(
                (s, predicat, o, "Type cible incorrect")
            )

    return erreurs

# EXPORTATION

def exporter(G, n_pages, n_inter, details):

    KG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    (KG_DIR / "ontologie.json").write_text(
        json.dumps(
            ONTOLOGIE,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    noeuds = [
        {"id": n, **d}
        for n, d in G.nodes(data=True)
    ]

    pd.DataFrame(noeuds).to_csv(
        KG_DIR / "noeuds.csv",
        index=False,
        encoding="utf-8-sig"
    )
    
    relations = [
        {
            "sujet": s,
            "predicat": d["predicat"],
            "objet": o,
            **{
                k: v
                for k, v in d.items()
                if k != "predicat"
            }
        }
        for s, o, d in G.edges(data=True)
    ]

    pd.DataFrame(relations).to_csv(
        KG_DIR / "relations.csv",
        index=False,
        encoding="utf-8-sig"
    )

    H = nx.MultiDiGraph()

    for n, d in G.nodes(data=True):
        H.add_node(
            n,
            **{
                k: str(v)
                for k, v in d.items()
            }
        )

    for s, o, d in G.edges(data=True):
        H.add_edge(
            s,
            o,
            **{
                k: str(v)
                for k, v in d.items()
            }
        )

    nx.write_graphml(
        H,
        KG_DIR / "kg.graphml"
    )

    cn = Counter(
        d["type"]
        for _, d in G.nodes(data=True)
    )

    cr = Counter(
        d["predicat"]
        for _, _, d in G.edges(data=True)
    )

    inter = Counter(
        d["niveau"]
        for _, _, d in G.edges(data=True)
        if d["predicat"] == "interagitAvec"
    )

    tp = Counter(
        d.get("type_produit", "non renseigné")
        for _, d in G.nodes(data=True)
        if d["type"] == "Produit"
    )

    L = [
        "# Statistiques du graphe",
        "",
        f"- {G.number_of_nodes()} nœuds",
        f"- {G.number_of_edges()} relations",
        "",
        "## Nœuds par classe",
        ""
    ]

    L.extend(
        f"- {k} : {v}"
        for k, v in cn.most_common()
    )

    L.extend([
        "",
        "## Relations par prédicat",
        ""
    ])

    L.extend(
        f"- {k} : {v}"
        for k, v in cr.most_common()
    )

    L.extend([
        "",
        f"## Extraction DwaDZ : {n_pages} pages lues, "
        f"{n_inter} interactions",
        ""
    ])

    L.extend(
        f"- {k} : {v}"
        for k, v in inter.most_common()
    )

    L.extend([
        "",
        "## Type de produit",
        ""
    ])

    L.extend(
        f"- {k} : {v}"
        for k, v in tp.most_common()
    )

    L.extend([
        "",
        "## Détail par page DwaDZ",
        "",
        "| page | type produit | labo | n° enreg. | interactions |",
        "|---|---|---|---|---|"
    ])

    L.extend(
        f"| {p} | {c.get('type_produit', '—')} | "
        f"{c.get('laboratoire', '—')} | "
        f"{c.get('n_enregistrement', '—')} | {n} |"
        for p, c, n in details
    )

    (KG_DIR / "kg_stats.md").write_text(
        "\n".join(L),
        encoding="utf-8"
    )

    return cn, cr

# PROGRAMME PRINCIPAL
def main():

    print("Construction du Knowledge Graph...")

    G, _, n_pages, n_inter, details = construire()

    print("Vérification de l'ontologie...")

    erreurs = verifier_ontologie(G)

    cn, cr = exporter(
        G,
        n_pages,
        n_inter,
        details
    )

    print("\n RESULTATS ")

    print(
        f"Graphe : {G.number_of_nodes()} noeuds, "
        f"{G.number_of_edges()} relations"
    )

    print(
        f"Violations d'ontologie : {len(erreurs)}"
    )

    print("\nNoeuds :")
    print(dict(cn))

    print("\nRelations :")
    print(dict(cr))

    print(
        f"\nDwaDZ : {n_pages} pages, "
        f"{n_inter} interactions extraites"
    )

    print("\nFichiers exportés dans data/kg/")

    for e in erreurs[:10]:
        print("Violation :", e)

    print("\nConstruction terminée.")


if __name__ == "__main__":
    main()
