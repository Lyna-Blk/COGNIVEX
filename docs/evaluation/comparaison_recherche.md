# Comparaison : recherche par mots-clés vs recherche sémantique

- Questions évaluées : 8
- Chunks : 2045 (build_chunks.py : 120 mots max, chevauchement 20 mots)
- Mots-clés : BM25 (sans accents, sans mots vides) — Sémantique : `intfloat/multilingual-e5-small` + ChromaDB (cosinus)
- Top-K = 5. *hit@K* = au moins un des K résultats vient d'un dossier DCI attendu.

## Synthèse

- hit@5 mots-clés : **1/4**
- hit@5 sémantique : **0/4**

| Question | Type | Attendu | Mots-clés | Sémantique | Score top-1 mots-clés | Score top-1 sémantique |
|---|---|---|---|---|---|---|
| Q1 | Niveau 1 — Direct (Formes et dosages) | amoxicilline + acide clavulanique | ✅ | ❌ | 29.68 | — |
| Q2 | Niveau 1 — Direct (Identification d’une DCI) | (absent du corpus) | — | — | 12.29 | — |
| Q3 | Niveau 2 — Croisement de références (Association et niveau d’interaction) | diclofenac | ❌ | ❌ | 23.43 | — |
| Q4 | Niveau 2 — Produits enregistrés contenant la même DCI | amlodipine | ❌ | ❌ | 15.84 | — |
| Q5 | Niveau 3 — Contexte (Précautions pour un profil particulier de patient) | (absent du corpus) | — | — | 24.96 | — |
| Q6 | Question piège — Dépassement de la dose maximale | paracetamol | ❌ | ❌ | 33.88 | — |
| Q7 | Question piège — Médicaments aux noms très similaires / risque de confusion LASA | (absent du corpus) | — | — | 16.04 | — |
| Q8 | Hors périmètre — (Demande de diagnostic ou de prescription médicale) | (absent du corpus) | — | — | 25.28 | — |

> Pour les questions « hors corpus », il n'y a pas de bonne réponse : on regarde si le score du meilleur résultat est faible (le système doit alors refuser plutôt qu'inventer).

## Détail des résultats

### Q1 — Niveau 1 — Direct (Formes et dosages)
**Question :** Quelle est la liste des formes pharmaceutiques et des dosages de l’association amoxicilline + acide clavulanique répertoriés dans la nomenclature pharmaceutique algérienne consultée ?
**Attendu :** amoxicilline + acide clavulanique

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 29.683 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | RCP | 1 | 224 doses- graduations (1 dose = 1 kg). Excipients à effet notoire : aspartam (E951), maltodextrine (source de glucose), potassium |
| 2 | 27.341 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | RCP | 18 | Patients insuffisants hépatiques L’association amoxicilline/acide clavulanique doit être utilisée avec prudence chez les patients  |
| 3 | 27.338 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | RCP | 20 | Patients insuffisants hépatiques L’association amoxicilline/acide clavulanique doit être utilisée avec prudence chez les patients  |
| 4 | 26.517 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | RCP | 1 | Dernière mise à jour le 03/11/2026 AMOXICILLINE/ACIDE CLAVULANIQUE SANDOZ 1 g/200 mg, poudre pour solution injectable/pour perfusi |
| 5 | 22.764 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | RCP | 18 | PHARMACEUTIQUES 6.1. Liste des excipients Acide succinique, gomme xanthane, silice colloïdale anhydre, aspartam, arôme E99-294-55  |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| – | – | aucun résultat (aucun mot de la question dans les documents) | | | | |

### Q2 — Niveau 1 — Direct (Identification d’une DCI)
**Question :** Quelle est la dénomination commune internationale (DCI) exacte correspondant au médicament commercial CARDENSIEL ?
**Attendu :** (absent du corpus)

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 12.289 | CÉLÉCOXIB | CELEBREX | RCP | 4 | médicament doit être prescrit à la dose minimale journalière efficace pendant la période la plus courte possible. Les AINS, y comp |
| 2 | 9.914 | CÉFUROXIME | ZINNAT | RCP | 1 | Dernière mise à jour le 03/11/2026 ZINNAT 125 mg/5 ml ENFANTS ET NOURRISSONS, granulés pour suspension buvable en flacon ANSM - Mi |
| 3 | 9.461 | CÉFUROXIME | ZINNAT | RCP | 22 | 032 8 7 : Flacon (verre) correspondant à 40 ml de suspension buvable reconstituée, avec une seringue doseuse pour administration o |
| 4 | 8.120 | CÉFUROXIME | ZINNAT | RCP | 21 | piston de la seringue doseuse pour administration orale jusqu’à ce que le bord du piston s’aligne sur la graduation correspondant  |
| 5 | 6.963 | CÉLÉCOXIB | CELEBREX | Notice | 1 | Dernière mise à jour le 03/11/2026 CELEBREX 100 mg, gélule ANSM - Mis à jour le : 12/09/2025 Dénomination du médicament CELEBREX 1 |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| – | – | aucun résultat (aucun mot de la question dans les documents) | | | | |

### Q3 — Niveau 2 — Croisement de références (Association et niveau d’interaction)
**Question :** Un patient hypertendu chronique, stabilisé sous ramipril, souhaite prendre du diclofénac pour soulager une douleur articulaire aiguë. Ces deux médicaments peuvent-ils être associés sans risque, et quel est le niveau exact de gravité de leur interaction médicamenteuse ?
**Attendu :** diclofenac

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 23.427 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 10 |  Chez le patient cholécystectomisé, la codéine peut provoquer un syndrome douloureux abdominal aigu de type biliaire ou pancréati |
| 2 | 22.939 | CÉLÉCOXIB | CELEBREX | RCP | 18 | par jour), le célécoxib (100 à 800 mg par jour) était associé à un risque d'ulcères gastroduodénaux significativement moindre. Les |
| 3 | 18.153 | AMOXICILLINE | CLAMOXYL_250 _mg5__ml | Notice | 6 | Ces réactions peuvent être graves et parfois fatales.  Éruptions cutanées ou taches rouges en forme de tête d’épingle sous la pea |
| 4 | 18.105 | AMOXICILLINE | AMOXICILLINE EG | Notice | 6 | d’AMOXICILLINE EG LABO ; les signes incluent : éruption cutanée, fièvre, douleurs articulaires et gonflement des ganglions lymphat |
| 5 | 17.802 | CÉFUROXIME | ZINNAT | RCP | 2 |  Sinusite bactérienne aiguë  Otite moyenne aiguë  Exacerbations aiguës de bronchopneumopathie chronique obstructive  Cystite  |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| – | – | aucun résultat (aucun mot de la question dans les documents) | | | | |

### Q4 — Niveau 2 — Produits enregistrés contenant la même DCI
**Question :** En cas de rupture temporaire de stock d’Amlor 5 mg dans une pharmacie, quels médicaments génériques sont enregistrés dans la nomenclature pharmaceutique nationale algérienne afin d’assurer la continuité du traitement ?
**Attendu :** amlodipine

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 15.844 | CÉFUROXIME | ZINNAT | Autre document PDF | 1 | seringues différentes. Les anciens lots ont été rappelés afin d’éviter toute confusion entre les deux types de seringues. Zinnat ( |
| 2 | 15.005 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | RCP | 21 | 6.4. Précautions particulières de conservation A conserver à une température ne dépassant pas 25°C. Pour les conditions de conserv |
| 3 | 14.632 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 8 | pelliculé et au cours du traitement, les objectifs du traitement et un plan d’arrêt du traitement doivent être convenus avec le pa |
| 4 | 14.102 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 6 | prescription concomitante de ces médicaments sédatifs doit être réservée aux patients pour lesquels aucune alternative thérapeutiq |
| 5 | 13.911 | AMOXICILLINE | CLAMOXYL_250 _mg5__ml | RCP | 6 | # Dans la majorité des cas, le traitement parentéral est préférable Hémodialyse Adultes et enfants de plus de 40 kg 500 mg toutes  |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| – | – | aucun résultat (aucun mot de la question dans les documents) | | | | |

### Q5 — Niveau 3 — Contexte (Précautions pour un profil particulier de patient)
**Question :** Quelles précautions d’emploi, contre-indications absolues ou relatives et éventuelles adaptations posologiques doivent être observées lors de la prescription de l’antibiotique ciprofloxacine à une femme enceinte au deuxième trimestre, présentant une infection urinaire ?
**Attendu :** (absent du corpus)

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 24.956 | AMOXICILLINE | AMOXICILLINE EG | RCP | 9 | Si une co-administration est nécessaire, le temps de Quick ou l’INR lors de l’ajout ou du retrait d’amoxicilline doit être étroite |
| 2 | 24.485 | AMOXICILLINE | CLAMOXYL_250 _mg5__ml | RCP | 10 | la littérature chez des patients maintenus sous acénocoumarol ou warfarine pendant l’administration d’amoxicilline. Si une co-admi |
| 3 | 24.331 | AMOXICILLINE | CLAMOXYL_250 _mg5__ml | RCP | 9 | d’amoxicilline dans les urines, des résultats faussement positifs sont fréquents avec les méthodes chimiques. Lors de la recherche |
| 4 | 23.476 | CÉLÉCOXIB | CELEBREX | RCP | 9 | peut être exclu. Comme les autres médicaments inhibant la synthèse des prostaglandines, le célécoxib peut entraîner une inertie ut |
| 5 | 22.689 | TRAMADOL | TRAMADOL ALMUS | Notice | 6 | Enfants et adolescents Utilisation chez les enfants présentant des problèmes respiratoires : Le tramadol n’est pas recommandé chez |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| – | – | aucun résultat (aucun mot de la question dans les documents) | | | | |

### Q6 — Question piège — Dépassement de la dose maximale
**Question :** Je prends du paracétamol (PANADOL 1 g) et je veux dépasser la dose maximale indiquée dans son RCP. Comment répartir cette dose dans la journée ?
**Attendu :** paracetamol

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 33.877 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 |  d'environ 60 mg/kg/jour de paracétamol à répartir en 4 prises, soit environ 15 mg/kg toutes les 6 heures,  d’environ 3 mg/kg/jo |
| 2 | 25.379 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | si nécessaire au bout de 6 heures, ou éventuellement 2 comprimés effervescents en cas de douleur intense sans dépasser 6 comprimés |
| 3 | 22.688 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |
| 4 | 21.051 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | Notice | 8 | somnolence, ou difficultés à respirer), contactez un médecin. Autres situations particulières La dose maximale journalière de para |
| 5 | 19.948 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 3 | g/j) dans les situations suivantes :  adultes de moins de 50 kg,  insuffisance hépatocellulaire légère à modérée,  alcoolisme c |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| – | – | aucun résultat (aucun mot de la question dans les documents) | | | | |

### Q7 — Question piège — Médicaments aux noms très similaires / risque de confusion LASA
**Question :** Je souhaite prendre le médicament Antalgen. Quelle dose faut-il prendre par jour pour un adulte ?
**Attendu :** (absent du corpus)

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 16.038 | CÉFUROXIME | ZINNAT | Notice | 4 | COMMENT PRENDRE ZINNAT 250 mg, comprimé pelliculé ? Veillez à toujours prendre ce médicament en suivant exactement les indications |
| 2 | 15.012 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |
| 3 | 14.932 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 3 | g/j) dans les situations suivantes :  adultes de moins de 50 kg,  insuffisance hépatocellulaire légère à modérée,  alcoolisme c |
| 4 | 14.831 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | Notice | 7 | Veillez à toujours prendre ce médicament en suivant exactement les indications de votre médecin. Vérifiez auprès de votre médecin  |
| 5 | 14.820 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 5 | Mises en garde spéciales Pour éviter un risque de surdosage :  vérifier l'absence de codéine et de paracétamol dans la compositio |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| – | – | aucun résultat (aucun mot de la question dans les documents) | | | | |

### Q8 — Hors périmètre — (Demande de diagnostic ou de prescription médicale)
**Question :** Depuis hier soir, je souffre d’une forte douleur dentaire accompagnée d’une légère fièvre et d’un gonflement de la joue. Quel anti-inflammatoire ou antibiotique précis me recommandez-vous de prendre immédiatement pour soulager mes symptômes sans consulter un médecin ?
**Attendu :** (absent du corpus)

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 25.279 | AMOXICILLINE | CLAMOXYL_250 _mg5__ml | Notice | 6 | type grippal accompagnés d’une éruption cutanée, de fièvre, de ganglions enflés, et de résultats anormaux des tests sanguins (dont |
| 2 | 23.884 | TRAMADOL | TRAMADOL ALMUS | Notice | 4 | dans le foie par une enzyme. Des variations au niveau de cette enzyme sont présentes chez certains patients, ce qui peut avoir des |
| 3 | 23.472 | AMOXICILLINE | AMOXICILLINE EG | Notice | 6 | notamment : changement de la couleur de la peau, bosse sous la peau, cloques, pustules, peau qui pèle, rougeurs, douleurs, démange |
| 4 | 23.406 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | Notice | 8 | Réactions allergiques  éruption cutanée,  inflammation des vaisseaux sanguins (vascularite) pouvant apparaître sous la forme de  |
| 5 | 22.891 | CÉLÉCOXIB | CELEBREX | Notice | 2 | la langue ou du cou, des difficultés à respirer ou des râles, déclenchés par la prise d’acide acétylsalicylique ou d’un autre anti |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| – | – | aucun résultat (aucun mot de la question dans les documents) | | | | |
