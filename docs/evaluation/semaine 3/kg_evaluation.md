# Evaluation du Knowledge Graph

## 1. Statistiques generales
- Nombre de noeuds : 1132
- Nombre de relations : 1230

### Types de noeuds
- Produit : 455
- Presentation : 455
- Document : 87
- DCI : 40
- CodeATC : 38
- Laboratoire : 24
- Partenaire : 21
- TypeSource : 9
- ClasseTherapeutique : 3

### Types de relations
- aPourDCI : 455
- aPourPresentation : 455
- decritDCI : 87
- provientDeSource : 87
- aPourATC : 38
- appartientAClasse : 38
- fabriquePar : 34
- interagitAvec : 28
- decritProduit : 6
- partenaireEstDCI : 2

## 2. Tests de nomenclature
- Resultats DCI : 2
- Produits equivalents (lignes, produit interroge inclus) : 33
- Interactions trouvees (PERINDOPRIL, tous niveaux) : 12

## 3. Questions testees
- Quelle est la DCI de CARDENSIEL ?
- Quelle est la DCI de ANTALGEN ?
- Quels produits partagent la DCI de AMLOR ?
- Quelles interactions sont associees au PERINDOPRIL ?

## 4. Fichiers generes
- kg_resultats_dci.csv
- kg_resultats_equivalents.csv
- kg_resultats_interactions.csv
- knowledge_graph.graphml : copie disponible

Les resultats dependent des informations presentes dans le Knowledge Graph.