import sys

import pandas as pd

from build_kg import KG_DIR, NIVEAUX, ONTOLOGIE
from rag_config import ROOT

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SORTIE = ROOT / "docs" / "ontologie.md"


def effectifs(fichier: str, colonne: str) -> dict:
    chemin = KG_DIR / fichier
    if not chemin.is_file():
        return {}
    return pd.read_csv(chemin, encoding="utf-8-sig")[colonne].value_counts().to_dict()


def main():
    n_classes = effectifs("noeuds.csv", "type")
    n_relations = effectifs("relations.csv", "predicat")
    if not n_classes:
        print("[AVERTISSEMENT] data/kg/ introuvable : les effectifs seront vides. "
              "Lancez d'abord python src/build_kg.py")
    nb = lambda d, k: f"{d[k]}" if k in d else "—"

    classes, relations = ONTOLOGIE["classes"], ONTOLOGIE["relations"]
    lignes = [
        "# Ontologie minimale — COGNIVEX", "",
        "> Document généré par `src/generer_ontologie_md.py` à partir de `src/build_kg.py`. "
        "Ne pas le modifier à la main : modifier `ONTOLOGIE` dans `build_kg.py`, puis relancer le script.", "",
        "## Principe", "",
        "Le graphe relie un médicament commercialisé (**Produit**) à sa substance active (**DCI**), "
        "à sa classification (**CodeATC**, **ClasseTherapeutique**), à sa **Presentation** (forme et dosage) "
        "et à son **Laboratoire**. Chaque **Document** du corpus est relié aux DCI et produits qu'il décrit "
        "et à son **TypeSource** (niveau d'autorité). Les interactions relient une DCI à un **Partenaire** "
        "(substance ou classe citée dans la page source).", "",
        f"## Entités : {len(classes)} classes", "",
        "| Classe | Définition | Nombre de nœuds |", "|---|---|---|",
        *[f"| {c} | {d} | {nb(n_classes, c)} |" for c, d in classes.items()], "",
        f"## Relations : {len(relations)} prédicats", "",
        "| Relation | Domaine (source) | Codomaine (cible) | Nombre |", "|---|---|---|---|",
        *[f"| {r} | {dom} | {cod} | {nb(n_relations, r)} |" for r, (dom, cod) in relations.items()], "",
    ]
    for r, description in ONTOLOGIE.get("inferee", {}).items():
        lignes += [f"**Relation inférée (non stockée)** — `{r}` : {description}", ""]
    lignes += [
        "## Niveaux de gravité d'une interaction", "",
        "Valeurs possibles pour l'attribut `niveau` de `interagitAvec` : "
        + " ; ".join(libelle for _, libelle in NIVEAUX) + ".", "",
        "## Validation", "",
        "`verifier_ontologie()` (dans `build_kg.py`) contrôle chaque relation du graphe : le prédicat doit être "
        "défini ci-dessus et les types de la source et de la cible doivent correspondre au domaine et au "
        "codomaine. Le résultat est affiché à la fin de `build_kg.py` (« Violations d'ontologie »).", "",
        "## Limites", "",
        "- « Produits équivalents » (`estEquivalentDe`) signifie « même DCI dans la nomenclature » ; ce n'est pas "
        "une liste officielle de génériques, et aucune substitution n'est recommandée.",
        "- Les interactions viennent uniquement des pages DwaDZ du corpus : l'absence de relation `interagitAvec` "
        "pour une DCI ne signifie pas qu'elle n'a pas d'interaction, seulement qu'aucune page n'a été lue.",
        "- Un nom commercial absent de la nomenclature n'a pas de DCI dans le graphe : on n'en déduit pas une "
        "par ressemblance de nom (risque LASA, ex. ANTALGEN ≈ ANTALGAN).",
        "- Le type de produit (générique, référence étrangère) n'est renseigné que lorsque la source le précise.",
        "- Un `Partenaire` n'est relié à une DCI (`partenaireEstDCI`) que lorsque son nom correspond à une DCI du graphe.",
        "",
    ]
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text("\n".join(lignes), encoding="utf-8")
    print(f"Écrit : {SORTIE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
