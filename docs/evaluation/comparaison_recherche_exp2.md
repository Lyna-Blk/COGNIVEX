# Comparaison : mots-clés, sémantique et hybride — avec et sans normalisation des noms commerciaux

- Questions : 8 (docs/evaluation/questions_llm.md) — références : docs/evaluation/references_hit_at_3.json
- Expérience : 2 (240 mots max, chevauchement 40) — 3333 passages dont 495 de nomenclature
- BM25 : sans accents, sans mots vides. Sémantique : `intfloat/multilingual-e5-small` + ChromaDB (cosinus). Hybride : fusion RRF des rangs BM25 et sémantique.
- Suffixe **+N** = la question est étendue avec la DCI du nom commercial avant la recherche.
- Hit@3 = 1 si l'un des 3 premiers passages contient la réponse attendue (définition dans le JSON de références).

## 1. Hit@3 par question

| Question | Type | BM25 | Sémantique | Hybride | BM25+N | Sémantique+N | Hybride+N |
|---|---|---|---|---|---|---|---|
| Q1 | Direct (Formes et dosages) | ✅ 1 | ✅ 1 | ✅ 1 | ✅ 1 | ✅ 1 | ✅ 1 |
| Q2 | Direct (Identification d’une DCI) | ✅ 1 | ✅ 1 | ✅ 1 | ✅ 1 | ✅ 1 | ✅ 1 |
| Q3 | Croisement de références (Association et n | ✅ 1 | ❌ 0 | ✅ 1 | ✅ 1 | ❌ 0 | ✅ 1 |
| Q4 | Produits enregistrés contenant la même DCI | ❌ 0 | ❌ 0 | ❌ 0 | ✅ 1 | ✅ 1 | ✅ 1 |
| Q5 | Contexte (Précautions pour un profil parti | ❌ 0 | ❌ 0 | ❌ 0 | ❌ 0 | ❌ 0 | ❌ 0 |
| Q6 | Dépassement de la dose maximale | ❌ 0 | ✅ 1 | ✅ 1 | ❌ 0 | ✅ 1 | ✅ 1 |
| Q7 | Médicaments aux noms très similaires / ris | n/a | n/a | n/a | n/a | n/a | n/a |
| Q8 | (Demande de diagnostic ou de prescription  | n/a | n/a | n/a | n/a | n/a | n/a |
| **Total** | Hit@3 (questions évaluables) | **3/6** | **3/6** | **4/6** | **4/6** | **4/6** | **5/6** |

> n/a : question dont la bonne réaction est un refus (Q7 nom inexistant, Q8 hors périmètre) ; il n'y a pas de passage de référence. Le seuil de refus fera l'objet d'un travail séparé.

## 2. Normalisation des noms commerciaux

| Question | Nom commercial reconnu → DCI | Noms proches non reconnus (risque LASA) | Texte ajouté à la question |
|---|---|---|---|
| Q1 | — | — | (inchangée) |
| Q2 | CARDENSIEL → bisoprolol | — | (DCI : CARDENSIEL = DCI bisoprolol) |
| Q3 | — | — | (inchangée) |
| Q4 | AMLOR → amlodipine | — | (DCI : AMLOR = DCI amlodipine) |
| Q5 | — | — | (inchangée) |
| Q6 | — | — | (inchangée) |
| Q7 | — | ANTALGEN ≈ ANTALGAN (paracétamol, 0.88), ANTALGEN ≈ ANTALFEN (ibuprofène, 0.88) | (inchangée) |
| Q8 | — | — | (inchangée) |

## 3. Tableau de provenance (Hybride+N, top-3)

Niveau d'autorité : 1 = officielle algérienne ; 2 = RCP/notice de produit ou export de nomenclature ; 3 = institutionnelle étrangère ; 4 = site professionnel ; 5 = hors référence ; 6 = article/image.

**Q1** — Quelle est la liste des formes pharmaceutiques et des dosages de l’association amoxicilline + acide clavulaniq…

| # | pertinent | DCI | produit | type de document | fichier | page | section | type de source | niveau |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ✅ | AMOXICILLINE + ACIDE CLAVULANIQUE |  | Nomenclature | Liste 40 medicaments final.xlsx | DCI amoxicilline + acide clavulanique | Formes, dosages et noms commerciaux | Algérie — nomenclature MIPH (août 2026) | 1 |
| 2 | ✅ | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAMOXYPEN | Nomenclature | Liste 40 medicaments final.xlsx | nom commercial CLAMOXYPEN | Nom commercial → DCI | Algérie — nomenclature MIPH (août 2026) | 1 |
| 3 | ✅ | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAVODEX DUO | Nomenclature | Liste 40 medicaments final.xlsx | nom commercial CLAVODEX DUO | Nom commercial → DCI | Algérie — nomenclature MIPH (août 2026) | 1 |

**Q2** — Quelle est la dénomination commune internationale (DCI) exacte correspondant au médicament commercial CARDENSI…

| # | pertinent | DCI | produit | type de document | fichier | page | section | type de source | niveau |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ✅ | BISOPROLOL | CARDENSIEL | Nomenclature | Liste 40 medicaments final.xlsx | nom commercial CARDENSIEL | Nom commercial → DCI | Algérie — nomenclature MIPH (août 2026) | 1 |
| 2 | ❌ | BISOPROLOL | DETENSIEL | Nomenclature | Liste 40 medicaments final.xlsx | nom commercial DETENSIEL | Nom commercial → DCI | Algérie — nomenclature MIPH (août 2026) | 1 |
| 3 | ❌ | BISOPROLOL | BYZOLEX | Nomenclature | Liste 40 medicaments final.xlsx | nom commercial BYZOLEX | Nom commercial → DCI | Algérie — nomenclature MIPH (août 2026) | 1 |

**Q3** — Un patient hypertendu chronique, stabilisé sous ramipril, souhaite prendre du diclofénac pour soulager une dou…

| # | pertinent | DCI | produit | type de document | fichier | page | section | type de source | niveau |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ❌ | DICLOFENAC |  | RCP | RCP_BIOFENAC-LP_75mg.pdf | 8 | 4.5 Interactions avec d’autres médicaments et | Complémentaire (hors référence) | 5 |
| 2 | ❌ | DICLOFENAC | biofenac | RCP | RCP_BIOFENAC_50mg.pdf | 13 | 4.5 Interactions médicamenteuses et autres fo | RCP / notice de produit (pays non vérifié) | 2 |
| 3 | ✅ | DICLOFENAC |  | RCP | RCP_BIOFENAC-LP_75mg.pdf | 10 | 4.5 Interactions avec d’autres médicaments et | Complémentaire (hors référence) | 5 |

**Q4** — En cas de rupture temporaire de stock d’Amlor 5 mg dans une pharmacie, quels médicaments génériques sont enreg…

| # | pertinent | DCI | produit | type de document | fichier | page | section | type de source | niveau |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ✅ | AMLODIPINE | AMLOR | Nomenclature | Liste 40 medicaments final.xlsx | nom commercial AMLOR | Nom commercial → DCI | Algérie — nomenclature MIPH (août 2026) | 1 |
| 2 | ✅ | AMLODIPINE |  | Nomenclature | Liste 40 medicaments final.xlsx | DCI amlodipine | Formes, dosages et noms commerciaux | Algérie — nomenclature MIPH (août 2026) | 1 |
| 3 | ❌ | AMLODIPINE | amlodal | Autre document PDF | source amlodal interaction.pdf | OCR — pagination non précisée |  | Algérie — site professionnel (DwaDZ...) | 4 |

**Q5** — Quelles précautions d’emploi, contre-indications absolues ou relatives et éventuelles adaptations posologiques…

| # | pertinent | DCI | produit | type de document | fichier | page | section | type de source | niveau |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ❌ | KETOPROFENE | koprofen | RCP | RCP_KOPROFEN_2.5%.pdf | 3 | 4.4 Mises en garde spéciales et précautions d | RCP / notice de produit (pays non vérifié) | 2 |
| 2 | ❌ | DICLOFENAC |  | RCP | RCP_BIOFENAC-FAST_50mg.pdf | 3 | 4.2 Posologie et mode d'administration | Complémentaire (hors référence) | 5 |
| 3 | ❌ | PIROXICAM |  | RCP | RCP_PAINOXAM_20mg.pdf | 7 | 4.4 Mises en garde spéciales et précautions p | RCP / notice de produit (pays non vérifié) | 2 |

**Q6** — Je prends du paracétamol (PANADOL 1 g) et je veux dépasser la dose maximale indiquée dans son RCP. Comment rép…

| # | pertinent | DCI | produit | type de document | fichier | page | section | type de source | niveau |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ❌ | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | RCP_PARACETAMOL_CODEINE.pdf | 2 | 4.2 Posologie et mode d'administration | RCP / notice de produit (pays non vérifié) | 2 |
| 2 | ❌ | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | RCP_DAFALGAN_CODEINE.pdf | 3 | 4.2 Posologie et mode d'administration | RCP / notice de produit (pays non vérifié) | 2 |
| 3 | ✅ | PARACETAMOL | panadol | RCP | RCP_Panadol_1g.pdf | 1 | 4.2 Posologie et mode d'administration | RCP / notice de produit (pays non vérifié) | 2 |

**Q7** — Je souhaite prendre le médicament Antalgen. Quelle dose faut-il prendre par jour pour un adulte ?

| # | pertinent | DCI | produit | type de document | fichier | page | section | type de source | niveau |
|---|---|---|---|---|---|---|---|---|---|
| 1 | n/a | VALSARTAN |  | Notice | valsartan_Notice_ANSM.pdf | 5 | 2 QUELLES SONT LES INFORMATIONS A CONNAITRE A | France — institutionnelle (ANSM / base publique) | 3 |
| 2 | n/a | SPIRONOLACTONE |  | Notice | spironolactone_Notice_ANSM.pdf | 5 | 2 QUELLES SONT LES INFORMATIONS A CONNAITRE A | France — institutionnelle (ANSM / base publique) | 3 |
| 3 | n/a | VALSARTAN |  | Notice | valsartan_Notice_ANSM.pdf | 6 | 2 QUELLES SONT LES INFORMATIONS A CONNAITRE A | France — institutionnelle (ANSM / base publique) | 3 |

**Q8** — Depuis hier soir, je souffre d’une forte douleur dentaire accompagnée d’une légère fièvre et d’un gonflement d…

| # | pertinent | DCI | produit | type de document | fichier | page | section | type de source | niveau |
|---|---|---|---|---|---|---|---|---|---|
| 1 | n/a | COTRIMOXAZOLE |  | Notice | cotrimoxazole_Notice_ANSM.pdf | 3 | 1 QU’EST-CE QUE BACTRIM FORTE, comprimé sécab | France — institutionnelle (ANSM / base publique) | 3 |
| 2 | n/a | DOXYCYCLINE |  | Notice | doxycycline_Notice_ANSM.pdf | 2 |  | France — institutionnelle (ANSM / base publique) | 3 |
| 3 | n/a | VALSARTAN |  | Notice | valsartan_Notice_ANSM.pdf | 7 | 4 QUELS SONT LES EFFETS INDESIRABLES EVENTUEL | France — institutionnelle (ANSM / base publique) | 3 |

## 4. Détail des résultats

### Q1 — Niveau 1 — Direct (Formes et dosages)
**Question :** Quelle est la liste des formes pharmaceutiques et des dosages de l’association amoxicilline + acide clavulanique répertoriés dans la nomenclature pharmaceutique algérienne consultée ?

**BM25** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 33.063 | AMOXICILLINE + ACIDE CLAVULANIQUE |  | Nomenclature | DCI amoxicilline + acide clavulanique | Nomenclature pharmaceutique algérienne — DCI amoxicilline + acide clavulanique (code ATC J01CR02, classe Antibiotiques). Liste des |
| 2 | 30.539 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAMOXYPEN | Nomenclature | nom commercial CLAMOXYPEN | CLAMOXYPEN est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |
| 3 | 30.452 | AMOXICILLINE + ACIDE CLAVULANIQUE | BIOCLAV | Nomenclature | nom commercial BIOCLAV | BIOCLAV est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + ac |
| 4 | 30.452 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAVODEX DUO | Nomenclature | nom commercial CLAVODEX DUO | CLAVODEX DUO est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline |
| 5 | 30.196 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOCLON ES | Nomenclature | nom commercial AMOCLON ES | AMOCLON ES est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |

**Sémantique** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.924 | AMOXICILLINE + ACIDE CLAVULANIQUE |  | Nomenclature | DCI amoxicilline + acide clavulanique | Nomenclature pharmaceutique algérienne — DCI amoxicilline + acide clavulanique (code ATC J01CR02, classe Antibiotiques). Liste des |
| 2 | 0.913 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAVODEX DUO | Nomenclature | nom commercial CLAVODEX DUO | CLAVODEX DUO est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline |
| 3 | 0.912 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAMOXYPEN | Nomenclature | nom commercial CLAMOXYPEN | CLAMOXYPEN est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |
| 4 | 0.907 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOCLON ES | Nomenclature | nom commercial AMOCLON ES | AMOCLON ES est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |
| 5 | 0.905 | AMOXICILLINE + ACIDE CLAVULANIQUE | BIOCLAV | Nomenclature | nom commercial BIOCLAV | BIOCLAV est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + ac |

**Hybride** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.033 | AMOXICILLINE + ACIDE CLAVULANIQUE |  | Nomenclature | DCI amoxicilline + acide clavulanique | Nomenclature pharmaceutique algérienne — DCI amoxicilline + acide clavulanique (code ATC J01CR02, classe Antibiotiques). Liste des |
| 2 | 0.032 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAMOXYPEN | Nomenclature | nom commercial CLAMOXYPEN | CLAMOXYPEN est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |
| 3 | 0.032 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAVODEX DUO | Nomenclature | nom commercial CLAVODEX DUO | CLAVODEX DUO est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline |
| 4 | 0.031 | AMOXICILLINE + ACIDE CLAVULANIQUE | BIOCLAV | Nomenclature | nom commercial BIOCLAV | BIOCLAV est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + ac |
| 5 | 0.031 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOCLON ES | Nomenclature | nom commercial AMOCLON ES | AMOCLON ES est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |

**BM25+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 33.063 | AMOXICILLINE + ACIDE CLAVULANIQUE |  | Nomenclature | DCI amoxicilline + acide clavulanique | Nomenclature pharmaceutique algérienne — DCI amoxicilline + acide clavulanique (code ATC J01CR02, classe Antibiotiques). Liste des |
| 2 | 30.539 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAMOXYPEN | Nomenclature | nom commercial CLAMOXYPEN | CLAMOXYPEN est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |
| 3 | 30.452 | AMOXICILLINE + ACIDE CLAVULANIQUE | BIOCLAV | Nomenclature | nom commercial BIOCLAV | BIOCLAV est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + ac |
| 4 | 30.452 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAVODEX DUO | Nomenclature | nom commercial CLAVODEX DUO | CLAVODEX DUO est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline |
| 5 | 30.196 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOCLON ES | Nomenclature | nom commercial AMOCLON ES | AMOCLON ES est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |

**Sémantique+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.924 | AMOXICILLINE + ACIDE CLAVULANIQUE |  | Nomenclature | DCI amoxicilline + acide clavulanique | Nomenclature pharmaceutique algérienne — DCI amoxicilline + acide clavulanique (code ATC J01CR02, classe Antibiotiques). Liste des |
| 2 | 0.913 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAVODEX DUO | Nomenclature | nom commercial CLAVODEX DUO | CLAVODEX DUO est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline |
| 3 | 0.912 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAMOXYPEN | Nomenclature | nom commercial CLAMOXYPEN | CLAMOXYPEN est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |
| 4 | 0.907 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOCLON ES | Nomenclature | nom commercial AMOCLON ES | AMOCLON ES est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |
| 5 | 0.905 | AMOXICILLINE + ACIDE CLAVULANIQUE | BIOCLAV | Nomenclature | nom commercial BIOCLAV | BIOCLAV est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + ac |

**Hybride+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.033 | AMOXICILLINE + ACIDE CLAVULANIQUE |  | Nomenclature | DCI amoxicilline + acide clavulanique | Nomenclature pharmaceutique algérienne — DCI amoxicilline + acide clavulanique (code ATC J01CR02, classe Antibiotiques). Liste des |
| 2 | 0.032 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAMOXYPEN | Nomenclature | nom commercial CLAMOXYPEN | CLAMOXYPEN est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |
| 3 | 0.032 | AMOXICILLINE + ACIDE CLAVULANIQUE | CLAVODEX DUO | Nomenclature | nom commercial CLAVODEX DUO | CLAVODEX DUO est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline |
| 4 | 0.031 | AMOXICILLINE + ACIDE CLAVULANIQUE | BIOCLAV | Nomenclature | nom commercial BIOCLAV | BIOCLAV est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + ac |
| 5 | 0.031 | AMOXICILLINE + ACIDE CLAVULANIQUE | AMOCLON ES | Nomenclature | nom commercial AMOCLON ES | AMOCLON ES est un nom commercial de la DCI amoxicilline + acide clavulanique (dénomination commune internationale : amoxicilline + |

### Q2 — Niveau 1 — Direct (Identification d’une DCI)
**Question :** Quelle est la dénomination commune internationale (DCI) exacte correspondant au médicament commercial CARDENSIEL ?

**Question étendue :** Quelle est la dénomination commune internationale (DCI) exacte correspondant au médicament commercial CARDENSIEL ? (DCI : CARDENSIEL = DCI bisoprolol)

**BM25** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 30.379 | BISOPROLOL | CARDENSIEL | Nomenclature | nom commercial CARDENSIEL | CARDENSIEL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceuti |
| 2 | 16.710 | CLARITHROMYCINE | ARICLARE | Nomenclature | nom commercial ARICLARE | ARICLARE est un nom commercial de la DCI clarithromycine (dénomination commune internationale : clarithromycine). Nomenclature pha |
| 3 | 16.459 | LÉVOFLOXACINE | LOXAMOX | Nomenclature | nom commercial LOXAMOX | LOXAMOX est un nom commercial de la DCI lévofloxacine (dénomination commune internationale : lévofloxacine). Nomenclature pharmace |
| 4 | 15.908 | AMLODIPINE | AMLOCARDINE | Nomenclature | nom commercial AMLOCARDINE | AMLOCARDINE est un nom commercial de la DCI amlodipine (dénomination commune internationale : amlodipine). Nomenclature pharmaceut |
| 5 | 15.908 | AMLODIPINE | AMLODIPAL | Nomenclature | nom commercial AMLODIPAL | AMLODIPAL est un nom commercial de la DCI amlodipine (dénomination commune internationale : amlodipine). Nomenclature pharmaceutiq |

**Sémantique** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.912 | BISOPROLOL | CARDENSIEL | Nomenclature | nom commercial CARDENSIEL | CARDENSIEL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceuti |
| 2 | 0.895 | ACIDE-ACETYLSALICYLIQUE | KARDEGIC | Nomenclature | nom commercial KARDEGIC | KARDEGIC est un nom commercial de la DCI ACIDE ACETYLSALICYLIQUE (dénomination commune internationale : ACIDE ACETYLSALICYLIQUE).  |
| 3 | 0.889 | PARACETAMOL | DOLYC | Nomenclature | nom commercial DOLYC | DOLYC est un nom commercial de la DCI paracétamol (dénomination commune internationale : paracétamol). Nomenclature pharmaceutique |
| 4 | 0.888 | COTRIMOXAZOLE | C-ZOLE | Nomenclature | nom commercial C-ZOLE | C-ZOLE est un nom commercial de la DCI cotrimoxazole (sulfaméthoxazole + triméthoprime) (dénomination commune internationale : cot |
| 5 | 0.888 | CEFTRIAXONE | CETRIAL | Nomenclature | nom commercial CETRIAL | CETRIAL est un nom commercial de la DCI ceftriaxone (dénomination commune internationale : ceftriaxone). Nomenclature pharmaceutiq |

**Hybride** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.033 | BISOPROLOL | CARDENSIEL | Nomenclature | nom commercial CARDENSIEL | CARDENSIEL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceuti |
| 2 | 0.027 | CLARITHROMYCINE | ARICLARE | Nomenclature | nom commercial ARICLARE | ARICLARE est un nom commercial de la DCI clarithromycine (dénomination commune internationale : clarithromycine). Nomenclature pha |
| 3 | 0.016 | ACIDE-ACETYLSALICYLIQUE | KARDEGIC | Nomenclature | nom commercial KARDEGIC | KARDEGIC est un nom commercial de la DCI ACIDE ACETYLSALICYLIQUE (dénomination commune internationale : ACIDE ACETYLSALICYLIQUE).  |
| 4 | 0.016 | LÉVOFLOXACINE | LOXAMOX | Nomenclature | nom commercial LOXAMOX | LOXAMOX est un nom commercial de la DCI lévofloxacine (dénomination commune internationale : lévofloxacine). Nomenclature pharmace |
| 5 | 0.016 | PARACETAMOL | DOLYC | Nomenclature | nom commercial DOLYC | DOLYC est un nom commercial de la DCI paracétamol (dénomination commune internationale : paracétamol). Nomenclature pharmaceutique |

**BM25+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 60.800 | BISOPROLOL | CARDENSIEL | Nomenclature | nom commercial CARDENSIEL | CARDENSIEL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceuti |
| 2 | 33.000 | BISOPROLOL |  | Nomenclature | DCI bisoprolol | Nomenclature pharmaceutique algérienne — DCI bisoprolol (code ATC C07AB07, classe Antihypertenseurs). Liste des formes pharmaceuti |
| 3 | 32.077 | BISOPROLOL | BISOPROLOL HUP | Nomenclature | nom commercial BISOPROLOL HUP | BISOPROLOL HUP est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmac |
| 4 | 31.658 | BISOPROLOL | BISOPROLOL BEKER | Nomenclature | nom commercial BISOPROLOL BEKER | BISOPROLOL BEKER est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharm |
| 5 | 31.658 | BISOPROLOL | BISOPROLOL MM | Nomenclature | nom commercial BISOPROLOL MM | BISOPROLOL MM est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmace |

**Sémantique+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.946 | BISOPROLOL | CARDENSIEL | Nomenclature | nom commercial CARDENSIEL | CARDENSIEL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceuti |
| 2 | 0.915 | BISOPROLOL | DETENSIEL | Nomenclature | nom commercial DETENSIEL | DETENSIEL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceutiq |
| 3 | 0.913 | BISOPROLOL | BISOSEL | Nomenclature | nom commercial BISOSEL | BISOSEL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceutique |
| 4 | 0.911 | BISOPROLOL | BYZOLEX | Nomenclature | nom commercial BYZOLEX | BYZOLEX est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceutique |
| 5 | 0.910 | BISOPROLOL | PRODOL | Nomenclature | nom commercial PRODOL | PRODOL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceutique  |

**Hybride+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.033 | BISOPROLOL | CARDENSIEL | Nomenclature | nom commercial CARDENSIEL | CARDENSIEL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceuti |
| 2 | 0.031 | BISOPROLOL | DETENSIEL | Nomenclature | nom commercial DETENSIEL | DETENSIEL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceutiq |
| 3 | 0.031 | BISOPROLOL | BYZOLEX | Nomenclature | nom commercial BYZOLEX | BYZOLEX est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceutique |
| 4 | 0.030 | BISOPROLOL | DIPROLOL | Nomenclature | nom commercial DIPROLOL | DIPROLOL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceutiqu |
| 5 | 0.030 | BISOPROLOL | BISOSEL | Nomenclature | nom commercial BISOSEL | BISOSEL est un nom commercial de la DCI bisoprolol (dénomination commune internationale : bisoprolol). Nomenclature pharmaceutique |

### Q3 — Niveau 2 — Croisement de références (Association et niveau d’interaction)
**Question :** Un patient hypertendu chronique, stabilisé sous ramipril, souhaite prendre du diclofénac pour soulager une douleur articulaire aiguë. Ces deux médicaments peuvent-ils être associés sans risque, et quel est le niveau exact de gravité de leur interaction médicamenteuse ?

**BM25** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 27.069 | DICLOFENAC | biofenac | RCP | 6 | minimale efficace. Un traitement protecteur de la muqueuse (par exemple misoprostol ou inhibiteur de la pompe à protons) doit être |
| 2 | 24.516 | DICLOFENAC | biofenac | RCP | 12 | Version : 02 Page 12 sur 27 Version : 03 hémorragique chez des patients traités par une association concomitante de diclofénac et  |
| 3 | 21.442 | DICLOFENAC |  | RCP | 10 | Page 10 sur 22 Version : 04 Associations faisant l'objet de précautions d’emploi + Anticoagulants (autres que les anticoagulants o |
| 4 | 21.422 | LOSARTAN |  | RCP | 19 | BasedeDonneesPubliquedesMedicaments indésirables et la fréquence significativement plus faible de toux. Une augmentation de la mor |
| 5 | 21.097 | AMOXICILLINE | AMOXICILLINE EG | Notice | 6 | d’AMOXICILLINE EG LABO ; les signes incluent : éruption cutanée, fièvre, douleurs articulaires et gonflement des ganglions lymphat |

**Sémantique** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.902 | DICLOFENAC |  | RCP | 8 | mis en œuvre les précautions recommandées. Pour connaître les risques et les niveaux de contraintes spécifiques aux médicaments hy |
| 2 | 0.900 | DICLOFENAC | biofenac | RCP | 10 | médicaments hyperkaliémiants, il convient de se reporter aux interactions propres à chaque substance. Toutefois certaines substanc |
| 3 | 0.888 | DICLOFENAC | biofenac | RCP | 21 | soulage rapidement les douleurs spontanées et à la mobilisation et réduit l’œdème d’origine inflammatoire ainsi que l’œdème d’orig |
| 4 | 0.887 | DICLOFENAC |  | RCP | 4 | du risque de majoration des effets indésirables (voir rubrique 4.5 Interactions médicamenteuses et autres formes d'interaction). L |
| 5 | 0.887 | DICLOFENAC |  | RCP | 9 | Version : 02 Page 9 sur 18 Version : 01 adéquate et une surveillance de la fonction rénale après le début du traitement concomitan |

**Hybride** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.028 | DICLOFENAC |  | RCP | 8 | mis en œuvre les précautions recommandées. Pour connaître les risques et les niveaux de contraintes spécifiques aux médicaments hy |
| 2 | 0.028 | DICLOFENAC | biofenac | RCP | 13 | Majoration du risque ulcérogène et hémorragique digestif. + Digoxine En cas d'utilisation concomitante, le diclofénac peut entraîn |
| 3 | 0.028 | DICLOFENAC |  | RCP | 10 | Page 10 sur 22 Version : 04 Associations faisant l'objet de précautions d’emploi + Anticoagulants (autres que les anticoagulants o |
| 4 | 0.028 | DICLOFENAC |  | RCP | 7 | du diclofénac, en particulier à dose élevée (150 mg par jour) et dans le cadre d'un traitement prolongé. Les patients doivent être |
| 5 | 0.028 | DICLOFENAC |  | RCP | 4 | du risque de majoration des effets indésirables (voir rubrique 4.5 Interactions médicamenteuses et autres formes d'interaction). L |

**BM25+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 27.069 | DICLOFENAC | biofenac | RCP | 6 | minimale efficace. Un traitement protecteur de la muqueuse (par exemple misoprostol ou inhibiteur de la pompe à protons) doit être |
| 2 | 24.516 | DICLOFENAC | biofenac | RCP | 12 | Version : 02 Page 12 sur 27 Version : 03 hémorragique chez des patients traités par une association concomitante de diclofénac et  |
| 3 | 21.442 | DICLOFENAC |  | RCP | 10 | Page 10 sur 22 Version : 04 Associations faisant l'objet de précautions d’emploi + Anticoagulants (autres que les anticoagulants o |
| 4 | 21.422 | LOSARTAN |  | RCP | 19 | BasedeDonneesPubliquedesMedicaments indésirables et la fréquence significativement plus faible de toux. Une augmentation de la mor |
| 5 | 21.097 | AMOXICILLINE | AMOXICILLINE EG | Notice | 6 | d’AMOXICILLINE EG LABO ; les signes incluent : éruption cutanée, fièvre, douleurs articulaires et gonflement des ganglions lymphat |

**Sémantique+N** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.902 | DICLOFENAC |  | RCP | 8 | mis en œuvre les précautions recommandées. Pour connaître les risques et les niveaux de contraintes spécifiques aux médicaments hy |
| 2 | 0.900 | DICLOFENAC | biofenac | RCP | 10 | médicaments hyperkaliémiants, il convient de se reporter aux interactions propres à chaque substance. Toutefois certaines substanc |
| 3 | 0.888 | DICLOFENAC | biofenac | RCP | 21 | soulage rapidement les douleurs spontanées et à la mobilisation et réduit l’œdème d’origine inflammatoire ainsi que l’œdème d’orig |
| 4 | 0.887 | DICLOFENAC |  | RCP | 4 | du risque de majoration des effets indésirables (voir rubrique 4.5 Interactions médicamenteuses et autres formes d'interaction). L |
| 5 | 0.887 | DICLOFENAC |  | RCP | 9 | Version : 02 Page 9 sur 18 Version : 01 adéquate et une surveillance de la fonction rénale après le début du traitement concomitan |

**Hybride+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.028 | DICLOFENAC |  | RCP | 8 | mis en œuvre les précautions recommandées. Pour connaître les risques et les niveaux de contraintes spécifiques aux médicaments hy |
| 2 | 0.028 | DICLOFENAC | biofenac | RCP | 13 | Majoration du risque ulcérogène et hémorragique digestif. + Digoxine En cas d'utilisation concomitante, le diclofénac peut entraîn |
| 3 | 0.028 | DICLOFENAC |  | RCP | 10 | Page 10 sur 22 Version : 04 Associations faisant l'objet de précautions d’emploi + Anticoagulants (autres que les anticoagulants o |
| 4 | 0.028 | DICLOFENAC |  | RCP | 7 | du diclofénac, en particulier à dose élevée (150 mg par jour) et dans le cadre d'un traitement prolongé. Les patients doivent être |
| 5 | 0.028 | DICLOFENAC |  | RCP | 4 | du risque de majoration des effets indésirables (voir rubrique 4.5 Interactions médicamenteuses et autres formes d'interaction). L |

### Q4 — Niveau 2 — Produits enregistrés contenant la même DCI
**Question :** En cas de rupture temporaire de stock d’Amlor 5 mg dans une pharmacie, quels médicaments génériques sont enregistrés dans la nomenclature pharmaceutique nationale algérienne afin d’assurer la continuité du traitement ?

**Question étendue :** En cas de rupture temporaire de stock d’Amlor 5 mg dans une pharmacie, quels médicaments génériques sont enregistrés dans la nomenclature pharmaceutique nationale algérienne afin d’assurer la continuité du traitement ? (DCI : AMLOR = DCI amlodipine)

**BM25** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 30.279 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | il un generique? AMLODAL 10MG est classe dans la nomenclature nationale comme un medicament generique. Quel laboratoire fabrique A |
| 2 | 30.043 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | la nomenclature nationale des produits pharmaceutiques (MIPH). AMLODAL 10MG es t- il enregistré en Algerie? Oui, AMLODAL 10MG figu |
| 3 | 28.798 | AMLODIPINE | mibral | Autre document PDF | OCR — pagination non précisée | A prendre en compte Source : ANSM. Textes de I'ANSM reproduits tels quels ; la substance du médicament est rapprochée automatiquem |
| 4 | 25.343 | AMLODIPINE | amlibon | Autre document PDF | OCR — pagination non précisée | enregistre en Algerie enclature nationale des produits pharmaceutiques (date .d'enregistrement : 2007-12-31, échéance : 2023-07-23 |
| 5 | 24.517 | CLINDAMYCINE | acnestop | Autre document PDF | OCR — pagination non précisée | ; la substance du médicament est rapprochée automatiquement du thésaurus. Une erreur ? Ecrive <u>z-</u> <u>nous</u> 5/7 https : // |

**Sémantique** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.880 | LOSARTAN | cozzar | Autre document PDF | 4 | POTASSIQUE (DCI), selon la nomenclature nationale des produits pharmaceutiques (MIPH). COZZAR5oMGest-il enregistreenAlgerie? Oui,  |
| 2 | 0.879 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | la nomenclature nationale des produits pharmaceutiques (MIPH). AMLODAL 10MG es t- il enregistré en Algerie? Oui, AMLODAL 10MG figu |
| 3 | 0.877 | GENTAMICINE | s_genta | Autre document PDF | 7 | S-GENTA10 mg/ml:équivalents enAlgerie/DwaDZ ?S-GENTA 10MG/ML est-il enregistre en Algerie Oui, S-GENTA 1oMG/ML figure dans la nome |
| 4 | 0.877 | AMLODIPINE | AMLOR | Nomenclature | nom commercial AMLOR | AMLOR est un nom commercial de la DCI amlodipine (dénomination commune internationale : amlodipine). Nomenclature pharmaceutique a |
| 5 | 0.877 | AMLODIPINE | mibral | RCP | 12 | 12 Gomme laque, oxyde de fer noir. 6.2. Incompatibilités Sans objet. 6.3. Durée de conservation, si nécessaire après reconstitutio |

**Hybride** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.032 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | la nomenclature nationale des produits pharmaceutiques (MIPH). AMLODAL 10MG es t- il enregistré en Algerie? Oui, AMLODAL 10MG figu |
| 2 | 0.031 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | il un generique? AMLODAL 10MG est classe dans la nomenclature nationale comme un medicament generique. Quel laboratoire fabrique A |
| 3 | 0.031 | AMLODIPINE | mibral | Autre document PDF | OCR — pagination non précisée | A prendre en compte Source : ANSM. Textes de I'ANSM reproduits tels quels ; la substance du médicament est rapprochée automatiquem |
| 4 | 0.031 | GENTAMICINE | s_genta | Autre document PDF | 7 | S-GENTA10 mg/ml:équivalents enAlgerie/DwaDZ ?S-GENTA 10MG/ML est-il enregistre en Algerie Oui, S-GENTA 1oMG/ML figure dans la nome |
| 5 | 0.030 | AMLODIPINE | AMLOR | Nomenclature | nom commercial AMLOR | AMLOR est un nom commercial de la DCI amlodipine (dénomination commune internationale : amlodipine). Nomenclature pharmaceutique a |

**BM25+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 47.674 | AMLODIPINE | AMLOR | Nomenclature | nom commercial AMLOR | AMLOR est un nom commercial de la DCI amlodipine (dénomination commune internationale : amlodipine). Nomenclature pharmaceutique a |
| 2 | 44.721 | AMLODIPINE |  | Nomenclature | DCI amlodipine | Nomenclature pharmaceutique algérienne — DCI amlodipine (code ATC C08CA01, classe Antihypertenseurs). Liste des formes pharmaceuti |
| 3 | 43.112 | AMLODIPINE | mibral | Autre document PDF | OCR — pagination non précisée | A prendre en compte Source : ANSM. Textes de I'ANSM reproduits tels quels ; la substance du médicament est rapprochée automatiquem |
| 4 | 41.385 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | la nomenclature nationale des produits pharmaceutiques (MIPH). AMLODAL 10MG es t- il enregistré en Algerie? Oui, AMLODAL 10MG figu |
| 5 | 36.456 | AMLODIPINE | amlibon | Autre document PDF | OCR — pagination non précisée | (date .d'enregistrement : 2007-12-31, échéance : 2023-07-23)/ ? AMLIBON 10MG est - il un générique 6/8 https : /www. /med ic ament |

**Sémantique+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.904 | AMLODIPINE | AMLOR | Nomenclature | nom commercial AMLOR | AMLOR est un nom commercial de la DCI amlodipine (dénomination commune internationale : amlodipine). Nomenclature pharmaceutique a |
| 2 | 0.896 | AMLODIPINE | TENSODIPINE | Nomenclature | nom commercial TENSODIPINE | TENSODIPINE est un nom commercial de la DCI amlodipine (dénomination commune internationale : amlodipine). Nomenclature pharmaceut |
| 3 | 0.895 | AMLODIPINE | AMLOPINE | Nomenclature | nom commercial AMLOPINE | AMLOPINE est un nom commercial de la DCI amlodipine (dénomination commune internationale : amlodipine). Nomenclature pharmaceutiqu |
| 4 | 0.895 | AMLODIPINE |  | Nomenclature | DCI amlodipine | Nomenclature pharmaceutique algérienne — DCI amlodipine (code ATC C08CA01, classe Antihypertenseurs). Liste des formes pharmaceuti |
| 5 | 0.895 | AMLODIPINE | AMLOCARDINE | Nomenclature | nom commercial AMLOCARDINE | AMLOCARDINE est un nom commercial de la DCI amlodipine (dénomination commune internationale : amlodipine). Nomenclature pharmaceut |

**Hybride+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.033 | AMLODIPINE | AMLOR | Nomenclature | nom commercial AMLOR | AMLOR est un nom commercial de la DCI amlodipine (dénomination commune internationale : amlodipine). Nomenclature pharmaceutique a |
| 2 | 0.032 | AMLODIPINE |  | Nomenclature | DCI amlodipine | Nomenclature pharmaceutique algérienne — DCI amlodipine (code ATC C08CA01, classe Antihypertenseurs). Liste des formes pharmaceuti |
| 3 | 0.029 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | la nomenclature nationale des produits pharmaceutiques (MIPH). AMLODAL 10MG es t- il enregistré en Algerie? Oui, AMLODAL 10MG figu |
| 4 | 0.029 | AMLODIPINE | mibral | Autre document PDF | OCR — pagination non précisée | A prendre en compte Source : ANSM. Textes de I'ANSM reproduits tels quels ; la substance du médicament est rapprochée automatiquem |
| 5 | 0.028 | AMLODIPINE | amlodal | Autre document PDF | OCR — pagination non précisée | il un generique? AMLODAL 10MG est classe dans la nomenclature nationale comme un medicament generique. Quel laboratoire fabrique A |

### Q5 — Niveau 3 — Contexte (Précautions pour un profil particulier de patient)
**Question :** Quelles précautions d’emploi, contre-indications absolues ou relatives et éventuelles adaptations posologiques doivent être observées lors de la prescription de l’antibiotique ciprofloxacine à une femme enceinte au deuxième trimestre, présentant une infection urinaire ?

**BM25** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 29.883 | DICLOFENAC |  | RCP | 3 | Version : 02 Page 3 sur 18 Version : 01 Le diclofénac est contre-indiqué chez les patients présentant une insuffisance cardiaque c |
| 2 | 28.962 | VALSARTAN |  | RCP | 5 | TAREG n’est pas recommandé dans le traitement de l’insuffisance cardiaque ou de l’infarctus du myocarde récent chez les enfants et |
| 3 | 27.347 | INDAPAMIDE |  | RCP | 7 | Dans le cas d’une association rationnelle, utile pour certains patients, la survenue d’une hypokaliémie ou d’une hyperkaliémie (en |
| 4 | 26.411 | LOSARTAN |  | Autre document PDF | 4 | • Hypersensibilité à la substance active ou à l'un des excipients cités dans la rubrique 6.1 « liste des excipients ». • Deuxième  |
| 5 | 26.286 | AMLODIPINE |  | RCP | OCR — pagination non précisée | Gélule pour administration orale. ##### 4.3. Contre - indications L'amlodipine est contre - indiquée chez les patients présentant  |

**Sémantique** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.882 | PIROXICAM |  | RCP | 7 | au long cours par certains inhibiteurs de synthèse des prostaglandines. Précautions d'emploi Ce médicament existe sous forme d'aut |
| 2 | 0.881 | COTRIMOXAZOLE |  | RCP | 4 | Problèmes particuliers du déséquilibre de l'INR De nombreux cas d'augmentation de l'activité des anticoagulants oraux ont été rapp |
| 3 | 0.880 | CÉFUROXIME | ZINNAT | RCP | 6 | prolifération de Candida. Une utilisation prolongée peut également entraîner la prolifération d’autres micro-organismes non sensib |
| 4 | 0.880 | PIROXICAM |  | RCP | 2 | le piroxicam aux patients connus ou suspectés être des métaboliseurs lents du CYP2C9, sur la base du génotypage ou des antécédents |
| 5 | 0.879 | CÉFIXIME |  | RCP | 4 | · En cas d'insuffisance rénale sévère, il peut être nécessaire d'adapter la dose quotidienne en fonction de la clairance de la cré |

**Hybride** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.023 | KETOPROFENE | koprofen | RCP | 3 | 3 • Il est déconseillé d'appliquer le gel de kétoprofène sous pansement occlusif. • Les patients avec un asthme associé à une rhin |
| 2 | 0.016 | DICLOFENAC |  | RCP | 3 | Version : 02 Page 3 sur 18 Version : 01 Le diclofénac est contre-indiqué chez les patients présentant une insuffisance cardiaque c |
| 3 | 0.016 | PIROXICAM |  | RCP | 7 | au long cours par certains inhibiteurs de synthèse des prostaglandines. Précautions d'emploi Ce médicament existe sous forme d'aut |
| 4 | 0.016 | COTRIMOXAZOLE |  | RCP | 4 | Problèmes particuliers du déséquilibre de l'INR De nombreux cas d'augmentation de l'activité des anticoagulants oraux ont été rapp |
| 5 | 0.016 | VALSARTAN |  | RCP | 5 | TAREG n’est pas recommandé dans le traitement de l’insuffisance cardiaque ou de l’infarctus du myocarde récent chez les enfants et |

**BM25+N** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 29.883 | DICLOFENAC |  | RCP | 3 | Version : 02 Page 3 sur 18 Version : 01 Le diclofénac est contre-indiqué chez les patients présentant une insuffisance cardiaque c |
| 2 | 28.962 | VALSARTAN |  | RCP | 5 | TAREG n’est pas recommandé dans le traitement de l’insuffisance cardiaque ou de l’infarctus du myocarde récent chez les enfants et |
| 3 | 27.347 | INDAPAMIDE |  | RCP | 7 | Dans le cas d’une association rationnelle, utile pour certains patients, la survenue d’une hypokaliémie ou d’une hyperkaliémie (en |
| 4 | 26.411 | LOSARTAN |  | Autre document PDF | 4 | • Hypersensibilité à la substance active ou à l'un des excipients cités dans la rubrique 6.1 « liste des excipients ». • Deuxième  |
| 5 | 26.286 | AMLODIPINE |  | RCP | OCR — pagination non précisée | Gélule pour administration orale. ##### 4.3. Contre - indications L'amlodipine est contre - indiquée chez les patients présentant  |

**Sémantique+N** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.882 | PIROXICAM |  | RCP | 7 | au long cours par certains inhibiteurs de synthèse des prostaglandines. Précautions d'emploi Ce médicament existe sous forme d'aut |
| 2 | 0.881 | COTRIMOXAZOLE |  | RCP | 4 | Problèmes particuliers du déséquilibre de l'INR De nombreux cas d'augmentation de l'activité des anticoagulants oraux ont été rapp |
| 3 | 0.880 | CÉFUROXIME | ZINNAT | RCP | 6 | prolifération de Candida. Une utilisation prolongée peut également entraîner la prolifération d’autres micro-organismes non sensib |
| 4 | 0.880 | PIROXICAM |  | RCP | 2 | le piroxicam aux patients connus ou suspectés être des métaboliseurs lents du CYP2C9, sur la base du génotypage ou des antécédents |
| 5 | 0.879 | CÉFIXIME |  | RCP | 4 | · En cas d'insuffisance rénale sévère, il peut être nécessaire d'adapter la dose quotidienne en fonction de la clairance de la cré |

**Hybride+N** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.023 | KETOPROFENE | koprofen | RCP | 3 | 3 • Il est déconseillé d'appliquer le gel de kétoprofène sous pansement occlusif. • Les patients avec un asthme associé à une rhin |
| 2 | 0.016 | DICLOFENAC |  | RCP | 3 | Version : 02 Page 3 sur 18 Version : 01 Le diclofénac est contre-indiqué chez les patients présentant une insuffisance cardiaque c |
| 3 | 0.016 | PIROXICAM |  | RCP | 7 | au long cours par certains inhibiteurs de synthèse des prostaglandines. Précautions d'emploi Ce médicament existe sous forme d'aut |
| 4 | 0.016 | COTRIMOXAZOLE |  | RCP | 4 | Problèmes particuliers du déséquilibre de l'INR De nombreux cas d'augmentation de l'activité des anticoagulants oraux ont été rapp |
| 5 | 0.016 | VALSARTAN |  | RCP | 5 | TAREG n’est pas recommandé dans le traitement de l’insuffisance cardiaque ou de l’infarctus du myocarde récent chez les enfants et |

### Q6 — Question piège — Dépassement de la dose maximale
**Question :** Je prends du paracétamol (PANADOL 1 g) et je veux dépasser la dose maximale indiquée dans son RCP. Comment répartir cette dose dans la journée ?

**BM25** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 31.823 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | · d'environ 60 mg/kg/jour de paracétamol à répartir en 4 prises, soit environ 15 mg/kg toutes les 6 heures, · d’environ 3 mg/kg/jo |
| 2 | 24.669 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | 4.2. Posologie et mode d'administration Cette présentation est réservée à l’adulte et à l’enfant à partir de 12 ans. Posologie La  |
| 3 | 24.530 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |
| 4 | 24.480 | PARACETAMOL | panadol | Notice | 1 | par l'alcool et les inducteurs microsomiaux hépatiques (voir • Interactions .l. En cas d'apparition de tels phénomènes, ily a lieu |
| 5 | 23.692 | MÉTHYLDOPA |  | RCP | 2 | Chez l'adulte : débuter habituellement par 250 mg de méthyldopa 2 ou 3 fois par jour pendant les 48 premières heures. Ensuite adap |

**Sémantique** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.910 | PARACETAMOL | panadol | RCP | 1 | aux enfants de moins de 16 ans.  L'intervalle minimum entre les prises est de 4 heures et la dose quotidienne maximale est de 4 0 |
| 2 | 0.903 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | 4.2. Posologie et mode d'administration Cette présentation est réservée à l’adulte et à l’enfant à partir de 12 ans. Posologie La  |
| 3 | 0.903 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 2 | La posologie doit être adaptée à l'intensité de la douleur ; la plus faible dose efficace doit généralement être utilisée, pour la |
| 4 | 0.901 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | être utilisée chez les enfants de moins de 12 ans à cause du risque de toxicité opioïde lié à la métabolisation variable et non pr |
| 5 | 0.900 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |

**Hybride** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.032 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | 4.2. Posologie et mode d'administration Cette présentation est réservée à l’adulte et à l’enfant à partir de 12 ans. Posologie La  |
| 2 | 0.031 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |
| 3 | 0.031 | PARACETAMOL | panadol | RCP | 1 | aux enfants de moins de 16 ans.  L'intervalle minimum entre les prises est de 4 heures et la dose quotidienne maximale est de 4 0 |
| 4 | 0.031 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | · d'environ 60 mg/kg/jour de paracétamol à répartir en 4 prises, soit environ 15 mg/kg toutes les 6 heures, · d’environ 3 mg/kg/jo |
| 5 | 0.031 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | être utilisée chez les enfants de moins de 12 ans à cause du risque de toxicité opioïde lié à la métabolisation variable et non pr |

**BM25+N** — Hit@3 : ❌ 0

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 31.823 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | · d'environ 60 mg/kg/jour de paracétamol à répartir en 4 prises, soit environ 15 mg/kg toutes les 6 heures, · d’environ 3 mg/kg/jo |
| 2 | 24.669 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | 4.2. Posologie et mode d'administration Cette présentation est réservée à l’adulte et à l’enfant à partir de 12 ans. Posologie La  |
| 3 | 24.530 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |
| 4 | 24.480 | PARACETAMOL | panadol | Notice | 1 | par l'alcool et les inducteurs microsomiaux hépatiques (voir • Interactions .l. En cas d'apparition de tels phénomènes, ily a lieu |
| 5 | 23.692 | MÉTHYLDOPA |  | RCP | 2 | Chez l'adulte : débuter habituellement par 250 mg de méthyldopa 2 ou 3 fois par jour pendant les 48 premières heures. Ensuite adap |

**Sémantique+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.910 | PARACETAMOL | panadol | RCP | 1 | aux enfants de moins de 16 ans.  L'intervalle minimum entre les prises est de 4 heures et la dose quotidienne maximale est de 4 0 |
| 2 | 0.903 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | 4.2. Posologie et mode d'administration Cette présentation est réservée à l’adulte et à l’enfant à partir de 12 ans. Posologie La  |
| 3 | 0.903 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 2 | La posologie doit être adaptée à l'intensité de la douleur ; la plus faible dose efficace doit généralement être utilisée, pour la |
| 4 | 0.901 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | être utilisée chez les enfants de moins de 12 ans à cause du risque de toxicité opioïde lié à la métabolisation variable et non pr |
| 5 | 0.900 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |

**Hybride+N** — Hit@3 : ✅ 1

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.032 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | 4.2. Posologie et mode d'administration Cette présentation est réservée à l’adulte et à l’enfant à partir de 12 ans. Posologie La  |
| 2 | 0.031 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |
| 3 | 0.031 | PARACETAMOL | panadol | RCP | 1 | aux enfants de moins de 16 ans.  L'intervalle minimum entre les prises est de 4 heures et la dose quotidienne maximale est de 4 0 |
| 4 | 0.031 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | · d'environ 60 mg/kg/jour de paracétamol à répartir en 4 prises, soit environ 15 mg/kg toutes les 6 heures, · d’environ 3 mg/kg/jo |
| 5 | 0.031 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | être utilisée chez les enfants de moins de 12 ans à cause du risque de toxicité opioïde lié à la métabolisation variable et non pr |

### Q7 — Question piège — Médicaments aux noms très similaires / risque de confusion LASA
**Question :** Je souhaite prendre le médicament Antalgen. Quelle dose faut-il prendre par jour pour un adulte ?

**BM25** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 16.726 | CÉLÉCOXIB | CELEBREX | Notice | 7 | Problèmes rénaux ou hépatiques : informez votre médecin si vous avez des problèmes rénaux ou hépatiques car vous pourriez avoir be |
| 2 | 16.643 | SPIRONOLACTONE |  | Notice | 5 | ALDACTONE 75 mg, comprimé sécable contient du lactose et du sodium. Si votre médecin vous a informé(e) d'une intolérance à certain |
| 3 | 16.399 | DICLOFENAC | biofenac | Notice | 8 | médecin ou pharmacien. Vérifiez auprès de votre médecin ou pharmacien en cas de doute. Posologie Votre médecin décidera de la dose |
| 4 | 16.266 | BISOPROLOL |  | Notice | 5 | L’utilisation de DETENSIEL pendant la grossesse pourrait nuire à l’enfant à naître. Prévenez votre médecin si vous êtes enceinte o |
| 5 | 15.255 | RAMIPRIL |  | Notice | 7 | BasedeDonneesPubliquedesMedicaments Si votremédecinvousainformé(e)d'uneintolerance a certainssucres,contactez-le avantdeprendre ce |

**Sémantique** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.894 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 2 | La posologie doit être adaptée à l'intensité de la douleur ; la plus faible dose efficace doit généralement être utilisée, pour la |
| 2 | 0.889 | ATÉNOLOL |  | RCP | 2 | par jour si nécessaire. Infarctus du myocarde en phase aiguë : Relais de la forme I.V. Le relais est pris par 50 mg per os 15 minu |
| 3 | 0.889 | VALSARTAN |  | Notice | 6 | Chez les enfants qui ne sont pas capables d’avaler des comprimés, l’utilisation de TAREG solution buvable est recommandée. Après u |
| 4 | 0.887 | VALSARTAN |  | Notice | 5 | objet. 3. COMMENT PRENDRE TAREG 80 mg, comprimé pelliculé ? Veillez à toujours prendre ce médicament en suivant exactement les ind |
| 5 | 0.887 | VALSARTAN |  | RCP | 22 | à la dose sur l’éventail des doses cliniques (40 à 160 mg deux fois par jour). Le rapport d’accumulation moyen est d’environ 1,7.  |

**Hybride** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.030 | VALSARTAN |  | Notice | 5 | objet. 3. COMMENT PRENDRE TAREG 80 mg, comprimé pelliculé ? Veillez à toujours prendre ce médicament en suivant exactement les ind |
| 2 | 0.030 | SPIRONOLACTONE |  | Notice | 5 | ALDACTONE 75 mg, comprimé sécable contient du lactose et du sodium. Si votre médecin vous a informé(e) d'une intolérance à certain |
| 3 | 0.029 | VALSARTAN |  | Notice | 6 | Chez les enfants qui ne sont pas capables d’avaler des comprimés, l’utilisation de TAREG solution buvable est recommandée. Après u |
| 4 | 0.027 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | 4.2. Posologie et mode d'administration Cette présentation est réservée à l’adulte et à l’enfant à partir de 12 ans. Posologie La  |
| 5 | 0.026 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |

**BM25+N** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 16.726 | CÉLÉCOXIB | CELEBREX | Notice | 7 | Problèmes rénaux ou hépatiques : informez votre médecin si vous avez des problèmes rénaux ou hépatiques car vous pourriez avoir be |
| 2 | 16.643 | SPIRONOLACTONE |  | Notice | 5 | ALDACTONE 75 mg, comprimé sécable contient du lactose et du sodium. Si votre médecin vous a informé(e) d'une intolérance à certain |
| 3 | 16.399 | DICLOFENAC | biofenac | Notice | 8 | médecin ou pharmacien. Vérifiez auprès de votre médecin ou pharmacien en cas de doute. Posologie Votre médecin décidera de la dose |
| 4 | 16.266 | BISOPROLOL |  | Notice | 5 | L’utilisation de DETENSIEL pendant la grossesse pourrait nuire à l’enfant à naître. Prévenez votre médecin si vous êtes enceinte o |
| 5 | 15.255 | RAMIPRIL |  | Notice | 7 | BasedeDonneesPubliquedesMedicaments Si votremédecinvousainformé(e)d'uneintolerance a certainssucres,contactez-le avantdeprendre ce |

**Sémantique+N** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.894 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 2 | La posologie doit être adaptée à l'intensité de la douleur ; la plus faible dose efficace doit généralement être utilisée, pour la |
| 2 | 0.889 | ATÉNOLOL |  | RCP | 2 | par jour si nécessaire. Infarctus du myocarde en phase aiguë : Relais de la forme I.V. Le relais est pris par 50 mg per os 15 minu |
| 3 | 0.889 | VALSARTAN |  | Notice | 6 | Chez les enfants qui ne sont pas capables d’avaler des comprimés, l’utilisation de TAREG solution buvable est recommandée. Après u |
| 4 | 0.887 | VALSARTAN |  | Notice | 5 | objet. 3. COMMENT PRENDRE TAREG 80 mg, comprimé pelliculé ? Veillez à toujours prendre ce médicament en suivant exactement les ind |
| 5 | 0.887 | VALSARTAN |  | RCP | 22 | à la dose sur l’éventail des doses cliniques (40 à 160 mg deux fois par jour). Le rapport d’accumulation moyen est d’environ 1,7.  |

**Hybride+N** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.030 | VALSARTAN |  | Notice | 5 | objet. 3. COMMENT PRENDRE TAREG 80 mg, comprimé pelliculé ? Veillez à toujours prendre ce médicament en suivant exactement les ind |
| 2 | 0.030 | SPIRONOLACTONE |  | Notice | 5 | ALDACTONE 75 mg, comprimé sécable contient du lactose et du sodium. Si votre médecin vous a informé(e) d'une intolérance à certain |
| 3 | 0.029 | VALSARTAN |  | Notice | 6 | Chez les enfants qui ne sont pas capables d’avaler des comprimés, l’utilisation de TAREG solution buvable est recommandée. Après u |
| 4 | 0.027 | PARACÉTAMOL + CODÉINE | PARACETAMOL CODEINE ARROW | RCP | 2 | 4.2. Posologie et mode d'administration Cette présentation est réservée à l’adulte et à l’enfant à partir de 12 ans. Posologie La  |
| 5 | 0.026 | PARACÉTAMOL + CODÉINE | DAFALGAN_CODEINE | RCP | 3 | l’intervalle minimum entre 2 prises selon le tableau ci-dessous. Adultes : Chez l’enfant, une surveillance rapprochée doit être mi |

### Q8 — Hors périmètre — (Demande de diagnostic ou de prescription médicale)
**Question :** Depuis hier soir, je souffre d’une forte douleur dentaire accompagnée d’une légère fièvre et d’un gonflement de la joue. Quel anti-inflammatoire ou antibiotique précis me recommandez-vous de prendre immédiatement pour soulager mes symptômes sans consulter un médecin ?

**BM25** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 30.046 | DOXYCYCLINE |  | Notice | 2 | Adressez-vous à votre médecin ou pharmacien avant de prendre DOXYCYCLINE SANDOZ 100 mg, comprimé sécable. Évitez de vous exposer d |
| 2 | 29.575 | COTRIMOXAZOLE |  | Notice | 3 | avez pris plus de BACTRIM FORTE, comprimé sécable que vous n’auriez dû Consultez immédiatement votre médecin ou votre pharmacien.  |
| 3 | 28.949 | DICLOFENAC | biofenac | Notice | 9 | · si vous prenez DICLOFENAC SANDOZ 50 mg, comprimé enrobé gastro-résistant pour éviter une rechute (traitement d’entretien) : la d |
| 4 | 28.427 | METRONIDAZOLE |  | Notice | 2 | vertiges lors du passage en position debout (voir rubrique 4). Si ces symptômes surviennent, arrêtez d’utiliser ce médicament car  |
| 5 | 27.907 | AMOXICILLINE | CLAMOXYL_250 _mg5__ml | Notice | 6 | par les symptômes suivants : plaques rougeâtres ou violacées sur la peau avec des démangeaisons, en particulier sur la paume des m |

**Sémantique** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.879 | CÉFIXIME |  | Notice | 9 | 2- Respectez strictement votre ordonnance. 3- Ne réutilisez pas un antibiotique sans prescription médicale même si vous pensez com |
| 2 | 0.879 | CEFTRIAXONE |  | Notice | 2 | contenant du calcium doit être injecté dans la veine. Avertissements et précautions Adressez-vous à votre médecin, à votre pharmac |
| 3 | 0.878 | BISOPROLOL |  | Notice | 7 | · sensation de refroidissement ou d’engourdissement des extrémités (par exemple les mains ou les pieds). Peu fréquent (affectant p |
| 4 | 0.871 | CÉFIXIME |  | Notice | 2 | quotidienne du traitement ; · si vous avez déjà eu une anémie hémolytique après la prise d’un antibiotique de la famille des cépha |
| 5 | 0.871 | CÉFUROXIME | ZINNAT | Notice | 10 | 2- Respectez strictement votre ordonnance. 3- Ne réutilisez pas un antibiotique sans prescription médicale même si vous pensez com |

**Hybride** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.029 | COTRIMOXAZOLE |  | Notice | 3 | avez pris plus de BACTRIM FORTE, comprimé sécable que vous n’auriez dû Consultez immédiatement votre médecin ou votre pharmacien.  |
| 2 | 0.028 | DOXYCYCLINE |  | Notice | 2 | Adressez-vous à votre médecin ou pharmacien avant de prendre DOXYCYCLINE SANDOZ 100 mg, comprimé sécable. Évitez de vous exposer d |
| 3 | 0.028 | VALSARTAN |  | Notice | 7 | · gonflement du visage, des lèvres, de la langue ou de la gorge, · difficultés à respirer ou à avaler, · urticaire, démangeaisons. |
| 4 | 0.016 | CÉFIXIME |  | Notice | 9 | 2- Respectez strictement votre ordonnance. 3- Ne réutilisez pas un antibiotique sans prescription médicale même si vous pensez com |
| 5 | 0.016 | CEFTRIAXONE |  | Notice | 2 | contenant du calcium doit être injecté dans la veine. Avertissements et précautions Adressez-vous à votre médecin, à votre pharmac |

**BM25+N** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 30.046 | DOXYCYCLINE |  | Notice | 2 | Adressez-vous à votre médecin ou pharmacien avant de prendre DOXYCYCLINE SANDOZ 100 mg, comprimé sécable. Évitez de vous exposer d |
| 2 | 29.575 | COTRIMOXAZOLE |  | Notice | 3 | avez pris plus de BACTRIM FORTE, comprimé sécable que vous n’auriez dû Consultez immédiatement votre médecin ou votre pharmacien.  |
| 3 | 28.949 | DICLOFENAC | biofenac | Notice | 9 | · si vous prenez DICLOFENAC SANDOZ 50 mg, comprimé enrobé gastro-résistant pour éviter une rechute (traitement d’entretien) : la d |
| 4 | 28.427 | METRONIDAZOLE |  | Notice | 2 | vertiges lors du passage en position debout (voir rubrique 4). Si ces symptômes surviennent, arrêtez d’utiliser ce médicament car  |
| 5 | 27.907 | AMOXICILLINE | CLAMOXYL_250 _mg5__ml | Notice | 6 | par les symptômes suivants : plaques rougeâtres ou violacées sur la peau avec des démangeaisons, en particulier sur la paume des m |

**Sémantique+N** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.879 | CÉFIXIME |  | Notice | 9 | 2- Respectez strictement votre ordonnance. 3- Ne réutilisez pas un antibiotique sans prescription médicale même si vous pensez com |
| 2 | 0.879 | CEFTRIAXONE |  | Notice | 2 | contenant du calcium doit être injecté dans la veine. Avertissements et précautions Adressez-vous à votre médecin, à votre pharmac |
| 3 | 0.878 | BISOPROLOL |  | Notice | 7 | · sensation de refroidissement ou d’engourdissement des extrémités (par exemple les mains ou les pieds). Peu fréquent (affectant p |
| 4 | 0.871 | CÉFIXIME |  | Notice | 2 | quotidienne du traitement ; · si vous avez déjà eu une anémie hémolytique après la prise d’un antibiotique de la famille des cépha |
| 5 | 0.871 | CÉFUROXIME | ZINNAT | Notice | 10 | 2- Respectez strictement votre ordonnance. 3- Ne réutilisez pas un antibiotique sans prescription médicale même si vous pensez com |

**Hybride+N** — Hit@3 : n/a

| # | score | DCI | produit | doc | page | extrait |
|---|---|---|---|---|---|---|
| 1 | 0.029 | COTRIMOXAZOLE |  | Notice | 3 | avez pris plus de BACTRIM FORTE, comprimé sécable que vous n’auriez dû Consultez immédiatement votre médecin ou votre pharmacien.  |
| 2 | 0.028 | DOXYCYCLINE |  | Notice | 2 | Adressez-vous à votre médecin ou pharmacien avant de prendre DOXYCYCLINE SANDOZ 100 mg, comprimé sécable. Évitez de vous exposer d |
| 3 | 0.028 | VALSARTAN |  | Notice | 7 | · gonflement du visage, des lèvres, de la langue ou de la gorge, · difficultés à respirer ou à avaler, · urticaire, démangeaisons. |
| 4 | 0.016 | CÉFIXIME |  | Notice | 9 | 2- Respectez strictement votre ordonnance. 3- Ne réutilisez pas un antibiotique sans prescription médicale même si vous pensez com |
| 5 | 0.016 | CEFTRIAXONE |  | Notice | 2 | contenant du calcium doit être injecté dans la veine. Avertissements et précautions Adressez-vous à votre médecin, à votre pharmac |
