# Comparaison : recherche par mots-clés vs recherche sémantique

- Questions : 8 (docs/evaluation/questions_llm.md)
- Chunks : 3989 (build_chunks.py : 120 mots max, chevauchement 20 mots)
- Mots-clés : BM25 (sans accents, sans mots vides) — Sémantique : `intfloat/multilingual-e5-small` + ChromaDB (cosinus)
- Top-K = 5 résultats par méthode. Aucune réponse de référence : on compare les extraits retrouvés.

## Synthèse

| Question | Type | DCI retrouvées (mots-clés) | DCI retrouvées (sens) | Chunks communs | Score top-1 mots-clés | Score top-1 sens |
|---|---|---|---|---|---|---|
| Q1 | Niveau 1 — Direct (Formes et dosages) | AMOXICILLINE + ACIDE CLAVULANIQUE ×5 | AMOXICILLINE + ACIDE CLAVULANIQUE ×5 | 1/5 | 27.97 | 0.90 |
| Q2 | Niveau 1 — Direct (Identification d’une DCI) | PARACETAMOL ×2, AMLODIPINE ×1, KETOPROFENE ×1, PIROXICAM ×1 | PARACETAMOL ×2, PERINDOPRIL ×1, CLINDAMYCINE ×1, PARACÉTAMOL + CODÉINE ×1 | 2/5 | 25.42 | 0.84 |
| Q3 | Niveau 2 — Croisement de références (Association et niveau d’interaction) | PERINDOPRIL ×3, KETOPROFENE ×1, MÉTHYLDOPA ×1 | DICLOFENAC ×5 | 0/5 | 22.94 | 0.90 |
| Q4 | Niveau 2 — Produits enregistrés contenant la même DCI | AMLODIPINE ×5 | AMLODIPINE ×3, CLINDAMYCINE ×1, GENTAMICINE ×1 | 3/5 | 29.65 | 0.89 |
| Q5 | Niveau 3 — Contexte (Précautions pour un profil particulier de patient) | DICLOFENAC ×2, AMLODIPINE ×2, VALSARTAN ×1 | PIROXICAM ×3, VALSARTAN ×2 | 0/5 | 26.10 | 0.88 |
| Q6 | Question piège — Dépassement de la dose maximale | PARACÉTAMOL + CODÉINE ×4, PARACETAMOL ×1 | PARACÉTAMOL + CODÉINE ×4, PARACETAMOL ×1 | 2/5 | 34.25 | 0.91 |
| Q7 | Question piège — Médicaments aux noms très similaires / risque de confusion LASA | SPIRONOLACTONE ×2, BISOPROLOL ×1, CÉFUROXIME ×1, VALSARTAN ×1 | VALSARTAN ×3, MELOXICAM ×1, ATÉNOLOL ×1 | 0/5 | 16.62 | 0.90 |
| Q8 | Hors périmètre — (Demande de diagnostic ou de prescription médicale) | DICLOFENAC ×2, MELOXICAM ×2, AMOXICILLINE ×1 | CÉFIXIME ×1, CLINDAMYCINE ×1, VALSARTAN ×1, INDAPAMIDE ×1, CÉFUROXIME ×1 | 0/5 | 26.33 | 0.87 |

> Les scores ne sont pas comparables entre les deux méthodes (BM25 n'est pas borné, le cosinus va de 0 à 1) et un score élevé ne prouve pas que la réponse est dans le corpus : pour juger, lire les extraits dans le détail ci-dessous.

## Détail des résultats

### Q1 — Niveau 1 — Direct (Formes et dosages)
**Question :** Quelle est la liste des formes pharmaceutiques et des dosages de l’association amoxicilline + acide clavulanique répertoriés dans la nomenclature pharmaceutique algérienne consultée ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 27.973 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | RCP | 1 | 224 doses- graduations (1 dose = 1 kg). Excipients à effet notoire : aspartam (E951), maltodextrine (source de glucose), potassium |
| 2 | 26.814 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | RCP | 18 | Patients insuffisants hépatiques L’association amoxicilline/acide clavulanique doit être utilisée avec prudence chez les patients  |
| 3 | 26.632 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | RCP | 20 | Patients insuffisants hépatiques L’association amoxicilline/acide clavulanique doit être utilisée avec prudence chez les patients  |
| 4 | 26.068 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg | RCP | 1 | Dernière mise à jour le 03/11/2026 AMOXICILLINE/ACIDE CLAVULANIQUE SANDOZ 1 g/200 mg, poudre pour solution injectable/pour perfusi |
| 5 | 22.186 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS | RCP | 18 | PHARMACEUTIQUES 6.1. Liste des excipients Acide succinique, gomme xanthane, silice colloïdale anhydre, aspartam, arôme E99-294-55  |

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
| 1 | 25.421 | AMLODIPINE | mibral | RCP | 1 | ANNEXE I RESUME DES CARACTERISTIQUES DU PRODUIT 1 Email : contact@ldmgroupe.com CONSTANTINE : Oued Hamimime – 25100 El Khroub – Té |
| 2 | 22.670 | KETOPROFENE | koprofen | RCP | 1 | ANNEXE I RESUME DES CARACTERISTIQUES DU PRODUIT 1 Email : contact@ldmgroupe.com CONSTANTINE : Oued Hamimime – 25100 El Khroub – Té |
| 3 | 22.264 | PIROXICAM |  | RCP | 1 | RÉSUMÉ DES CARACTÉRISTIQUES DU PRODUIT PAINOXAM ® suppositoire 20 mg, boite de 15 Code : E0002/3.07.0002/TR Version : 02 Page 1 su |
| 4 | 22.076 | PARACETAMOL | panadol | RCP | 1 | ANNEXE I RESUME DES CARACTERISTIQUES DU PRODUIT 1 Email : contact@ldmgroupe.com CONSTANTINE : Z.I Oued Hamimime – 25100 El Khroub  |
| 5 | 22.021 | PARACETAMOL | documents_complementaires_non_reference | RCP | 1 | ANNEXE I RESUME DES CARACTERISTIQUES DU PRODUIT 1. DENOMINATION DU MEDICAMENT 1.1 Dénomination commerciale, dosage et forme pharma |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.843 | PARACETAMOL | panadol | RCP | 1 | ANNEXE I RESUME DES CARACTERISTIQUES DU PRODUIT 1 Email : contact@ldmgroupe.com CONSTANTINE : Z.I Oued Hamimime – 25100 El Khroub  |
| 2 | 0.842 | PERINDOPRIL | perindosyl | Autre document PDF | OCR — pagination non précisée | listes plus bas. REPERES IDENTIFICATION PPA DCI(Substance PERINDOPRIL Prixnon disponible active) ERBUMINE DCI Nom de marque PERIND |
| 3 | 0.842 | CLINDAMYCINE | clinaram | Autre document PDF | OCR — pagination non précisée | a la notice .fournie avec la boite, ou demandezconseil a unmédecin ou a un pharmacien Voir la boite(Google) Touslesmedicaments ave |
| 4 | 0.841 | PARACETAMOL | documents_complementaires_non_reference | RCP | 1 | ANNEXE I RESUME DES CARACTERISTIQUES DU PRODUIT 1. DENOMINATION DU MEDICAMENT 1.1 Dénomination commerciale, dosage et forme pharma |
| 5 | 0.838 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 23 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |

### Q3 — Niveau 2 — Croisement de références (Association et niveau d’interaction)
**Question :** Un patient hypertendu chronique, stabilisé sous ramipril, souhaite prendre du diclofénac pour soulager une douleur articulaire aiguë. Ces deux médicaments peuvent-ils être associés sans risque, et quel est le niveau exact de gravité de leur interaction médicamenteuse ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 22.943 | KETOPROFENE | koprofen | RCP | 3 | ANNEXE I RESUME DES CARACTERISTIQUES DU PRODUIT 3 Email : contact@ldmgroupe.com CONSTANTINE : Oued Hamimime – 25100 El Khroub – Té |
| 2 | 22.359 | MÉTHYLDOPA |  | Notice | 4 | abdominal, constipation, flatulence, colite (inflammation du gros intestin), langue saburrale (recouverte d'un enduit blanc-jaunât |
| 3 | 22.330 | PERINDOPRIL | coversyl | Autre document PDF | OCR — pagination non précisée | conversion (IEC) non associes conversion (IEC) non associes perindopril Autresmedicaments aveclamemeDCI 1medicament(s)enregistre(s |
| 4 | 22.248 | PERINDOPRIL | coversyl | Autre document PDF | OCR — pagination non précisée | renine-angiotensine conversion (IEC) non associes conversion (IEC) non associes perindopril Autresmedicaments aveclamemeDCI 1medic |
| 5 | 21.966 | PERINDOPRIL | perindosyl | Autre document PDF | OCR — pagination non précisée | renine-angiotensine conversion (IEC) non associes conversion (IEC) non associes perindopril ★ Interactions médicamenteuses Interac |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.903 | DICLOFENAC | documents_complementaires_non_reference | RCP | 8 | l'association d’une IEC et d'un AINS, par exemple, est à moindre risque dès l'instant que sont mis en œuvre les précautions recomm |
| 2 | 0.901 | DICLOFENAC | biofenac | RCP | 10 | AINS, par exemple, est à moindre risque dès l’instant que sont mises en œuvre les précautions recommandées. Pour connaitre les ris |
| 3 | 0.896 | DICLOFENAC | biofenac | RCP | 10 | d’interaction : Risque lié à l’hyperkaliémie : Certains médicaments ou classes thérapeutiques sont susceptibles de favoriser la su |
| 4 | 0.894 | DICLOFENAC | documents_complementaires_non_reference | RCP | 8 | d’autres médicaments et autres formes d’interactions : Risque lié à l’hyperkaliémie : Certains médicaments ou classes thérapeutiqu |
| 5 | 0.893 | DICLOFENAC | documents_complementaires_non_reference | RCP | 11 | de facteurs de risque d'insuffisance rénale. En cas d’association, surveiller la fonction rénale. Associations à prendre en compte |

### Q4 — Niveau 2 — Produits enregistrés contenant la même DCI
**Question :** En cas de rupture temporaire de stock d’Amlor 5 mg dans une pharmacie, quels médicaments génériques sont enregistrés dans la nomenclature pharmaceutique nationale algérienne afin d’assurer la continuité du traitement ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 29.654 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | I'ANSM reproduits tels quels ; la substance du medicament est rapprochee automatiquement du thesaurus. Une erreur ? ~~Ecrivez-nous |
| 2 | 29.047 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | 1OMG es ~~t-~~ il enregistre en Algerie? Oui, AMLODAL 10MG figure dans la nomenclature nationale des produits pharmaceutiques (dat |
| 3 | 26.891 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | un medicament generique. ###### Quel laboratoirefabriqueAMLODAL1oMG? AMLODAL 1OMG est produit par le laboratoire PHARMIDAL NS (ALG |
| 4 | 26.389 | AMLODIPINE | mibral | Autre document PDF | OCR — pagination non précisée | zai ~~r~~ - ~~p~~ harma. ~~n~~ et/med ~~ic~~ ament/enreg ~~is~~ trement/1043/m ~~i~~ bra ~~l-~~ 10m ~~g-~~ gelule# ~~i~~ nterac ~~ |
| 5 | 25.338 | AMLODIPINE | mibral | Autre document PDF | OCR — pagination non précisée | nationale comme un médicament générique ? Quel laboratoire fabrique MIBRAL 10MG MIBRAL 1OMG est produit par le laboratoire LABORAT |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.894 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | 1OMG es ~~t-~~ il enregistre en Algerie? Oui, AMLODAL 10MG figure dans la nomenclature nationale des produits pharmaceutiques (dat |
| 2 | 0.883 | AMLODIPINE | mibral | Autre document PDF | OCR — pagination non précisée | zai ~~r~~ - ~~p~~ harma. ~~n~~ et/med ~~ic~~ ament/enreg ~~is~~ trement/1043/m ~~i~~ bra ~~l-~~ 10m ~~g-~~ gelule# ~~i~~ nterac ~~ |
| 3 | 0.872 | CLINDAMYCINE | acnestop | Autre document PDF | OCR — pagination non précisée | en Algérie Oui, ACNESTOP 1% (1OMG/ML) figure dans la nomenclature nationale des produits pharmaceutiques (date .d'enregistrement : |
| 4 | 0.872 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | I'ANSM reproduits tels quels ; la substance du medicament est rapprochee automatiquement du thesaurus. Une erreur ? ~~Ecrivez-nous |
| 5 | 0.872 | GENTAMICINE | s_genta | Autre document PDF | OCR — pagination non précisée | I'aminoside (insuffisance cochléovestibulaire,etéventuellement,des rénale fonctionnelle liée a la déshydratation concentrationspla |

### Q5 — Niveau 3 — Contexte (Précautions pour un profil particulier de patient)
**Question :** Quelles précautions d’emploi, contre-indications absolues ou relatives et éventuelles adaptations posologiques doivent être observées lors de la prescription de l’antibiotique ciprofloxacine à une femme enceinte au deuxième trimestre, présentant une infection urinaire ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 26.104 | DICLOFENAC | documents_complementaires_non_reference | RCP | 3 | d'exposition, la dose quotidienne efficace la plus faible doit être utilisée et pendant la durée la plus courte possible (voir rub |
| 2 | 25.414 | DICLOFENAC | documents_complementaires_non_reference | RCP | 3 | Insuffisance hépatique BIOFENAC FAST® est contre-indiqué chez les patients atteints d’insuffisance hépatique (voir rubrique 4.3 Co |
| 3 | 25.241 | VALSARTAN |  | RCP | 5 | TAREG n’est pas recommandé dans le traitement de l’insuffisance cardiaque ou de l’infarctus du myocarde récent chez les enfants et |
| 4 | 24.236 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | ~~-~~ avec les autres antagonistes des canaux calciques. Surveillance clinique et adaptation posologique pendant le traitement par |
| 5 | 24.182 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | TENIR Majoration des effets indesirables de I'antagoniste des canaux Association deconseillee: calciques, le plus souvent a type d |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.884 | VALSARTAN |  | RCP | 9 | II est contre-indiquée aux 2ème et 3ème trimestres de la grossesse (voir rubriques 4.3 et 4.4) Les données épidémiologiques dispon |
| 2 | 0.884 | PIROXICAM |  | RCP | 12 | grossesse, la mère et le nouveau-né peuvent présenter : · un allongement du temps de saignement du fait d’une action anti-agrégant |
| 3 | 0.882 | PIROXICAM |  | RCP | 2 | du traitement doivent être réévalués dans les 14 jours. Si la poursuite du traitement s'avère nécessaire, ce dernier devra être ac |
| 4 | 0.882 | VALSARTAN |  | RCP | 10 | modifier le traitement antihypertenseur pour un médicament ayant un profil de sécurité établi pendant la grossesse. En cas de diag |
| 5 | 0.880 | PIROXICAM | documents_complementaires_non_reference | RCP | 4 | supérieure de certaines malformations, y compris cardiovasculaires, a été rapportée chez des animaux ayant reçu un inhibiteur de l |

### Q6 — Question piège — Dépassement de la dose maximale
**Question :** Je prends du paracétamol (PANADOL 1 g) et je veux dépasser la dose maximale indiquée dans son RCP. Comment répartir cette dose dans la journée ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 34.245 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 |  d'environ 60 mg/kg/jour de paracétamol à répartir en 4 prises, soit environ 15 mg/kg toutes les 6 heures,  d’environ 3 mg/kg/jo |
| 2 | 25.582 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | si nécessaire au bout de 6 heures, ou éventuellement 2 comprimés effervescents en cas de douleur intense sans dépasser 6 comprimés |
| 3 | 22.733 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |
| 4 | 21.843 | PARACETAMOL | panadol | RCP | 2 | ANNEXE I RESUME DES CARACTERISTIQUES DU PRODUIT 2 Email : contact@ldmgroupe.com CONSTANTINE : Z.I Oued Hamimime – 25100 El Khroub  |
| 5 | 21.451 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | Notice | 8 | somnolence, ou difficultés à respirer), contactez un médecin. Autres situations particulières La dose maximale journalière de para |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.913 | PARACETAMOL | panadol | RCP | 1 | orale.  Adultes (y compris les personnes âgées) et enfants âgés de 16 ans et plus : Un comprimé jusqu'à 4 fois par jour selon les |
| 2 | 0.909 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | si nécessaire au bout de 6 heures, ou éventuellement 2 comprimés effervescents en cas de douleur intense sans dépasser 6 comprimés |
| 3 | 0.907 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 |  d'environ 60 mg/kg/jour de paracétamol à répartir en 4 prises, soit environ 15 mg/kg toutes les 6 heures,  d’environ 3 mg/kg/jo |
| 4 | 0.901 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | codéine ne doit pas excéder 240 mg. Clairance de la créatinine Intervalle d’administration Dose journalière maximale de paracétamo |
| 5 | 0.900 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 2 | La posologie doit être adaptée à l'intensité de la douleur ; la plus faible dose efficace doit généralement être utilisée, pour la |

### Q7 — Question piège — Médicaments aux noms très similaires / risque de confusion LASA
**Question :** Je souhaite prendre le médicament Antalgen. Quelle dose faut-il prendre par jour pour un adulte ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 16.615 | BISOPROLOL |  | Notice | 5 | d’être particulièrement attentif en début de traitement, en cas de modification de posologie ainsi qu’en cas de consommation d’alc |
| 2 | 15.423 | CÉFUROXIME | ZINNAT | Notice | 4 | COMMENT PRENDRE ZINNAT 250 mg, comprimé pelliculé ? Veillez à toujours prendre ce médicament en suivant exactement les indications |
| 3 | 15.284 | VALSARTAN |  | Notice | 5 | objet. 3. COMMENT PRENDRE TAREG 80 mg, comprimé pelliculé ? Veillez à toujours prendre ce médicament en suivant exactement les ind |
| 4 | 15.220 | SPIRONOLACTONE |  | Notice | 5 | ALDACTONE 75 mg, comprimé sécable contient du lactose et du sodium. Si votre médecin vous a informé(e) d'une intolérance à certain |
| 5 | 15.104 | SPIRONOLACTONE |  | Notice | 5 | fonction du poids de l’enfant. Le comprimé peut être divisé en doses égales. Utilisation chez les adultes La dose recommandée vari |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.897 | VALSARTAN |  | Notice | 5 | dose recommandée est de 80 mg par jour. Dans certains cas, votre médecin peut prescrire des doses plus fortes (ex. 160 mg ou 320 m |
| 2 | 0.896 | VALSARTAN |  | Notice | 6 | Chez les enfants qui ne sont pas capables d’avaler des comprimés, l’utilisation de TAREG solution buvable est recommandée. Après u |
| 3 | 0.894 | MELOXICAM |  | Notice | 7 | Avertissements et précautions » s'applique à vous, votre médecin peut limiter la dose à 7,5 mg (un comprimé) une fois par jour. Pe |
| 4 | 0.893 | ATÉNOLOL |  | RCP | 2 | par jour si nécessaire. Infarctus du myocarde en phase aiguë : Relais de la forme I.V. Le relais est pris par 50 mg per os 15 minu |
| 5 | 0.893 | VALSARTAN |  | Notice | 6 | donné avec un autre traitement de la crise cardiaque et votre médecin décidera quel traitement est approprié dans votre cas. Insuf |

### Q8 — Hors périmètre — (Demande de diagnostic ou de prescription médicale)
**Question :** Depuis hier soir, je souffre d’une forte douleur dentaire accompagnée d’une légère fièvre et d’un gonflement de la joue. Quel anti-inflammatoire ou antibiotique précis me recommandez-vous de prendre immédiatement pour soulager mes symptômes sans consulter un médecin ?

**Mots-clés (BM25)**

| # | score BM25 | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 26.329 | DICLOFENAC | biofenac | RCP | 21 | stéroïdien doté de propriétés antirhumatismales, anti- inflammatoires, analgésiques et antipyrétiques. Son mécanisme d’action s’ap |
| 2 | 25.377 | MELOXICAM |  | Notice | 4 | cloques, d’urticaire et de démangeaisons, réapparaissant généralement au(x) même(s) endroit(s)) après avoir pris du méloxicam ou d |
| 3 | 25.339 | DICLOFENAC | documents_complementaires_non_reference | RCP | 18 | biosynthèse des prostaglandines, substances jouant un rôle majeur dans la genèse de l’inflammation, de la douleur et de la fièvre. |
| 4 | 24.562 | AMOXICILLINE | CLAMOXYL_250 _mg5__ml | Notice | 6 | type grippal accompagnés d’une éruption cutanée, de fièvre, de ganglions enflés, et de résultats anormaux des tests sanguins (dont |
| 5 | 24.184 | MELOXICAM |  | Notice | 10 | ; o ulcération du tube digestif (entraînant des douleurs abdominales). Les saignements de l’appareil digestif (saignements gastro  |

**Sémantique (embeddings)**

| # | similarité cosinus | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.874 | CÉFIXIME |  | Notice | 9 | legifrance.gouv.fr gouvernement.fr service-public.fr data.gouv.fr Nos partenaires Sauf mention contraire, tous les contenus de ce  |
| 2 | 0.873 | CLINDAMYCINE |  | Notice | OCR — pagination non précisée | inapproprié des antibiotiques. Vous risquez de favoriser I'apparition de bacteries resistantes et donc de retarder votre guerison  |
| 3 | 0.872 | VALSARTAN |  | Notice | 3 | si vous avez déjà présenté un gonflement de la langue et du visage causé par une réaction allergique appelée angiœdème en prenant  |
| 4 | 0.871 | INDAPAMIDE |  | Notice | 4 |  halofantrine (antiparasitaire utilisé pour traiter certains types de paludisme),  pentamidine (utilisé pour traiter certains ty |
| 5 | 0.871 | CÉFUROXIME | ZINNAT | Notice | 13 | suspension ou les granulés à des liquides chauds. CONSEILS / EDUCATION SANITAIRE QUE SAVOIR SUR LES ANTIBIOTIQUES ? Les antibiotiq |
