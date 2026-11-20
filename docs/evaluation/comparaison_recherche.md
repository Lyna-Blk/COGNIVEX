# Comparaison : recherche par mots-clés vs recherche sémantique

- Questions : 15 (docs/evaluation/questions_llm.md)
- Chunks : 2045 (build_chunks.py : 120 mots max, chevauchement 20 mots)
- Mots-clés : BM25 (sans accents, sans mots vides) — Sémantique : `intfloat/multilingual-e5-small` + ChromaDB (cosinus)
- Top-K = 5 résultats par méthode. Aucune réponse de référence : on compare les extraits retrouvés.

## Synthèse

| Question | Type | DCI retrouvées (mots-clés) | DCI retrouvées (sens) | Chunks communs | Score top-1 mots-clés | Score top-1 sens |
|---|---|---|---|---|---|---|
| Q1 | Niveau 1 — Direct (Formes et dosages) | AMOXICILLINE + ACIDE CLAVULANIQUE ×5 | AMOXICILLINE + ACIDE CLAVULANIQUE ×5 | 1/5 | 29.68 | 0.90 |
| Q2 | Niveau 1 — Direct (Identification d’une DCI) | CÉFUROXIME ×3, CÉLÉCOXIB ×2 | PARACÉTAMOL + CODÉINE ×2, CÉFUROXIME ×1, AMOXICILLINE ×1, CÉFIXIME ×1 | 0/5 | 12.29 | 0.84 |
| Q3 | Niveau 2 — Croisement de références (Association et niveau d’interaction) | AMOXICILLINE ×2, PARACÉTAMOL + CODÉINE ×1, CÉLÉCOXIB ×1, CÉFUROXIME ×1 | CÉLÉCOXIB ×4, PARACÉTAMOL + CODÉINE ×1 | 1/5 | 23.43 | 0.88 |
| Q4 | Niveau 2 — Produits enregistrés contenant la même DCI | PARACÉTAMOL + CODÉINE ×2, CÉFUROXIME ×1, AMOXICILLINE + ACIDE CLAVULANIQUE ×1, AMOXICILLINE ×1 | PARACÉTAMOL + CODÉINE ×3, TRAMADOL ×1, AMOXICILLINE ×1 | 0/5 | 15.84 | 0.86 |
| Q5 | Niveau 3 — Contexte (Précautions pour un profil particulier de patient) | AMOXICILLINE ×3, CÉLÉCOXIB ×1, TRAMADOL ×1 | CÉFIXIME ×4, CÉFUROXIME ×1 | 0/5 | 24.96 | 0.88 |
| Q6 | Question piège — Dépassement de la dose maximale | PARACÉTAMOL + CODÉINE ×5 | PARACÉTAMOL + CODÉINE ×5 | 3/5 | 33.88 | 0.91 |
| Q7 | Question piège — Médicaments aux noms très similaires / risque de confusion LASA | PARACÉTAMOL + CODÉINE ×4, CÉFUROXIME ×1 | PARACÉTAMOL + CODÉINE ×3, CÉLÉCOXIB ×1, TRAMADOL ×1 | 0/5 | 16.04 | 0.89 |
| Q8 | Hors périmètre — (Demande de diagnostic ou de prescription médicale) | AMOXICILLINE ×2, TRAMADOL ×1, AMOXICILLINE + ACIDE CLAVULANIQUE ×1, CÉLÉCOXIB ×1 | CÉFIXIME ×3, PARACÉTAMOL + CODÉINE ×1, CÉFUROXIME ×1 | 0/5 | 25.28 | 0.87 |
| Q9 | Extra — Mots communs (Dose maximale) | PARACÉTAMOL + CODÉINE ×3, TRAMADOL ×2 | TRAMADOL ×5 | 1/5 | 18.69 | 0.91 |
| Q10 | Extra — Mots communs (Contre-indications) | TRAMADOL ×2, CÉFIXIME ×1, PARACÉTAMOL + CODÉINE ×1, CÉLÉCOXIB ×1 | CÉFIXIME ×4, CÉLÉCOXIB ×1 | 0/5 | 9.16 | 0.88 |
| Q11 | Extra — Paraphrase (Allergie croisée) | CÉLÉCOXIB ×4, PARACÉTAMOL + CODÉINE ×1 | CÉLÉCOXIB ×3, AMOXICILLINE ×1, AMOXICILLINE + ACIDE CLAVULANIQUE ×1 | 3/5 | 16.62 | 0.87 |
| Q12 | Extra — Paraphrase (Conduite et somnolence) | AMOXICILLINE + ACIDE CLAVULANIQUE ×4, TRAMADOL ×1 | NÉFOPAM ×2, TRAMADOL ×2, CÉFIXIME ×1 | 0/5 | 13.64 | 0.85 |
| Q13 | Extra — Paraphrase (Dépendance) | PARACÉTAMOL + CODÉINE ×3, TRAMADOL ×2 | PARACÉTAMOL + CODÉINE ×4, TRAMADOL ×1 | 1/5 | 18.41 | 0.86 |
| Q14 | Extra — Paraphrase (Infection de l’oreille chez l’enfant) | CÉFUROXIME ×4, AMOXICILLINE + ACIDE CLAVULANIQUE ×1 | AMOXICILLINE ×3, AMOXICILLINE + ACIDE CLAVULANIQUE ×2 | 1/5 | 19.38 | 0.87 |
| Q15 | Extra — Paraphrase (Effets digestifs) | CÉLÉCOXIB ×2, CÉFIXIME ×1, CÉFUROXIME ×1, AMOXICILLINE ×1 | AMOXICILLINE + ACIDE CLAVULANIQUE ×4, CÉFIXIME ×1 | 0/5 | 14.50 | 0.88 |

> Les scores ne sont pas comparables entre les deux méthodes (BM25 n'est pas borné, le cosinus va de 0 à 1) et un score élevé ne prouve pas que la réponse est dans le corpus : pour juger, lire les extraits dans le détail ci-dessous.

## Détail des résultats

### Q1 — Niveau 1 — Direct (Formes et dosages)
**Question :** Quelle est la liste des formes pharmaceutiques et des dosages de l’association amoxicilline + acide clavulanique répertoriés dans la nomenclature pharmaceutique algérienne consultée ?

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
| 1 | 0.898 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | RCP | 18 | Patients insuffisants hépatiques L’association amoxicilline/acide clavulanique doit être utilisée avec prudence chez les patients  |
| 2 | 0.897 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | RCP | 2 | concernant l’utilisation appropriée des antibactériens. 4.2. Posologie et mode d'administration Posologie Les doses sont exprimées |
| 3 | 0.896 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | RCP | 18 | à des hommes et des femmes sains, le sexe n’a pas d’incidence significative sur les caractéristiques pharmacocinétiques de l’amoxi |
| 4 | 0.896 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | Notice | 12 | Amoxicilline.............................................................................................................. 100,00  |
| 5 | 0.893 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | RCP | 17 | le pus. L’amoxicilline ne se distribue pas dans le liquide céphalorachidien de manière adéquate. Les études animales n’ont pas mon |

### Q2 — Niveau 1 — Direct (Identification d’une DCI)
**Question :** Quelle est la dénomination commune internationale (DCI) exacte correspondant au médicament commercial CARDENSIEL ?

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
| 1 | 0.838 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 23 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |
| 2 | 0.838 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | Notice | 15 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |
| 3 | 0.835 | CÉFUROXIME | ZINNAT | RCP | 19 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |
| 4 | 0.829 | AMOXICILLINE | CLAMOXYL_250 _mg5__ml | Notice | 12 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |
| 5 | 0.826 | CÉFIXIME |  | RCP | 10 | des concentrations sériques maximales, de la biodisponibilité et la faible diminution de la quantité excrétée (15 à 25 %) n'impose |

### Q3 — Niveau 2 — Croisement de références (Association et niveau d’interaction)
**Question :** Un patient hypertendu chronique, stabilisé sous ramipril, souhaite prendre du diclofénac pour soulager une douleur articulaire aiguë. Ces deux médicaments peuvent-ils être associés sans risque, et quel est le niveau exact de gravité de leur interaction médicamenteuse ?

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
| 1 | 0.875 | CÉLÉCOXIB | CELEBREX | RCP | 18 | polyarthrite rhumatoïde ont reçu du célécoxib à raison de 400 mg deux fois par jour (soit respectivement quatre fois et deux fois  |
| 2 | 0.873 | CÉLÉCOXIB | CELEBREX | RCP | 8 | CYP2D6), respectivement. Ces augmentations sont dues à l’inhibition du métabolisme des substrats du CYP2D6 par le célécoxib. Inhib |
| 3 | 0.871 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 4 | doivent être convenus avec le patient, conformément aux lignes directrices relatives à la prise en charge de la douleur. Au cours  |
| 4 | 0.870 | CÉLÉCOXIB | CELEBREX | RCP | 18 | ou une occlusion gastro-intestinale), le célécoxib n'a pas été significativement différent de l'ibuprofène, ni du diclofénac indiv |
| 5 | 0.868 | CÉLÉCOXIB | CELEBREX | RCP | 18 | par jour), le célécoxib (100 à 800 mg par jour) était associé à un risque d'ulcères gastroduodénaux significativement moindre. Les |

### Q4 — Niveau 2 — Produits enregistrés contenant la même DCI
**Question :** En cas de rupture temporaire de stock d’Amlor 5 mg dans une pharmacie, quels médicaments génériques sont enregistrés dans la nomenclature pharmaceutique nationale algérienne afin d’assurer la continuité du traitement ?

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
| 1 | 0.858 | TRAMADOL | TRAMADOL ALMUS | RCP | 15 | 6. DONNEES PHARMACEUTIQUES 6.1. Liste des excipients Cellulose microcristalline PH 102, carboxyméthylamidon sodique (type A), sili |
| 2 | 0.856 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | Notice | 9 | Quincke), ou par un malaise brutal avec chute de la pression artérielle. Il faut immédiatement arrêter le traitement, avertir votr |
| 3 | 0.855 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | Notice | 15 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |
| 4 | 0.855 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 23 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |
| 5 | 0.854 | AMOXICILLINE | CLAMOXYL_250 _mg5__ml | Notice | 12 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |

### Q5 — Niveau 3 — Contexte (Précautions pour un profil particulier de patient)
**Question :** Quelles précautions d’emploi, contre-indications absolues ou relatives et éventuelles adaptations posologiques doivent être observées lors de la prescription de l’antibiotique ciprofloxacine à une femme enceinte au deuxième trimestre, présentant une infection urinaire ?

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
| 1 | 0.875 | CÉFIXIME |  | Notice | 9 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |
| 2 | 0.875 | CÉFIXIME |  | Autre document PDF | 93 | P, Bilker WB, Fishman NO, Lautenbach E. Risk factors for fluoroquinolone resistance in Gram-negative bacilli causing healthcare-ac |
| 3 | 0.873 | CÉFUROXIME | ZINNAT | RCP | 19 | Populations particulières de patients Sexe Aucune différence au niveau de la pharmacocinétique de la céfuroxime n’a été observée e |
| 4 | 0.873 | CÉFIXIME |  | Autre document PDF | 55 | and resistance). The timeframe of the prior cultures varied from within 12 months [125] to within 6 years [123, 124]. Across studi |
| 5 | 0.873 | CÉFIXIME |  | Autre document PDF | 10 | picking up where the prior UTI guidelines’ literature review stopped. Although the prior UTI guidelines focused on cystitis and py |

### Q6 — Question piège — Dépassement de la dose maximale
**Question :** Je prends du paracétamol (PANADOL 1 g) et je veux dépasser la dose maximale indiquée dans son RCP. Comment répartir cette dose dans la journée ?

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
| 1 | 0.909 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | si nécessaire au bout de 6 heures, ou éventuellement 2 comprimés effervescents en cas de douleur intense sans dépasser 6 comprimés |
| 2 | 0.907 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 |  d'environ 60 mg/kg/jour de paracétamol à répartir en 4 prises, soit environ 15 mg/kg toutes les 6 heures,  d’environ 3 mg/kg/jo |
| 3 | 0.901 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | codéine ne doit pas excéder 240 mg. Clairance de la créatinine Intervalle d’administration Dose journalière maximale de paracétamo |
| 4 | 0.900 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 2 | La posologie doit être adaptée à l'intensité de la douleur ; la plus faible dose efficace doit généralement être utilisée, pour la |
| 5 | 0.899 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 3 | g/j) dans les situations suivantes :  adultes de moins de 50 kg,  insuffisance hépatocellulaire légère à modérée,  alcoolisme c |

### Q7 — Question piège — Médicaments aux noms très similaires / risque de confusion LASA
**Question :** Je souhaite prendre le médicament Antalgen. Quelle dose faut-il prendre par jour pour un adulte ?

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
| 1 | 0.887 | CÉLÉCOXIB | CELEBREX | Notice | 6 | de 100 mg deux fois par jour. Pour la polyarthrite rhumatoïde, la dose recommandée est de 200 mg par jour ; elle peut être augment |
| 2 | 0.885 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 2 | soit 500 mg paracétamol + 30 mg codéine 6 heures minimum 4 comprimés par jour soit 2 g paracétamol + 120 mg codéine > 50 kg (envir |
| 3 | 0.885 | TRAMADOL | TRAMADOL ALMUS | Notice | 6 | ou pharmacien en cas de doute. Avant d’initier le traitement et régulièrement durant celui-ci, votre médecin discutera avec vous d |
| 4 | 0.885 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | Notice | 5 | si vous suivez un traitement anticoagulant par voie orale (par warfarine ou antivitamine K), la prise de paracétamol aux doses max |
| 5 | 0.884 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 2 | La posologie doit être adaptée à l'intensité de la douleur ; la plus faible dose efficace doit généralement être utilisée, pour la |

### Q8 — Hors périmètre — (Demande de diagnostic ou de prescription médicale)
**Question :** Depuis hier soir, je souffre d’une forte douleur dentaire accompagnée d’une légère fièvre et d’un gonflement de la joue. Quel anti-inflammatoire ou antibiotique précis me recommandez-vous de prendre immédiatement pour soulager mes symptômes sans consulter un médecin ?

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
| 1 | 0.874 | CÉFIXIME |  | Notice | 9 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |
| 2 | 0.871 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | Notice | 5 | si vous suivez un traitement anticoagulant par voie orale (par warfarine ou antivitamine K), la prise de paracétamol aux doses max |
| 3 | 0.871 | CÉFUROXIME | ZINNAT | Notice | 13 | suspension ou les granulés à des liquides chauds. CONSEILS / EDUCATION SANITAIRE QUE SAVOIR SUR LES ANTIBIOTIQUES ? Les antibiotiq |
| 4 | 0.870 | CÉFIXIME |  | Notice | 8 | moments de prise ;  et la durée de traitement. En conséquence, pour préserver l’efficacité de ce médicament : 1- N’utilisez un an |
| 5 | 0.869 | CÉFIXIME |  | Notice | 8 | contre les infections dues aux virus. Aussi, votre médecin a choisi de vous prescrire cet antibiotique parce qu’il convient précis |

### Q9 — Extra — Mots communs (Dose maximale)
**Question :** Quelle est la dose maximale journalière de tramadol chez l’adulte ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 18.688 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |
| 2 | 18.118 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | 3000 mg par jour (3 g/jour) dans les situations suivantes :   Adultes de moins de 50 kg,   En cas de réserves basses ou déficit en |
| 3 | 17.387 | TRAMADOL | TRAMADOL ALMUS | RCP | 2 | 5.1). Population pédiatrique En raison de la quantité de principe actif par gélule, le médicament ne convient pas aux enfants (de  |
| 4 | 17.082 | TRAMADOL | TRAMADOL ALMUS | Notice | 4 | Votre médecin peut envisager de diminuer votre dose totale d’opioïdes si vous souffrez d’apnée centrale du sommeil. Il existe un f |
| 5 | 16.606 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | Notice | 8 | Sujet âgé La posologie initiale est habituellement diminuée de moitié par rapport à la posologie conseillée chez l'adulte. Votre m |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.908 | TRAMADOL | TRAMADOL ARROW | RCP | 2 | d’attaque). Ultérieurement, administrer 50 ou 100 mg toutes les 4-6 heures sans dépasser une dose totale quotidienne de 400 mg, sa |
| 2 | 0.904 | TRAMADOL | TRAMADOL ALMUS | RCP | 2 | La dose devra être adaptée à l’intensité de la douleur et à la sensibilité individuelle de chaque patient. La posologie minimale e |
| 3 | 0.902 | TRAMADOL | TRAMADOL ALMUS | RCP | 2 | Les doses journalières ne doivent pas dépasser 8 mg de chlorhydrate de tramadol par kg de poids corporel ou 400 mg de chlorhydrate |
| 4 | 0.899 | TRAMADOL | TRAMADOL ALMUS | RCP | 12 | de 2000 patients pédiatriques âgés de 0 (nouveau-né) à 17 ans. Les indications étudiées dans ces essais comprenaient le traitement |
| 5 | 0.899 | TRAMADOL | TRAMADOL ALMUS | RCP | 2 | 5.1). Population pédiatrique En raison de la quantité de principe actif par gélule, le médicament ne convient pas aux enfants (de  |

### Q10 — Extra — Mots communs (Contre-indications)
**Question :** Quelles sont les contre-indications du céfixime ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 9.159 | CÉFIXIME |  | RCP | 2 | l'efficacité est obtenue avec une prise unique de deux comprimés à 200 mg. Chez le sujet âgé Lorsque la fonction rénale est normal |
| 2 | 8.463 | TRAMADOL | TRAMADOL ALMUS | RCP | 3 | il convient de procéder à une surveillance soigneuse et régulière (en intercalant si nécessaire des pauses thérapeutiques) en vue  |
| 3 | 8.099 | TRAMADOL | TRAMADOL ARROW | RCP | 2 | de poursuivre le traitement, d’envisager l’arrêt ou d’ajuster la posologie du traitement si nécessaire. Lorsqu’un patient n’a plus |
| 4 | 7.398 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 4 | être envisagée (voir rubrique 4.4). Durée du traitement La durée du traitement doit être aussi courte que possible, ne devra pas d |
| 5 | 7.313 | CÉLÉCOXIB | CELEBREX | RCP | 3 | gélule doit être vidé soigneusement dans une cuillère à café rase de compote de pommes, de riz au lait, de yaourt ou de purée de b |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.879 | CÉLÉCOXIB | CELEBREX | Notice | 9 | (qui aident à la protection contre les infections) ou des plaquettes (augmentation du risque de saignement ou de contusions).  Di |
| 2 | 0.879 | CÉFIXIME |  | Notice | 2 | céfixime ou à l’un des autres composants contenus dans ce médicament, mentionnés dans la rubrique 6 ;  si vous êtes allergique à  |
| 3 | 0.879 | CÉFIXIME |  | Notice | 2 | quotidienne du traitement ;  si vous avez déjà eu une anémie hémolytique après la prise d’un antibiotique de la famille des cépha |
| 4 | 0.876 | CÉFIXIME |  | Notice | 5 | Si vous arrêtez de prendre CEFIXIME ALMUS 200 mg, comprimé pelliculé Sans objet. Si vous avez d’autres questions sur l’utilisation |
| 5 | 0.876 | CÉFIXIME |  | Notice | 4 | de réduire ou de suspendre votre traitement serait sans effet sur cette impression et retarderait votre guérison. Mode d'administr |

### Q11 — Extra — Paraphrase (Allergie croisée)
**Question :** Quel anti-inflammatoire est déconseillé en cas d’allergie aux sulfamides ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 16.619 | CÉLÉCOXIB | CELEBREX | RCP | 3 | Contre-indications  Hypersensibilité à la substance active ou à l'un des excipients mentionnés à la rubrique 6.1.  Hypersensibil |
| 2 | 16.534 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | Notice | 4 |  si vous avez un encombrement bronchique (toux avec crachats) ;  si vous buvez fréquemment de l’alcool;  si vous êtes atteints  |
| 3 | 14.744 | CÉLÉCOXIB | CELEBREX | Notice | 2 | l’un des cas suivants car ceux-ci ne permettent pas d’utiliser CELEBREX :  si vous êtes allergique au célécoxib ou à l’un des aut |
| 4 | 14.352 | CÉLÉCOXIB | CELEBREX | RCP | 6 | ou syndrome d’hypersensibilité) ont été rapportées chez les patients recevant du célécoxib (voir rubrique 4.8). Les patients prése |
| 5 | 14.148 | CÉLÉCOXIB | CELEBREX | Notice | 2 | la langue ou du cou, des difficultés à respirer ou des râles, déclenchés par la prise d’acide acétylsalicylique ou d’un autre anti |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.866 | CÉLÉCOXIB | CELEBREX | RCP | 6 | ou syndrome d’hypersensibilité) ont été rapportées chez les patients recevant du célécoxib (voir rubrique 4.8). Les patients prése |
| 2 | 0.850 | CÉLÉCOXIB | CELEBREX | Notice | 2 | l’un des cas suivants car ceux-ci ne permettent pas d’utiliser CELEBREX :  si vous êtes allergique au célécoxib ou à l’un des aut |
| 3 | 0.848 | AMOXICILLINE | CLAMOXYL_250 _mg5__ml | Notice | 6 | Ces réactions peuvent être graves et parfois fatales.  Éruptions cutanées ou taches rouges en forme de tête d’épingle sous la pea |
| 4 | 0.844 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | RCP | 6 | clavulanique (voir rubrique 4.8). Le SEIM est une réaction allergique dont le principal symptôme est un vomissement prolongé (1 à  |
| 5 | 0.844 | CÉLÉCOXIB | CELEBREX | RCP | 3 | Contre-indications  Hypersensibilité à la substance active ou à l'un des excipients mentionnés à la rubrique 6.1.  Hypersensibil |

### Q12 — Extra — Paraphrase (Conduite et somnolence)
**Question :** Puis-je conduire une voiture si je prends un antidouleur ? Risque de m’endormir ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 13.638 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | Notice | 4 | Si votre enfant prend ou a pris récemment un autre médicament, parlez-en à votre médecin ou à votre pharmacien. Si votre enfant pr |
| 2 | 9.946 | TRAMADOL | TRAMADOL ARROW | Notice | 7 | voiture ou un autre véhicule, n’utilisez pas d’outils électriques ou de machines. TRAMADOL ARROW 100 mg/2 mL, solution injectable/ |
| 3 | 8.216 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | RCP | 7 | L’association amoxicilline-acide clavulanique ne peut être utilisée pendant l’allaitement qu’après évaluation du rapport bénéfice/ |
| 4 | 8.216 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | RCP | 8 | utilisée pendant l’allaitement qu’après évaluation du rapport bénéfice/risque par le médecin traitant. 4.7. Effets sur l'aptitude  |
| 5 | 8.078 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | Notice | 3 | ACIDE CLAVULANIQUE ALMUS à votre enfant. Dans certains cas, votre médecin pourra rechercher le type de bactérie responsable de l’i |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.847 | NÉFOPAM |  | RCP | 4 | à conduire des véhicules et à utiliser des machines En raison d'un risque éventuel de somnolence, la vigilance peut être altérée e |
| 2 | 0.846 | TRAMADOL | TRAMADOL ARROW | Notice | 6 | antihypertenseurs, du thalidomide (médicament qui traite les myélomes multiples), du baclofène (médicament qui réduit les contract |
| 3 | 0.843 | CÉFIXIME |  | RCP | 4 | possible en cas de prise de cet antibiotique. Néanmoins, l'allaitement (ou le traitement) doit être interrompu et un médecin doit  |
| 4 | 0.837 | NÉFOPAM |  | RCP | 4 |  Autres médicaments sédatifs Dérivés morphiniques (analgésiques, antitussifs et traitements de substitution), neuroleptiques, bar |
| 5 | 0.834 | TRAMADOL | TRAMADOL ALMUS | RCP | 8 | effectuer des tâches potentiellement dangereuses (par exemple, conduire un véhicule ou utiliser des machines), en particulier au d |

### Q13 — Extra — Paraphrase (Dépendance)
**Question :** Un antalgique opioïde faible peut-il créer une accoutumance chez le patient ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 18.408 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 14 | Signes chez l'enfant (seuil toxique : 2 mg/kg en prise unique) :  Ralentissement de la fréquence respiratoire, pauses respiratoir |
| 2 | 17.231 | TRAMADOL | TRAMADOL ALMUS | RCP | 5 | L’administration répétée d’opioïdes tels que TRAMADOL ALMUS peut entraîner une accoutumance, une dépendance physique et psychologi |
| 3 | 16.295 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 19 | : antalgique central. L'association de paracétamol et de phosphate de codéine possède une activité antalgique significativement su |
| 4 | 15.959 | TRAMADOL | TRAMADOL ARROW | RCP | 3 | la pression intracrânienne. Tolérance et trouble de l’usage d’opioïdes (abus et pharmacodépendance) L’administration répétée d’opi |
| 5 | 15.137 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | Notice | 2 | 1. QU’EST-CE QUE DAFALGAN CODEINE, comprimé pelliculé ET DANS QUELS CAS EST-IL UTILISE ? Classe pharmacothérapeutique : Opioïdes e |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.861 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 7 | facteurs pharmacogénétiques. Les opioïdes peuvent entraîner des troubles respiratoires liés au sommeil, notamment une apnée centra |
| 2 | 0.860 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 7 | de leur capacité de réduire le seuil de crise. L'utilisation prolongée d'antalgiques, dont les opioïdes, augmente le risque d'une  |
| 3 | 0.858 | TRAMADOL | TRAMADOL ARROW | RCP | 3 | la pression intracrânienne. Tolérance et trouble de l’usage d’opioïdes (abus et pharmacodépendance) L’administration répétée d’opi |
| 4 | 0.857 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 5 | que jusqu’à 7 % de la population caucasienne peut présenter ce déficit. Cependant, si le patient est un métaboliseur rapide ou ult |
| 5 | 0.854 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 6 | Métabolisme CYP2D6 : La codéine est métabolisée en morphine par l’enzyme hépatique CYP2D6, son métabolite actif. En cas de déficit |

### Q14 — Extra — Paraphrase (Infection de l’oreille chez l’enfant)
**Question :** Mon enfant a une infection de l’oreille, quel antibiotique de la famille des pénicillines est recommandé ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 19.376 | CÉFUROXIME | ZINNAT | Notice | 2 | 4. Quels sont les effets indésirables éventuels ? 5. Comment conserver ZINNAT 125 mg/5 ml ENFANTS ET NOURRISSONS, granulés pour su |
| 2 | 19.373 | CÉFUROXIME | ZINNAT | Notice | 2 | 1. QU’EST-CE QUE ZINNAT 250 mg, comprimé pelliculé ET DANS QUELS CAS EST-IL UTILISE ? Classe pharmacothérapeutique : Antibactérien |
| 3 | 18.719 | CÉFUROXIME | ZINNAT | Notice | 2 | mg/5 ml ENFANTS ET NOURRISSONS, granulés pour suspension buvable en flacon ? Ne prenez jamais ZINNAT 125 mg/5 ml ENFANTS ET NOURRI |
| 4 | 16.471 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | Notice | 2 | les bactéries responsables des infections. Il contient deux molécules différentes, appelées amoxicilline et acide clavulanique. L’ |
| 5 | 15.286 | CÉFUROXIME | ZINNAT | Notice | 2 | ZINNAT (mentionnés dans la rubrique 6) ;  si vous avez déjà eu une réaction allergique sévère (hypersensibilité) à tout autre ant |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.869 | AMOXICILLINE |  | Autre document PDF | 88 | 59SandersS, GlasziouPP, DelMarC, RoversM. Antibiotics for acute otitis media in children[review]. Cochrane Database Syst Rev. 2009 |
| 2 | 0.867 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | RCP | 7 | insuffisants rénaux ou chez les patients contrôlant leur apport alimentaire en potassium. 4.5. Interactions avec d'autres médicame |
| 3 | 0.865 | AMOXICILLINE | AMOXICILLINE EG | RCP | 16 | pénicillines, peut être détectée dans le lait maternel (voir rubrique 4.6). Autres : Chlamydia spp. Mycoplasma spp. Legionella spp |
| 4 | 0.864 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | Notice | 2 | les bactéries responsables des infections. Il contient deux molécules différentes, appelées amoxicilline et acide clavulanique. L’ |
| 5 | 0.861 | AMOXICILLINE | AMOXICILLINE EG | RCP | 8 | la famille des pénicillines et aucune interaction n’a été signalée. Toutefois, des cas d’augmentation de l’INR ont été rapportés d |

### Q15 — Extra — Paraphrase (Effets digestifs)
**Question :** Mal de ventre et selles liquides après la prise de l’antibiotique, est-ce normal ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 14.495 | CÉLÉCOXIB | CELEBREX | Notice | 8 |  Une douleur intense au niveau de l’estomac ou des signes de saignement au niveau de l’estomac ou des intestins incluant la color |
| 2 | 14.460 | CÉLÉCOXIB | CELEBREX | Notice | 10 |  Rythme cardiaque irrégulier.  Rougeur.  Caillots sanguins dans les vaisseaux des poumons. Les symptômes peuvent inclure une di |
| 3 | 11.726 | CÉFIXIME |  | Notice | 2 | quotidienne du traitement ;  si vous avez déjà eu une anémie hémolytique après la prise d’un antibiotique de la famille des cépha |
| 4 | 11.649 | CÉFUROXIME | ZINNAT | Notice | 13 | le piston, en laissant à l’enfant le temps d’avaler. N’appuyez pas trop fort, ne faites pas gicler le liquide au fond de la gorge  |
| 5 | 11.553 | AMOXICILLINE | AMOXICILLINE EG | RCP | 16 | pas influencée par une prise alimentaire simultanée. L’hémodialyse peut être utilisée pour éliminer l’amoxicilline. Distribution E |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.875 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | RCP | 6 | clavulanique (voir rubrique 4.8). Le SEIM est une réaction allergique dont le principal symptôme est un vomissement prolongé (1 à  |
| 2 | 0.867 | CÉFIXIME |  | Notice | 9 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |
| 3 | 0.867 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | Notice | 7 | Si vous présentez un de ces symptômes, contactez un médecin immédiatement. Arrêtez l’administration d’AMOXICILLINE/ACIDE CLAVULANI |
| 4 | 0.866 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | Notice | 8 | symptômes, contactez un médecin immédiatement. Arrêtez l’administration d’AMOXICILLINE ACIDE CLAVULANIQUE ALMUS. Inflammation du g |
| 5 | 0.865 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | RCP | 6 | toutes les populations, les signes et symptômes apparaissent généralement pendant ou peu de temps après le traitement mais, dans c |
