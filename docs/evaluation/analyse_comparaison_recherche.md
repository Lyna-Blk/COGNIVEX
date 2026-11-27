# Analyse — mots-clés et recherche sémantique

- Date : 20/11/2026
- Détail des passages : [comparaison_recherche.md](comparaison_recherche.md)
- 3586 passages, BM25 contre embeddings TF-IDF + SVD (dimension 192)

Le rang indiqué est celui du premier passage qui contient bien l’information demandée. Un rang 1 dans le top 5 ne veut pas dire que tout le top 5 est bon.

Sur 7 questions notées, les deux méthodes placent un passage utile dans le top 5 pour les questions 1, 4 et 6 seulement. Elles se rejoignent sur 21 passages sur 40.

## Question 1 — Formes et dosages

Les deux méthodes ouvrent la fiche `AMOXICILLINE_et_ACIDE CLAVULANIQUE`.

BM25 met d’abord le paragraphe « Précision », qui répète « nomenclature » et « algérienne ». La liste des formes et des dosages est au rang 3. La recherche sémantique met cette liste au rang 1.

Les deux top 5 contiennent aussi la fiche nifédipine, à cause des mêmes phrases de nomenclature. Le bon document est trouvé, mais il n’est pas seul.

## Question 2 — CARDENSIEL

Le nom figure dans `data/fiches_dci/bisoprolol.md`. Aucune des deux méthodes ne le place dans le top 5.

BM25 le classe 37e. La recherche sémantique le classe 558e. Les premiers passages sont des pages « Dénomination du médicament / DCI » d’autres RCP (amlodipine, aspirine), parce que la question reprend ces mots.

Pour un nom commercial rare, les mots-clés restent moins mauvais : la SVD étale ce nom parmi les autres pages de RCP. Ni l’un ni l’autre ne suffit tant que la question est pleine de formules communes à tous les RCP.

## Question 3 — Ramipril et diclofénac

Aucun passage du corpus ne cite les deux médicaments ensemble. Le critère « les deux noms dans le même passage » est donc introuvable pour les deux méthodes.

BM25 ne remonte que le diclofénac, plus une notice d’amoxicilline qui parle de douleur. La recherche sémantique met trois passages de diclofénac puis deux passages de ramipril dans le même top 5. Elle couvre les deux médicaments, sans jamais les relier.

Les RCP de diclofénac parlent d’IEC et d’AINS, pas du couple ramipril–diclofénac. Aucune des deux recherches ne peut fournir un niveau de gravité cité mot pour mot.

## Question 4 — Génériques d’Amlor

Les deux méthodes placent en tête la fiche amlodipine, au paragraphe « Précision », qui rappelle la nomenclature algérienne. Le tableau des noms commerciaux est dans la même fiche, mais ce n’est pas le passage affiché en premier.

Les rangs suivants sont d’autres fiches (losartan, énalapril, ramipril, valsartan) : elles recopient les mêmes phrases sur la nomenclature et les génériques. Le mot « générique » rapproche des médicaments qui ne contiennent pas d’amlodipine.

## Question 5 — Ciprofloxacine et grossesse

Le corpus n’a pas de fiche ni de RCP de ciprofloxacine. Le mot n’apparaît qu’en passant dans un autre document (rang 68 en BM25, rang 526 en sémantique).

Les premiers passages parlent de diclofénac ou de losartan, parce que la question contient « précautions », « grossesse » et « posologie ». Retrouver ces pages ne donne pas la réponse. Il faut dire que la source manque.

## Question 6 — Dose maximale de PANADOL

Les deux méthodes trouvent d’abord un RCP de paracétamol + codéine, parce que la question parle de dose maximale et de répartition dans la journée. Ce n’est pas le RCP de PANADOL 1 g.

BM25 garde quand même `RCP_Panadol_1g.md` au rang 5. La recherche sémantique remplit son top 5 avec les seuls RCP codéinés : le nom PANADOL disparaît. Ici les mots-clés protègent le nom du produit, la recherche par le sens le remplace par un produit proche.

## Question 7 — Antalgen

La fiche paracétamol contient ANTALGAN, pas Antalgen. Une lettre sépare les deux noms. BM25 classe un passage qui contient ANTALGAN au rang 807, la recherche sémantique au rang 842.

Les deux top 5 sont des sections « comment prendre / quelle dose » de diclofénac, ramipril, célécoxib, tramadol ou méloxicam. La question demande une dose pour un adulte, et ces notices répondent à cette forme de phrase. Aucune ne vérifie que le nom existe.

## Question 8 — Demande de traitement

Cette question est hors périmètre : le système ne doit pas choisir un médicament. Les deux recherches remontent quand même le célécoxib, parce que la question dit « anti-inflammatoire » et « gonflement ». La recherche sémantique ouvre sur la phrase qui classe CELEBREX parmi les anti-inflammatoires.

Ces passages ne doivent pas servir à recommander un traitement. Ils montrent seulement que la recherche suit les symptômes.

## Bilan

| Situation | Méthode la plus utile ici |
|---|---|
| La question reprend le nom du médicament et le type d’information (questions 1, 4, 6) | Les deux, avec des passages parasites |
| Nom commercial rare au milieu de formules de RCP (question 2) | BM25, et encore loin du top 5 |
| Deux médicaments à relier (question 3) | Sémantique : les deux DCI sont dans le top 5, jamais dans le même passage |
| Nom mal orthographié (question 7) | Aucune |
| Médicament absent du corpus (question 5) | Aucune : il faut répondre que la source manque |
| Demande de prescription (question 8) | Aucune ne doit répondre |

La recherche par mots-clés s’accroche aux mots exacts, y compris aux phrases recopiées d’une fiche à l’autre. La recherche sémantique rapproche des passages de même sujet, et elle confond plus facilement deux médicaments voisins ou un produit et son association. Les deux devront être croisées avant de rédiger une réponse avec citation.
