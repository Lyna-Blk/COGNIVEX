# Knowledge Graph — Summary

**Total nodes**: 757  |  **Total edges**: 4210


## Node types

| Type | Count |
|---|---|
| Medicament | 674 |
| DCI | 40 |
| CodeATC | 40 |
| ClasseThera | 3 |

## Edge types (relations)

| Relation | Count |
|---|---|
| EQUIVALENT_A | 2960 |
| EST_GENERIQUE_DE | 674 |
| MEME_CLASSE_QUE | 496 |
| APPARTIENT_A | 40 |
| A_CODE_ATC | 40 |

## Top 10 DCI by number of brand names

| DCI | Brand names (generics) |
|---|---|
| paracétamol | 89 |
| ibuprofène | 55 |
| diclofénac | 55 |
| célécoxib | 33 |
| métronidazole | 33 |
| valsartan | 33 |
| amlodipine | 26 |
| bisoprolol | 26 |
| kétoprofène | 25 |
| ciprofloxacine | 23 |

## Ontology

```
NODES:
  DCI          → active substance (paracétamol, amoxicilline...)
  Medicament   → brand product (DOLIPRANE 500mg comprimé)
  ClasseThera  → therapeutic class (Antalgiques, Antibiotiques...)
  CodeATC      → ATC classification code (N02BE01)

EDGES:
  EST_GENERIQUE_DE  Medicament → DCI
  APPARTIENT_A      DCI        → ClasseThera
  A_CODE_ATC        DCI        → CodeATC
  MEME_CLASSE_QUE   DCI        ↔ DCI  (same class)
  EQUIVALENT_A      Medicament ↔ Medicament  (same DCI+form+dosage)
```