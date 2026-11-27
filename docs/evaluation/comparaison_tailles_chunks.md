# Comparaison de trois tailles de chunks

## Objectif

Cette expérience compare trois tailles de passages afin d’observer leur effet sur le nombre de chunks, leur longueur et la couverture du corpus. Le nettoyage du texte est appliqué avant le découpage pour réduire les éléments répétitifs des sites et les résidus d’OCR.

## Méthode

Les trois configurations ont été exécutées sur le même corpus et avec la même méthode de nettoyage :

| Expérience | Taille maximale | Chevauchement |
|---|---:|---:|
| 1 | 120 mots | 20 mots |
| 2 | 240 mots | 40 mots |
| 3 | 500 mots | 75 mots |

Les passages sont enregistrés séparément pour chaque expérience. Le nettoyage vise notamment les éléments d’interface et pieds de page répétitifs, tels que « Voir la boîte (Google) », « Voir plus », « Cartes du monde », les liens et certains éléments de navigation. Les informations utiles sur les médicaments et les mentions de provenance, comme « DwaDZ », sont conservées.

## Résultats

| Expérience | Taille maximale | Chevauchement | Chunks créés | DCI représentées | Longueur moyenne | Longueur min.–max. |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 120 mots | 20 mots | 4 714 | 39 | 106,3 mots | 9–120 |
| 2 | 240 mots | 40 mots | 2 555 | 39 | 188,3 mots | 9–240 |
| 3 | 500 mots | 75 mots | 1 460 | 39 | 302,1 mots | 9–500 |

L’augmentation de la taille maximale réduit le nombre de chunks. Les trois expériences couvrent le même nombre de DCI dans les fichiers découpés. La longueur moyenne réelle est inférieure à la limite maximale, car certains documents et certaines pages contiennent moins de texte.

## Vérification des DCI

Le fichier Excel contient 40 DCI. L’hydrochlorothiazide n’ayant pas été retrouvé lors de la collecte, la comparaison porte sur les 39 autres DCI.

L’hydrochlorothiazide est documenté séparément comme DCI non retrouvée pendant la collecte.

## Périmètre des fichiers

Le script de découpage a trouvé 119 fichiers PDF dans `data/corpus`. Ce nombre désigne les PDF sources parcourus par le script. Les fichiers Markdown OCR enregistrés dans `data/processed_corpus` sont des sorties de traitement associées à certains PDF ; ils ne doivent pas être additionnés aux PDF comme s’il s’agissait de nouveaux documents sources.

## Choix provisoire

La configuration de 500 mots avec un chevauchement de 75 mots constitue un compromis provisoire : elle produit moins de chunks que la configuration 120/20, tout en conservant des passages plus courts.

## Cohérence entre chunks, embeddings et base vectorielle

Pour chaque expérience, le nombre d’embeddings calculés et le nombre de vecteurs dans ChromaDB doivent être égaux au nombre de chunks conservés après nettoyage :

| Expérience | Chunks attendus | Embeddings à confirmer | Vecteurs ChromaDB à confirmer |
|---|---:|---:|---:|
| 1 | 4 714 | 4 714 | 4 714 |
| 2 | 2 555| 2 555 | 2 555 |
| 3 | 1 460 | 1 460 | 1 460 |

Ces égalités sont à confirmer après le dernier nettoyage et la dernière reconstruction des embeddings et des bases vectorielles. Les anciens nombres de passages ou de vecteurs correspondent à des exécutions antérieures et ne doivent pas être mélangés aux résultats ci-dessus.
