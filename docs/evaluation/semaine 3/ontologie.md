# Ontologie minimale — COGNIVEX

> Document généré par `src/generer_ontologie_md.py` à partir de `src/build_kg.py`. Ne pas le modifier à la main : modifier `ONTOLOGIE` dans `build_kg.py`, puis relancer le script.

## Principe

Le graphe relie un médicament commercialisé (**Produit**) à sa substance active (**DCI**), à sa classification (**CodeATC**, **ClasseTherapeutique**), à sa **Presentation** (forme et dosage) et à son **Laboratoire**. Chaque **Document** du corpus est relié aux DCI et produits qu'il décrit et à son **TypeSource** (niveau d'autorité). Les interactions relient une DCI à un **Partenaire** (substance ou classe citée dans la page source).

## Entités : 9 classes

| Classe | Définition | Nombre de nœuds |
|---|---|---|
| ClasseTherapeutique | Classe thérapeutique | 3 |
| DCI | Dénomination commune internationale | 40 |
| CodeATC | Code de classification ATC | 38 |
| Produit | Médicament commercialisé : référence ou générique | 455 |
| Presentation | Forme pharmaceutique et dosage | 455 |
| Laboratoire | Laboratoire fabricant | 24 |
| Document | RCP, notice ou autre document | 87 |
| TypeSource | Type et niveau d'autorité de la source | 9 |
| Partenaire | Substance ou classe citée dans une interaction | 21 |

## Relations : 10 prédicats

| Relation | Domaine (source) | Codomaine (cible) | Nombre |
|---|---|---|---|
| aPourDCI | Produit | DCI | 455 |
| aPourATC | DCI | CodeATC | 38 |
| appartientAClasse | DCI | ClasseTherapeutique | 38 |
| aPourPresentation | Produit | Presentation | 455 |
| fabriquePar | Produit | Laboratoire | 34 |
| decritDCI | Document | DCI | 87 |
| decritProduit | Document | Produit | 6 |
| provientDeSource | Document | TypeSource | 87 |
| interagitAvec | DCI | Partenaire | 28 |
| partenaireEstDCI | Partenaire | DCI | 2 |

**Relation inférée (non stockée)** — `estEquivalentDe` : Produit-Produit : produits ayant la même DCI. Cette relation est calculée à partir de aPourDCI.

## Niveaux de gravité d'une interaction

Valeurs possibles pour l'attribut `niveau` de `interagitAvec` : Contre-indication ; Association déconseillée ; Précaution d'emploi ; À prendre en compte.

## Validation

`verifier_ontologie()` (dans `build_kg.py`) contrôle chaque relation du graphe : le prédicat doit être défini ci-dessus et les types de la source et de la cible doivent correspondre au domaine et au codomaine. Le résultat est affiché à la fin de `build_kg.py` (« Violations d'ontologie »).

## Limites

- « Produits équivalents » (`estEquivalentDe`) signifie « même DCI dans la nomenclature » ; ce n'est pas une liste officielle de génériques, et aucune substitution n'est recommandée.
- Les interactions viennent uniquement des pages DwaDZ du corpus : l'absence de relation `interagitAvec` pour une DCI ne signifie pas qu'elle n'a pas d'interaction, seulement qu'aucune page n'a été lue.
- Un nom commercial absent de la nomenclature n'a pas de DCI dans le graphe : on n'en déduit pas une par ressemblance de nom (risque LASA, ex. ANTALGEN ≈ ANTALGAN).
- Le type de produit (générique, référence étrangère) n'est renseigné que lorsque la source le précise.
- Un `Partenaire` n'est relié à une DCI (`partenaireEstDCI`) que lorsque son nom correspond à une DCI du graphe.
