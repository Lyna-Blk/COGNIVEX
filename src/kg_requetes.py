import sys
import shutil
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rag_config import ROOT
from build_kg import cle_dci, sans_espace

KG = ROOT / "data" / "kg"
EVALUATION = ROOT / "docs" / "evaluation" / "semaine 3" # même dossier que les autres rapports


def charger():
    noeuds_path = KG / "noeuds.csv"
    relations_path = KG / "relations.csv"

    if not noeuds_path.exists() or not relations_path.exists():
        raise FileNotFoundError(
            "Knowledge Graph introuvable. "
            "Executez d'abord : python src/build_kg.py"
        )

    n = pd.read_csv(noeuds_path, keep_default_na=False)
    r = pd.read_csv(relations_path, keep_default_na=False)

    return n, r


def trouver_produits(n, nom):
    cle = sans_espace(nom).upper()

    return n[
        (n["type"] == "Produit")
        & (
            n["label"].apply(
                lambda x: sans_espace(x).upper()
            ) == cle
        )
    ]


def dci_de(nom, n, r):
    """Q2 : retrouver la DCI d'un nom commercial."""

    produits = trouver_produits(n, nom)
    resultats = []

    for p in produits.itertuples():
        liens = r[
            (r["sujet"] == p.id)
            & (r["predicat"] == "aPourDCI")
        ]

        for dci_id in liens["objet"]:
            dci_node = n[n["id"] == dci_id]

            resultats.append({
                "nom_commercial": p.label,
                "DCI": (
                    dci_node.iloc[0]["label"]
                    if not dci_node.empty else dci_id
                ),
                "id_DCI": dci_id
            })

    return resultats


def equivalents(nom, n, r):
    """Q4 : produits ayant la meme DCI."""

    resultats = []

    for info in dci_de(nom, n, r):
        dci_id = info["id_DCI"]

        liens = r[
            (r["predicat"] == "aPourDCI")
            & (r["objet"] == dci_id)
        ]

        for pid in liens["sujet"]:
            produit = n[n["id"] == pid]

            if produit.empty:
                continue

            presentations = r[
                (r["sujet"] == pid)
                & (r["predicat"] == "aPourPresentation")
            ]

            if presentations.empty:
                resultats.append({
                    "DCI": info["DCI"],
                    "nom_commercial": produit.iloc[0]["label"],
                    "presentation": ""
                })

            for presentation_id in presentations["objet"]:
                presentation = n[
                    n["id"] == presentation_id
                ]

                resultats.append({
                    "DCI": info["DCI"],
                    "nom_commercial": produit.iloc[0]["label"],
                    "presentation": (
                        presentation.iloc[0]["label"]
                        if not presentation.empty else ""
                    )
                })

    return resultats


def interactions(dci, r, niveau=None):
    """Extraire les interactions d'une DCI."""

    dci_id = f"dci:{cle_dci(dci)}"

    x = r[
        (r["sujet"] == dci_id)
        & (r["predicat"] == "interagitAvec")
    ]

    if niveau and "niveau" in x.columns:
        x = x[x["niveau"] == niveau]

    colonnes = [
        c for c in ["sujet", "objet", "niveau", "document"]
        if c in x.columns
    ]

    return x[colonnes].to_dict("records")


def sauvegarder_csv(nom, donnees, colonnes):
    df = pd.DataFrame(donnees, columns=colonnes)
    chemin = EVALUATION / nom
    df.to_csv(chemin, index=False, encoding="utf-8-sig")
    return len(df)


def main():
    EVALUATION.mkdir(parents=True, exist_ok=True)

    n, r = charger()

    # Questions de test
    produits_test = [
        "CARDENSIEL",
        "ANTALGEN",
        "AMLOR"
    ]

    resultats_dci = []
    resultats_equivalents = []
    resultats_interactions = []

    for nom in produits_test:
        resultats_dci.extend(dci_de(nom, n, r))
        resultats_equivalents.extend(equivalents(nom, n, r))

    # toutes les interactions du périndopril, tous niveaux confondus (le niveau est dans la colonne « niveau »)
    for resultat in interactions("perindopril", r):
        resultat["niveau_recherche"] = "tous niveaux"
        resultats_interactions.append(resultat)

    
    nb_dci = sauvegarder_csv(
        "kg_resultats_dci.csv",
        resultats_dci,
        ["nom_commercial", "DCI", "id_DCI"]
    )

    nb_equiv = sauvegarder_csv(
        "kg_resultats_equivalents.csv",
        resultats_equivalents,
        ["DCI", "nom_commercial", "presentation"]
    )

    nb_inter = sauvegarder_csv(
        "kg_resultats_interactions.csv",
        resultats_interactions,
        ["sujet", "objet", "niveau", "document", "niveau_recherche"]
    )

    graphml = KG / "kg.graphml"   # nom écrit par build_kg.py
    graph_copie = False

    if graphml.exists():
        shutil.copy2(
            graphml,
            EVALUATION / "knowledge_graph.graphml"
        )
        graph_copie = True

    types_noeuds = (
        n["type"].value_counts().to_dict()
        if "type" in n.columns else {}
    )

    types_relations = (
        r["predicat"].value_counts().to_dict()
        if "predicat" in r.columns else {}
    )

    rapport = [
        "# Evaluation du Knowledge Graph",
        "",
        "## 1. Statistiques generales",
        f"- Nombre de noeuds : {len(n)}",
        f"- Nombre de relations : {len(r)}",
        "",
        "### Types de noeuds",
    ]

    for type_, nombre in types_noeuds.items():
        rapport.append(f"- {type_} : {nombre}")

    rapport += ["", "### Types de relations"]

    for relation, nombre in types_relations.items():
        rapport.append(f"- {relation} : {nombre}")

    rapport += [
        "",
        "## 2. Tests de nomenclature",
        f"- Resultats DCI : {nb_dci}",
        f"- Produits equivalents (lignes, produit interroge inclus) : {nb_equiv}",
        f"- Interactions trouvees (PERINDOPRIL, tous niveaux) : {nb_inter}",
        "",
        "## 3. Questions testees",
        "- Quelle est la DCI de CARDENSIEL ?",
        "- Quelle est la DCI de ANTALGEN ?",
        "- Quels produits partagent la DCI de AMLOR ?",
        "- Quelles interactions sont associees au PERINDOPRIL ?",
        "",
        "## 4. Fichiers generes",
        "- kg_resultats_dci.csv",
        "- kg_resultats_equivalents.csv",
        "- kg_resultats_interactions.csv",
        "- knowledge_graph.graphml : "
        + ("copie disponible" if graph_copie else "non disponible"),
        "",
        "Les resultats dependent des informations presentes "
        "dans le Knowledge Graph."
    ]

    (EVALUATION / "kg_evaluation.md").write_text(
        "\n".join(rapport),
        encoding="utf-8"
    )

    print("\n EVALUATION DU KNOWLEDGE GRAPH ")
    print("Dossier :", EVALUATION)
    print("Nombre de noeuds :", len(n))
    print("Nombre de relations :", len(r))
    print("Resultats DCI :", nb_dci)
    print("Equivalents :", nb_equiv)
    print("Interactions :", nb_inter)
    print("Rapport : kg_evaluation.md")
  


if __name__ == "__main__":
    main()
