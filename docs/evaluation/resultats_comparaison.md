# Résultats — recherche par mots-clés et recherche sémantique

- Date : 20/11/2026
- Corpus : 3 586 passages (`data/processed_corpus` et `data/fiches_dci`)
- Mots-clés : BM25
- Sémantique : similarité cosinus sur les vecteurs du corpus (TF-IDF + SVD, dimension 192)
- Passages détaillés : [comparaison_recherche.md](comparaison_recherche.md)

Un score BM25 et un score cosinus ne se comparent pas entre eux. On compare le passage qui arrive en premier.

| Question | Premier passage utile, mots-clés | Premier passage utile, sémantique | Passages identiques dans le top 5 | Premier document, mots-clés | Premier document, sémantique |
|---|---:|---:|---:|---|---|
| 1. Amoxicilline + acide clavulanique | 1 | 1 | 3 | bonne fiche DCI | bonne fiche DCI |
| 2. CARDENSIEL | 37 | 558 | 3 | amlodipine | acide acétylsalicylique |
| 3. Ramipril + diclofénac | introuvable | introuvable | 2 | diclofénac | diclofénac |
| 4. Génériques d’Amlor | 1 | 1 | 4 | amlodipine | amlodipine |
| 5. Ciprofloxacine | 68 | 526 | 1 | diclofénac | losartan |
| 6. PANADOL, dose maximale | 1 | 1 | 4 | paracétamol + codéine | paracétamol + codéine |
| 7. Antalgen | 807 | 842 | 2 | diclofénac | ramipril |
| 8. Demande de traitement | non noté | non noté | 2 | célécoxib | célécoxib |

Les deux méthodes retrouvent le même passage 21 fois sur 40. Seules les questions 1, 4 et 6 placent un passage utile dans le top 5 des deux méthodes.

## 1. Formes et dosages de l’amoxicilline + acide clavulanique

Les deux méthodes ouvrent la fiche `AMOXICILLINE_et_ACIDE CLAVULANIQUE`.

Les mots-clés mettent d’abord le paragraphe « Précision », qui répète « nomenclature algérienne ». La liste des formes et des dosages est au rang 3. La recherche sémantique met cette liste au rang 1.

Les deux top 5 contiennent aussi la fiche nifédipine, à cause des mêmes phrases de nomenclature.

## 2. DCI de CARDENSIEL

Le nom est dans `data/fiches_dci/bisoprolol.md`. La DCI est le bisoprolol. Aucune des deux méthodes ne place ce passage dans le top 5.

Les mots-clés le classent 37e. La recherche sémantique le classe 558e. Les premiers passages sont des pages « Dénomination du médicament / DCI » d’autres RCP, parce que la question reprend ces mots.

## 3. Association ramipril et diclofénac

Aucun passage du corpus ne cite les deux médicaments ensemble. Le niveau de gravité de cette paire est donc introuvable pour les deux méthodes.

Les mots-clés ne remontent que le diclofénac, plus une notice d’amoxicilline qui parle de douleur. La recherche sémantique met trois passages de diclofénac, puis deux passages de ramipril. Les RCP de diclofénac parlent d’IEC et d’AINS, pas du couple ramipril–diclofénac.

## 4. Génériques d’Amlor 5 mg

Les deux méthodes ouvrent la fiche amlodipine, au paragraphe « Précision ». Le tableau des noms commerciaux est dans la même fiche, mais ce n’est pas le premier passage affiché.

Les passages suivants sont losartan, énalapril, ramipril et valsartan : ces fiches recopient les mêmes phrases sur la nomenclature et les génériques.

## 5. Ciprofloxacine chez une femme enceinte

Le corpus n’a pas de fiche ni de RCP de ciprofloxacine. Le mot apparaît seulement dans un autre document : rang 68 pour les mots-clés, rang 526 pour la recherche sémantique.

Les premiers passages parlent de diclofénac ou de losartan, à cause de « précautions », « grossesse » et « posologie ». La source manque.

## 6. Dépasser la dose maximale de PANADOL 1 g

Les deux méthodes trouvent d’abord un RCP de paracétamol + codéine, parce que la question parle de dose maximale répartie dans la journée. Ce n’est pas le RCP de PANADOL 1 g.

Les mots-clés gardent `RCP_Panadol_1g.md` au rang 5. La recherche sémantique remplit son top 5 avec les RCP codéinés, et PANADOL disparaît.

Le système doit refuser de répartir une dose supérieure au maximum et le dire. Le RCP ne l’autorise pas.

## 7. Antalgen

La fiche paracétamol contient ANTALGAN, pas Antalgen. Une lettre sépare les deux noms. Les mots-clés classent un passage qui contient ANTALGAN au rang 807. La recherche sémantique le classe au rang 842.

Les deux top 5 sont des sections « comment prendre / dose pour un adulte » de diclofénac, ramipril, célécoxib, tramadol ou méloxicam. Aucune des deux méthodes ne vérifie que le nom existe.

## 8. Demande d’anti-inflammatoire ou d’antibiotique

Cette question est hors périmètre. Le système ne doit pas choisir un médicament.

Les deux recherches remontent quand même le célécoxib, parce que la question dit « anti-inflammatoire » et « gonflement ». Ces passages ne doivent pas devenir une recommandation.

## Bilan

| Situation | Résultat |
|---|---|
| Le nom du médicament est dans la question (1, 4, 6) | Les deux méthodes trouvent le bon groupe de documents, avec des passages parasites |
| Nom commercial rare (2) | Mots-clés meilleurs, mais hors du top 5 (rang 37 contre 558) |
| Deux médicaments à relier (3) | Sémantique : les deux DCI sont dans le top 5, jamais dans le même passage |
| Nom mal orthographié (7) | Aucune des deux méthodes |
| Médicament absent du corpus (5) | Aucune des deux méthodes. Il faut dire que la source manque |
| Demande de prescription (8) | Les deux retrouvent un anti-inflammatoire. Aucune ne doit répondre |
