# Ontologie — Graphe de connaissances DCI

Généré automatiquement : **757** noeuds, **4210** relations.


## Types de noeuds

| Type | Description | Nombre | Propriétés | Exemple |
|---|---|---|---|---|
| Medicament | Produit commercial : nom + forme + dosage | 674 | dans_nomenclature, dci, dosage, forme, label, nom_commercial, nom_normalized, source | `MED::doli_bien::compri::500mg` |
| DCI | Substance active (paracétamol, amoxicilline...) | 40 | atc, classe, dans_nomenclature, dci_normalized, label, numero, source | `DCI::paracétamol` |
| CodeATC | Code de classification ATC (ex: N02BE01) | 40 | label, prefix_4 | `ATC::N02BE01` |
| ClasseThera | Classe thérapeutique (Antalgiques, Antibiotiques...) | 3 | label | `CLASSE::Antalgiques et anti-inflammatoires` |

## Types de relations

| Relation | Domaine → Co-domaine | Description | Nombre |
|---|---|---|---|
| EQUIVALENT_A | Medicament → Medicament | Même DCI + même forme + même dosage (bidirectionnelle) | 2960 |
| EST_GENERIQUE_DE | Medicament → DCI | Le médicament est un générique/brand de cette DCI | 674 |
| MEME_CLASSE_QUE | DCI → DCI | Deux DCI de la même classe (bidirectionnelle) | 496 |
| APPARTIENT_A | DCI → ClasseThera | La DCI appartient à cette classe thérapeutique | 40 |
| A_CODE_ATC | DCI → CodeATC | La DCI possède ce code ATC | 40 |

## Schéma

```
Medicament --EST_GENERIQUE_DE--> DCI
Medicament <--EQUIVALENT_A-->    Medicament
DCI        --APPARTIENT_A-->     ClasseThera
DCI        --A_CODE_ATC-->       CodeATC
DCI        <--MEME_CLASSE_QUE--> DCI
```

## Fichiers exportés

- `graph.json` : node-link JSON (NetworkX)
- `graph.graphml` : pour Gephi / Cytoscape
- `nodes.csv` / `relations.csv` : tables plates (Excel, Neo4j, pandas)
- `graph_summary.md` : statistiques