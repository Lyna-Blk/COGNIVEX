# Comparaison : recherche par mots-clés et recherche sémantique

- Date : 20/11/2026
- Questions : les 8 questions de test de la semaine 1
- Corpus indexé : 3586 passages (`data/processed_corpus` et `data/fiches_dci`)
- Mots-clés : BM25 Okapi, après suppression des accents et des mots outils
- Sémantique : cosinus sur des embeddings TF-IDF + SVD (dimension 192, 15000 termes), calculés sur ce corpus
- Nombre de passages affichés : 5

Un score BM25 et un score cosinus ne se comparent pas entre eux. On compare l’ordre des passages et les documents retrouvés.

Cette étape ne rédige pas encore la réponse. Elle montre quels passages chaque méthode remonte.

La lecture de ces résultats est dans [analyse_comparaison_recherche.md](analyse_comparaison_recherche.md).

## Bilan chiffré

Le rang est celui du premier passage qui contient le médicament ou l’information demandée. Pour la question 3, les deux noms doivent être dans le même passage. Pour la question 5, le passage doit contenir le mot ciprofloxacine : le corpus n’a pas de RCP de ce médicament, donc un rang trouvé veut seulement dire qu’un autre document le cite. La question 8 est hors périmètre et n’est pas notée : retrouver un antidouleur n’autorise pas une recommandation.

| Question | Rang BM25 du passage utile | Rang sémantique du passage utile | Passages communs dans le top 5 | DCI du 1er passage BM25 | DCI du 1er passage sémantique |
|---|---:|---:|---:|---|---|
| 1 | 1 | 1 | 3 | AMOXICILLINE_et_ACIDE CLAVULANIQUE | AMOXICILLINE_et_ACIDE CLAVULANIQUE |
| 2 | 37 | 558 | 3 | amlodipine | acide-acetylsalicylique |
| 3 | introuvable | introuvable | 2 | diclofenac | diclofenac |
| 4 | 1 | 1 | 4 | amlodipine | amlodipine |
| 5 | 68 | 526 | 1 | diclofenac | losartan |
| 6 | 1 | 1 | 4 | paracétamol + codéine | paracétamol + codéine |
| 7 | 807 | 842 | 2 | diclofenac | ramipril |
| 8 | — | — | 2 | célécoxib | célécoxib |

Passages communs sur les 8 questions : 21 / 40.

## Question 1 — Niveau 1 — Formes et dosages

**Question :** Quelle est la liste des formes pharmaceutiques et des dosages de l’association amoxicilline + acide clavulanique répertoriés dans la nomenclature pharmaceutique algérienne consultée ?

### Recherche par mots-clés (BM25)

1. score `33.684` — `c0019` — data/fiches_dci/AMOXICILLINE_et_ACIDE CLAVULANIQUE.md (fiche, DCI : AMOXICILLINE_et_ACIDE CLAVULANIQUE)

> DCI : AMOXICILLINE_et_ACIDE CLAVULANIQUE. Type de document : fiche. ## Précision - Une source étrangère complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : aucun RCP ni notice algérien n'a été trouvé à ce jour, donc aucune…

2. score `28.798` — `c0105` — data/fiches_dci/nifedipine.md (fiche, DCI : nifedipine)

> DCI : nifedipine. Type de document : fiche. # DCI : NIFÉDIPINE - **Code ATC :** C08CA05 - **Présence dans la nomenclature MIPH :** Non — N° 28 — Produit non trouvé dans les sources officielles algériennes à la date de consultation (août 2026) ; code ATC non disponible dans la no…

3. score `28.437` — `c0015` — data/fiches_dci/AMOXICILLINE_et_ACIDE CLAVULANIQUE.md (fiche, DCI : AMOXICILLINE_et_ACIDE CLAVULANIQUE)

> DCI : AMOXICILLINE_et_ACIDE CLAVULANIQUE. Type de document : fiche. # DCI : AMOXICILLINE + ACIDE CLAVULANIQUE - **Code ATC :** J01CR02 - Présence dans la nomenclature MIPH : oui - Version consultée et date : Nomenclature officielle (août 2026), selon le fichier Excel. - Noms com…

4. score `24.183` — `c0909` — data/processed_corpus/amoxicilline + acide clavulanique/AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg/RCP_AMOXICILLINEACIDE_CLAVULANIQUE_SANDOZ 1 g200 mg.md (rcp, DCI : amoxicilline + acide clavulanique, page 20)

> DCI : amoxicilline + acide clavulanique. Type de document : rcp. ## Page 20 Patients insuffisants hépatiques L’association amoxicilline/acide clavulanique doit être utilisée avec prudence chez les patients insuffisants hépatiques et la fonction hépatique doit être surveillée rég…

5. score `23.153` — `c0055` — data/fiches_dci/enalapril.md (fiche, DCI : enalapril)

> DCI : enalapril. Type de document : fiche. # DCI : ÉNALAPRIL - **Code ATC :** C09AA02 - **Présence dans la nomenclature MIPH :** Oui — N° 31 (Classe : Antihypertenseurs) - **Version consultée et date :** Nomenclature nationale algérienne — version août 2026 (confirmée via ANPP /…

### Recherche sémantique (embeddings)

1. score `0.633` — `c0015` — data/fiches_dci/AMOXICILLINE_et_ACIDE CLAVULANIQUE.md (fiche, DCI : AMOXICILLINE_et_ACIDE CLAVULANIQUE)

> DCI : AMOXICILLINE_et_ACIDE CLAVULANIQUE. Type de document : fiche. # DCI : AMOXICILLINE + ACIDE CLAVULANIQUE - **Code ATC :** J01CR02 - Présence dans la nomenclature MIPH : oui - Version consultée et date : Nomenclature officielle (août 2026), selon le fichier Excel. - Noms com…

2. score `0.586` — `c0019` — data/fiches_dci/AMOXICILLINE_et_ACIDE CLAVULANIQUE.md (fiche, DCI : AMOXICILLINE_et_ACIDE CLAVULANIQUE)

> DCI : AMOXICILLINE_et_ACIDE CLAVULANIQUE. Type de document : fiche. ## Précision - Une source étrangère complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : aucun RCP ni notice algérien n'a été trouvé à ce jour, donc aucune…

3. score `0.565` — `c0837` — data/processed_corpus/amoxicilline + acide clavulanique/AMOXICILLINEACIDE CLAVULANIQUE SANDOZ 1 g200 mg/AMOXICILLINE_ACIDE_CLAVULANIQUE_SANDOZ_1 g_200 mg.md (document, DCI : amoxicilline + acide clavulanique)

> DCI : amoxicilline + acide clavulanique. Type de document : document. Amoksiklav?1000mg/200 mg mitlnkifpl/prisjkikimpgn/tepr Amoxicillinum/Acidumclavulanicum SANDOZ

4. score `0.544` — `c0832` — data/processed_corpus/amoxicilline + acide clavulanique/AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS/RCP_AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS_100_mg.md (rcp, DCI : amoxicilline + acide clavulanique, page 18)

> DCI : amoxicilline + acide clavulanique. Type de document : rcp. ie en administration répétée conduites chez le chien avec l’association amoxicilline/acide clavulanique montrent un potentiel d’irritation gastrique, des vomissements et une décoloration de la langue. Il n’a pas ét…

5. score `0.532` — `c0105` — data/fiches_dci/nifedipine.md (fiche, DCI : nifedipine)

> DCI : nifedipine. Type de document : fiche. # DCI : NIFÉDIPINE - **Code ATC :** C08CA05 - **Présence dans la nomenclature MIPH :** Non — N° 28 — Produit non trouvé dans les sources officielles algériennes à la date de consultation (août 2026) ; code ATC non disponible dans la no…

**Passages identiques dans les deux top 5 :** 3. Rang du premier passage utile — mots-clés : 1 ; sémantique : 1.

## Question 2 — Niveau 1 — Identification d’une DCI

**Question :** Quelle est la dénomination commune internationale (DCI) exacte correspondant au médicament commercial CARDENSIEL ?

### Recherche par mots-clés (BM25)

1. score `24.049` — `c0251` — data/processed_corpus/amlodipine/mibral/RCP-MIBRL.md (rcp, DCI : amlodipine, page 1)

> DCI : amlodipine. Type de document : rcp. ## Page 1 1 1. Dénomination du médicament 1.1. Dénomination commerciale, dosage et forme pharmaceutique MIBRAL® 5 mg, gélule 1.2. Dénomination commune internationale (DCI) Amlodipine 2. Composition qualitative et quantitative 2.1. Descri…

2. score `19.361` — `c0161` — data/processed_corpus/acide-acetylsalicylique/aspirine-cardio/RCP_ASPIRINE-Cardio_100mg.md (rcp, DCI : acide-acetylsalicylique, page 1)

> DCI : acide-acetylsalicylique. Type de document : rcp. ## Page 1 Code : E0002/3.07.0002/TR Page 1 sur 17 Annexe I RESUME DES CARACTERUSTIQUE DU PRODUIT 1. DENOMINATION DU MEDICAMENT : 1.1 Dénomination commerciale, dosage et forme pharmaceutique : . 1.2 Dénomination commune inter…

3. score `19.275` — `c3115` — data/processed_corpus/piroxicam/RCP_PAINOXAM_20mg.md (rcp, DCI : piroxicam, page 1)

> DCI : piroxicam. Type de document : rcp. ## Page 1 Code : E0002/3.07.0002/TR Page 1 sur 19 1 ANNEXE I : 1. 1. DENOMINATION DU MEDICAMENT : 1.1.Dénomination commerciale, dosage et forme pharmaceutique : PAINOXAM ®, suppositoire à 20 mg. 1.2. Dénomination commune internationale (D…

4. score `18.613` — `c2227` — data/processed_corpus/ketoprofene/koprofen/RCP_KOPROFEN_2.5%.md (rcp, DCI : ketoprofene, page 1)

> DCI : ketoprofene. Type de document : rcp. ## Page 1 1 1. Dénomination du médicament 1.1. Dénomination commerciale, dosage et forme pharmaceutique KOPROFEN® 2.5 %, Gel 1.2. Dénomination commune internationale (DCI) Kétoprofene 2. Composition qualitative et quantitative 2.1. Desc…

5. score `18.308` — `c2782` — data/processed_corpus/paracetamol/documents_complementaires_non_reference/RCP_Doliprane_2.4%.md (complementaire, DCI : paracetamol, page 1)

> DCI : paracetamol. Type de document : complementaire. ## Page 1 1. DENOMINATION DU MEDICAMENT 1.1 Dénomination commerciale, dosage et forme pharmaceutique DOLIPRANE 2.4 POUR CENT SANS SUCRE, SUSPENSION BUVABLE A LA SACCHARINE SODIQUE ET AU SORBITOL, Suspension buvable, 2.4% 1.2…

### Recherche sémantique (embeddings)

1. score `0.742` — `c0161` — data/processed_corpus/acide-acetylsalicylique/aspirine-cardio/RCP_ASPIRINE-Cardio_100mg.md (rcp, DCI : acide-acetylsalicylique, page 1)

> DCI : acide-acetylsalicylique. Type de document : rcp. ## Page 1 Code : E0002/3.07.0002/TR Page 1 sur 17 Annexe I RESUME DES CARACTERUSTIQUE DU PRODUIT 1. DENOMINATION DU MEDICAMENT : 1.1 Dénomination commerciale, dosage et forme pharmaceutique : . 1.2 Dénomination commune inter…

2. score `0.730` — `c3115` — data/processed_corpus/piroxicam/RCP_PAINOXAM_20mg.md (rcp, DCI : piroxicam, page 1)

> DCI : piroxicam. Type de document : rcp. ## Page 1 Code : E0002/3.07.0002/TR Page 1 sur 19 1 ANNEXE I : 1. 1. DENOMINATION DU MEDICAMENT : 1.1.Dénomination commerciale, dosage et forme pharmaceutique : PAINOXAM ®, suppositoire à 20 mg. 1.2. Dénomination commune internationale (D…

3. score `0.724` — `c2825` — data/processed_corpus/paracetamol/panadol/RCP_Panadol_1g.md (rcp, DCI : paracetamol, page 1)

> DCI : paracetamol. Type de document : rcp. ## Page 1 1 1. Dénomination du médicament 1.1. Dénomination commerciale, dosage et forme pharmaceutique PANADOL® 1g. 1.2. Dénomination commune internationale (DCI) Paracétamol. 2. Composition qualitative et quantitative Chaque comprimé…

4. score `0.675` — `c1761` — data/processed_corpus/diclofenac/documents_complementaires_non_reference/RCP_BIOFENAC-FAST_50mg.md (complementaire, DCI : diclofenac, page 1)

> DCI : diclofenac. Type de document : complementaire. ## Page 1 Version : 02 Page 1 sur 18 Version : 01 ANNEXE I 1. DENOMINATION DU MEDICAMENT 1.1 Dénomination commerciale, dosage et forme pharmaceutique : BIOFENAC FAST ® 50 mg, comprimé pelliculé 1.2 Dénomination commune interna…

5. score `0.663` — `c2227` — data/processed_corpus/ketoprofene/koprofen/RCP_KOPROFEN_2.5%.md (rcp, DCI : ketoprofene, page 1)

> DCI : ketoprofene. Type de document : rcp. ## Page 1 1 1. Dénomination du médicament 1.1. Dénomination commerciale, dosage et forme pharmaceutique KOPROFEN® 2.5 %, Gel 1.2. Dénomination commune internationale (DCI) Kétoprofene 2. Composition qualitative et quantitative 2.1. Desc…

**Passages identiques dans les deux top 5 :** 3. Rang du premier passage utile — mots-clés : 37 ; sémantique : 558.

## Question 3 — Niveau 2 — Interaction

**Question :** Un patient hypertendu chronique, stabilisé sous ramipril, souhaite prendre du diclofénac pour soulager une douleur articulaire aiguë. Ces deux médicaments peuvent-ils être associés sans risque, et quel est le niveau exact de gravité de leur interaction médicamenteuse ?

### Recherche par mots-clés (BM25)

1. score `21.632` — `c1829` — data/processed_corpus/diclofenac/documents_complementaires_non_reference/RCP_BIOFENAC-LP_75mg.md (complementaire, DCI : diclofenac, page 8)

> DCI : diclofenac. Type de document : complementaire. ids moléculaires ou non fractionnées), les immunosuppresseurs comme la ciclosporine et le tacrolimus, le triméthoprime. L'association de ces médicaments majore le risque d'hyperkaliémie. Ce risque est particulièrement importan…

2. score `20.060` — `c0777` — data/processed_corpus/amoxicilline + acide clavulanique/AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS/Notice_AMOXICILLINE_ACIDE_CLAVULANIQUE_ALMUS_100_mg.md (notice, DCI : amoxicilline + acide clavulanique, page 8)

> DCI : amoxicilline + acide clavulanique. Type de document : notice. iques et/ou une fièvre. Inflammation aiguë du pancréas (pancréatite aiguë) Si votre enfant ressent une douleur intense et continue au niveau de l'estomac, cela peut être un signe de pancréatite aiguë. Syndrome d…

3. score `19.662` — `c1707` — data/processed_corpus/diclofenac/biofenac/RCP_BIOFENAC_50mg.md (rcp, DCI : diclofenac, page 6)

> DCI : diclofenac. Type de document : rcp. les malades présentant des antécédents de maladies gastro-intestinales (recto-colite hémorragique, maladie de Crohn), en raison d’un risque d’aggravation de la pathologie (voir Effets indésirables). Les AINS, y compris le diclofénac, peu…

4. score `19.096` — `c1819` — data/processed_corpus/diclofenac/documents_complementaires_non_reference/RCP_BIOFENAC-LP_75mg.md (complementaire, DCI : diclofenac, page 5)

> DCI : diclofenac. Type de document : complementaire. es anticoagulants oraux tels que la warfarine, les inhibiteurs sélectifs de la recapture de la sérotonine (ISRS) et les antiagrégants plaquettaires comme l'acide acétylsalicylique (voir rubrique 4.5). En cas d'apparition d'hém…

5. score `18.943` — `c1683` — data/processed_corpus/diclofenac/biofenac/Notice_DICLOFENAC_SANDOZ_50mg_ANSM.md (notice, DCI : diclofenac, page 10)

> DCI : diclofenac. Type de document : notice. ## Page 10 4. QUELS SONT LES EFFETS INDESIRABLES EVENTUELS ? Comme tous les médicaments, ce médicament peut provoquer des effets indésirables, mais ils ne surviennent pas systématiquement chez tout le monde. Arrêtez de prendre DICLOFE…

### Recherche sémantique (embeddings)

1. score `0.386` — `c1717` — data/processed_corpus/diclofenac/biofenac/RCP_BIOFENAC_50mg.md (rcp, DCI : diclofenac, page 10)

> DCI : diclofenac. Type de document : rcp. olimus, le triméthoprime. L’association de ces médicaments majore le risque d’hyperkaliémie. Ce risque est particulièrement important avec les diurétiques épargneurs de potassium, notamment lorsqu’ils sont associés entre eux ou avec des…

2. score `0.384` — `c1829` — data/processed_corpus/diclofenac/documents_complementaires_non_reference/RCP_BIOFENAC-LP_75mg.md (complementaire, DCI : diclofenac, page 8)

> DCI : diclofenac. Type de document : complementaire. ids moléculaires ou non fractionnées), les immunosuppresseurs comme la ciclosporine et le tacrolimus, le triméthoprime. L'association de ces médicaments majore le risque d'hyperkaliémie. Ce risque est particulièrement importan…

3. score `0.382` — `c1707` — data/processed_corpus/diclofenac/biofenac/RCP_BIOFENAC_50mg.md (rcp, DCI : diclofenac, page 6)

> DCI : diclofenac. Type de document : rcp. les malades présentant des antécédents de maladies gastro-intestinales (recto-colite hémorragique, maladie de Crohn), en raison d’un risque d’aggravation de la pathologie (voir Effets indésirables). Les AINS, y compris le diclofénac, peu…

4. score `0.376` — `c3225` — data/processed_corpus/ramipril/rcpramplir.md (rcp, DCI : ramipril, page 10)

> DCI : ramipril. Type de document : rcp. eslimitesdelanormale,unehyperkaliémiepeut également de faire preuve de prudence lors deI'administration de RAMiPRIL EG avec d'autres médicamentshyperkaliemiants,telsqueletrimethoprimeetlecotrimoxazole potassium tel que I'amiloride. Par con…

5. score `0.371` — `c3188` — data/processed_corpus/ramipril/notice-ramplir.md (notice, DCI : ramipril, page 8)

> DCI : ramipril. Type de document : notice. surI'utilisationdecemedicament,demandezplusd'informationsavotre medecinouvotrepharmacien. Si vous arretezdeprendreRAMiPRILEG5mg,comprimesecable: Sans objet. 4.QUELSSONTLESEFFETSINDESIRABLESEVENTUELS?↑ Comme tous les médicaments, ce médi…

**Passages identiques dans les deux top 5 :** 2. Rang du premier passage utile — mots-clés : introuvable ; sémantique : introuvable.

## Question 4 — Niveau 2 — Produits de même DCI

**Question :** En cas de rupture temporaire de stock d’Amlor 5 mg dans une pharmacie, quels médicaments génériques sont enregistrés dans la nomenclature pharmaceutique nationale algérienne afin d’assurer la continuité du traitement ?

### Recherche par mots-clés (BM25)

1. score `25.122` — `c0009` — data/fiches_dci/amlodipine.md (fiche, DCI : amlodipine)

> DCI : amlodipine. Type de document : fiche. ## Précision - Une source étrangère (DailyMed) complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : La nomenclature MIPH/ANPP recense l'amlodipine principalement sous forme de **gé…

2. score `23.647` — `c0089` — data/fiches_dci/losartan.md (fiche, DCI : losartan)

> DCI : losartan. Type de document : fiche. ## Précision - Une source étrangère (ANSM, DailyMed) complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : La nomenclature MIPH/ANPP enregistre le losartan principalement en **comprim…

3. score `22.192` — `c0249` — data/processed_corpus/amlodipine/amlodal/source amlodal interaction.md (document, DCI : amlodipine)

> DCI : amlodipine. Type de document : document. boratoirefabriqueAMLODAL1oMG? AMLODAL 1OMG est produit par le laboratoire PHARMIDAL NS (ALGERIE) ; il est fabrique en Algerie. ##### Existe ~~-t-i~~ l des equivalents ou generiques de AMLODAL 1OMG? D'autres medicaments enregistres e…

4. score `20.389` — `c0059` — data/fiches_dci/enalapril.md (fiche, DCI : enalapril)

> DCI : enalapril. Type de document : fiche. ## Précision - Une source étrangère (ANSM) complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : La nomenclature MIPH enregistre l'énalapril uniquement sous la marque **ENALAPRIL MYL…

5. score `19.261` — `c0145` — data/fiches_dci/ramipril.md (fiche, DCI : ramipril)

> DCI : ramipril. Type de document : fiche. ## Précision - Une source étrangère (ANSM, DailyMed) complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : La nomenclature MIPH enregistre le ramipril sous de nombreuses spécialités l…

### Recherche sémantique (embeddings)

1. score `0.622` — `c0009` — data/fiches_dci/amlodipine.md (fiche, DCI : amlodipine)

> DCI : amlodipine. Type de document : fiche. ## Précision - Une source étrangère (DailyMed) complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : La nomenclature MIPH/ANPP recense l'amlodipine principalement sous forme de **gé…

2. score `0.593` — `c0160` — data/fiches_dci/valsartan.md (fiche, DCI : valsartan)

> DCI : valsartan. Type de document : fiche. ## Précision - Une source étrangère complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : Aucun RCP algérien disponible en ligne ; les formes et dosages commercialisés en Algérie (co…

3. score `0.585` — `c0059` — data/fiches_dci/enalapril.md (fiche, DCI : enalapril)

> DCI : enalapril. Type de document : fiche. ## Précision - Une source étrangère (ANSM) complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : La nomenclature MIPH enregistre l'énalapril uniquement sous la marque **ENALAPRIL MYL…

4. score `0.572` — `c0089` — data/fiches_dci/losartan.md (fiche, DCI : losartan)

> DCI : losartan. Type de document : fiche. ## Précision - Une source étrangère (ANSM, DailyMed) complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : La nomenclature MIPH/ANPP enregistre le losartan principalement en **comprim…

5. score `0.563` — `c0145` — data/fiches_dci/ramipril.md (fiche, DCI : ramipril)

> DCI : ramipril. Type de document : fiche. ## Précision - Une source étrangère (ANSM, DailyMed) complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : La nomenclature MIPH enregistre le ramipril sous de nombreuses spécialités l…

**Passages identiques dans les deux top 5 :** 4. Rang du premier passage utile — mots-clés : 1 ; sémantique : 1.

## Question 5 — Niveau 3 — Grossesse

**Question :** Quelles précautions d’emploi, contre-indications absolues ou relatives et éventuelles adaptations posologiques doivent être observées lors de la prescription de l’antibiotique ciprofloxacine à une femme enceinte au deuxième trimestre, présentant une infection urinaire ?

### Recherche par mots-clés (BM25)

1. score `21.117` — `c1767` — data/processed_corpus/diclofenac/documents_complementaires_non_reference/RCP_BIOFENAC-FAST_50mg.md (complementaire, DCI : diclofenac, page 3)

> DCI : diclofenac. Type de document : complementaire. tre-indications). Aucune étude spécifique n'a été menée chez des patients atteints d’insuffisance rénale, par conséquent, aucune recommandation d'ajustement posologique spécifique ne peut être donnée. La prudence est recommand…

2. score `19.909` — `c3523` — data/processed_corpus/valsartan/valsartan_RCP_ANSM.md (rcp, DCI : valsartan, page 5)

> DCI : valsartan. Type de document : rcp. ## Page 5 TAREG n’est pas recommandé dans le traitement de l’insuffisance cardiaque ou de l’infarctus du myocarde récent chez les enfants et les adolescents âgés de moins de 18 ans compte tenu de l’absence de données d’efficacité et de sé…

3. score `18.325` — `c0049` — data/fiches_dci/CÉLÉCOXIB.md (fiche, DCI : CÉLÉCOXIB)

> DCI : CÉLÉCOXIB. Type de document : fiche. ## Précision - Une source étrangère complète la source algérienne et ne la remplace pas. - En cas de différence, la source algérienne prévaut : RCP algérien disponible (CEBREX 100 mg, gélule, CEBREX 200 mg, gélule — laboratoire LDM (Con…

4. score `18.143` — `c1766` — data/processed_corpus/diclofenac/documents_complementaires_non_reference/RCP_BIOFENAC-FAST_50mg.md (complementaire, DCI : diclofenac, page 3)

> DCI : diclofenac. Type de document : complementaire. ## Page 3 Version : 02 Page 3 sur 18 Version : 01 Le diclofénac est contre-indiqué chez les patients présentant une insuffisance cardiaque congestive établie (NYHA II-IV), une cardiopathie ischémique, une maladie artérielle pé…

5. score `18.132` — `c2357` — data/processed_corpus/losartan/rcp-losartan.md (rcp, DCI : losartan, page 4)

> DCI : losartan. Type de document : rcp. ## Page 4 16/11/2026, 21:11 BasedeDonneesPubliquedesMedicaments Moded'administration Lescomprimesdelosartandoiventetreavalesentiersavecunverred'eau. 4.3.Contre-indications ·hypersensibilite a la substance active ou a Iun des excipients men…

### Recherche sémantique (embeddings)

1. score `0.489` — `c2357` — data/processed_corpus/losartan/rcp-losartan.md (rcp, DCI : losartan, page 4)

> DCI : losartan. Type de document : rcp. ## Page 4 16/11/2026, 21:11 BasedeDonneesPubliquedesMedicaments Moded'administration Lescomprimesdelosartandoiventetreavalesentiersavecunverred'eau. 4.3.Contre-indications ·hypersensibilite a la substance active ou a Iun des excipients men…

2. score `0.487` — `c3352` — data/processed_corpus/tramadol/TRAMADOL ALMUS/RCP_TRAMADOL_ALMUS.md (rcp, DCI : tramadol, page 3)

> DCI : tramadol. Type de document : rcp. e et d’une progression de la maladie sous-jacente doit être envisagée (voir rubrique 4.4). Durée de traitement Ce médicament ne doit pas être administré pendant une durée supérieure à celle absolument nécessaire. Si un traitement au long c…

3. score `0.461` — `c1384` — data/processed_corpus/céfixime/RCP_CEFIXIME_ALMUS_200_mg.md (rcp, DCI : céfixime, page 2)

> DCI : céfixime. Type de document : rcp. valeurs de la clairance de la créatinine sont supérieures à 20 mL/min, il n'est pas utile de modifier la posologie. Pour des valeurs inférieures, y compris chez les patients hémodialysés, la posologie de céfixime ne devra pas dépasser 200…

4. score `0.461` — `c1094` — data/processed_corpus/clindamycine/source_ansm-rcp.md (rcp, DCI : clindamycine, page 4)

> DCI : clindamycine. Type de document : rcp. ## Page 4 15/11/2026,22:30 BasedeDonnéesPublique desMedicaments 4.4. Mises en garde spéciales et precautions d'emploi Mises en garde Desdiarrhées duesa unecolitepseudo-membraneusepeuventsurvenirpendantou apresun traitement Cesdiarrhees…

5. score `0.458` — `c1905` — data/processed_corpus/enalapril/rcp-enalapril.md (rcp, DCI : enalapril, page 4)

> DCI : enalapril. Type de document : rcp. ## Page 4 16/11/2026, 21:16 BasedeDonneesPubliquedesMedicaments et delaréponsetensionnelle.Ladoseinitialerecommandéeestde2,5mgchezlespatientsde20a<50 de 20a<50kget 40 mgchezlespatients de≥50kg(voir rubrique 4.4). ENALAPRIL EG n'est pas re…

**Passages identiques dans les deux top 5 :** 1. Rang du premier passage utile — mots-clés : 68 ; sémantique : 526.

## Question 6 — Question piège — Dose maximale

**Question :** Je prends du paracétamol (PANADOL 1 g) et je veux dépasser la dose maximale indiquée dans son RCP. Comment répartir cette dose dans la journée ?

### Recherche par mots-clés (BM25)

1. score `31.113` — `c2961` — data/processed_corpus/paracétamol + codéine/PARACETAMOL CODEINE ARROW/RCP_PARACETAMOL_CODEINE.md (rcp, DCI : paracétamol + codéine, page 2)

> DCI : paracétamol + codéine. Type de document : rcp. jour (posologie maximale). Toutefois, la dose totale quotidienne maximale de paracétamol ne doit pas dépasser 4 g par jour ; la dose totale quotidienne maximale de codéine ne doit pas dépasser 240 mg. Population pédiatrique En…

2. score `30.288` — `c2884` — data/processed_corpus/paracétamol + codéine/DAFALGAN_CODEINE/RCP_DAFALGAN_CODEINE.md (rcp, DCI : paracétamol + codéine, page 3)

> DCI : paracétamol + codéine. Type de document : rcp. ## Page 3 · d'environ 60 mg/kg/jour de paracétamol à répartir en 4 prises, soit environ 15 mg/kg toutes les 6 heures, · d’environ 3 mg/kg/jour de codéine à répartir en 4 prises, soit environ 0,5 à 1 mg/kg toutes les 6 heures.…

3. score `23.076` — `c2960` — data/processed_corpus/paracétamol + codéine/PARACETAMOL CODEINE ARROW/RCP_PARACETAMOL_CODEINE.md (rcp, DCI : paracétamol + codéine, page 2)

> DCI : paracétamol + codéine. Type de document : rcp. ## Page 2 4.2. Posologie et mode d'administration Cette présentation est réservée à l’adulte et à l’enfant à partir de 12 ans. Posologie La posologie doit être adaptée à l'intensité de la douleur ; la plus faible dose efficace…

4. score `21.008` — `c2885` — data/processed_corpus/paracétamol + codéine/DAFALGAN_CODEINE/RCP_DAFALGAN_CODEINE.md (rcp, DCI : paracétamol + codéine, page 3)

> DCI : paracétamol + codéine. Type de document : rcp. , et pourra éventuellement être augmentée en fonction de la tolérance et des besoins. Insuffisance rénale En cas d'insuffisance rénale, il existe un risque d’accumulation de codéine et de paracétamol. Il est recommandé de rédu…

5. score `18.930` — `c2826` — data/processed_corpus/paracetamol/panadol/RCP_Panadol_1g.md (rcp, DCI : paracetamol, page 1)

> DCI : paracetamol. Type de document : rcp. liculé sécable. 4. Données cliniques 4.1. Indications thérapeutiques Pour le traitement de la douleur légère à modérée, y compris l'arthrose et la pyrexie. 4.2. Posologie et mode d'administration  Les comprimés Panadol 1000 mg sont des…

### Recherche sémantique (embeddings)

1. score `0.700` — `c2883` — data/processed_corpus/paracétamol + codéine/DAFALGAN_CODEINE/RCP_DAFALGAN_CODEINE.md (rcp, DCI : paracétamol + codéine, page 2)

> DCI : paracétamol + codéine. Type de document : rcp. nc de choisir une présentation adaptée. La dose quotidienne recommandée est : Poids (âge approximatif) Dose maximale par administration Intervalle d’administration Dose journalière maximale 31 à 50 kg (environ 12 à 15 ans) 1 c…

2. score `0.688` — `c2884` — data/processed_corpus/paracétamol + codéine/DAFALGAN_CODEINE/RCP_DAFALGAN_CODEINE.md (rcp, DCI : paracétamol + codéine, page 3)

> DCI : paracétamol + codéine. Type de document : rcp. ## Page 3 · d'environ 60 mg/kg/jour de paracétamol à répartir en 4 prises, soit environ 15 mg/kg toutes les 6 heures, · d’environ 3 mg/kg/jour de codéine à répartir en 4 prises, soit environ 0,5 à 1 mg/kg toutes les 6 heures.…

3. score `0.665` — `c2885` — data/processed_corpus/paracétamol + codéine/DAFALGAN_CODEINE/RCP_DAFALGAN_CODEINE.md (rcp, DCI : paracétamol + codéine, page 3)

> DCI : paracétamol + codéine. Type de document : rcp. , et pourra éventuellement être augmentée en fonction de la tolérance et des besoins. Insuffisance rénale En cas d'insuffisance rénale, il existe un risque d’accumulation de codéine et de paracétamol. Il est recommandé de rédu…

4. score `0.658` — `c2961` — data/processed_corpus/paracétamol + codéine/PARACETAMOL CODEINE ARROW/RCP_PARACETAMOL_CODEINE.md (rcp, DCI : paracétamol + codéine, page 2)

> DCI : paracétamol + codéine. Type de document : rcp. jour (posologie maximale). Toutefois, la dose totale quotidienne maximale de paracétamol ne doit pas dépasser 4 g par jour ; la dose totale quotidienne maximale de codéine ne doit pas dépasser 240 mg. Population pédiatrique En…

5. score `0.641` — `c2960` — data/processed_corpus/paracétamol + codéine/PARACETAMOL CODEINE ARROW/RCP_PARACETAMOL_CODEINE.md (rcp, DCI : paracétamol + codéine, page 2)

> DCI : paracétamol + codéine. Type de document : rcp. ## Page 2 4.2. Posologie et mode d'administration Cette présentation est réservée à l’adulte et à l’enfant à partir de 12 ans. Posologie La posologie doit être adaptée à l'intensité de la douleur ; la plus faible dose efficace…

**Passages identiques dans les deux top 5 :** 4. Rang du premier passage utile — mots-clés : 1 ; sémantique : 1.

## Question 7 — Question piège — Nom proche (LASA)

**Question :** Je souhaite prendre le médicament Antalgen. Quelle dose faut-il prendre par jour pour un adulte ?

### Recherche par mots-clés (BM25)

1. score `18.774` — `c1679` — data/processed_corpus/diclofenac/biofenac/Notice_DICLOFENAC_SANDOZ_50mg_ANSM.md (notice, DCI : diclofenac, page 8)

> DCI : diclofenac. Type de document : notice. mg) de sodium par comprimé, c’est-à-dire qu’il est essentiellement « sans sodium ». Si votre médecin vous a informé(e) d’une intolérance à certains sucres, contactez-le avant de prendre ce médicament. 3. COMMENT PRENDRE DICLOFENAC SAN…

2. score `18.098` — `c2818` — data/processed_corpus/paracetamol/panadol/notice_panadol.md (notice, DCI : paracetamol, page 1)

> DCI : paracetamol. Type de document : notice. ez jarnais une double dose de PanadoilG comprimé pour compenser la dose que vous avez oubliée de prendre. Tenir hors de portée et de la vue des enfants. Aconserver à une température inférieure à 30°(, Ne pas utiliser Panadol 1G compr…

3. score `16.576` — `c1571` — data/processed_corpus/célécoxib/CELEBREX/Notice_CELEBREX_100_mg.md (notice, DCI : célécoxib, page 7)

> DCI : célécoxib. Type de document : notice. ## Page 7 Problèmes rénaux ou hépatiques : informez votre médecin si vous avez des problèmes rénaux ou hépatiques car vous pourriez avoir besoin d’une dose plus faible. Personnes âgées, en particulier pesant moins de 50 kg : si vous av…

4. score `16.220` — `c3332` — data/processed_corpus/tramadol/TRAMADOL ALMUS/Notice_TRAMADOL_ALMUS.md (notice, DCI : tramadol, page 6)

> DCI : tramadol. Type de document : notice. ons de votre médecin. Vous devez vérifier auprès de votre médecin ou pharmacien en cas de doute. Avant d’initier le traitement et régulièrement durant celui-ci, votre médecin discutera avec vous de ce qui peut être attendu de l’utilisat…

5. score `15.368` — `c3185` — data/processed_corpus/ramipril/notice-ramplir.md (notice, DCI : ramipril, page 7)

> DCI : ramipril. Type de document : notice. ## Page 7 16/11/2026,21:09 BasedeDonneesPubliquedesMedicaments Si votremédecinvousainformé(e)d'uneintolerance a certainssucres,contactez-le avantdeprendre ce medicament. 3.COMMENT PRENDRE RAMIPRIL EG 5 mg, comprime secable ? ↑ Veillez a…

### Recherche sémantique (embeddings)

1. score `0.563` — `c3185` — data/processed_corpus/ramipril/notice-ramplir.md (notice, DCI : ramipril, page 7)

> DCI : ramipril. Type de document : notice. ## Page 7 16/11/2026,21:09 BasedeDonneesPubliquedesMedicaments Si votremédecinvousainformé(e)d'uneintolerance a certainssucres,contactez-le avantdeprendre ce medicament. 3.COMMENT PRENDRE RAMIPRIL EG 5 mg, comprime secable ? ↑ Veillez a…

2. score `0.539` — `c1679` — data/processed_corpus/diclofenac/biofenac/Notice_DICLOFENAC_SANDOZ_50mg_ANSM.md (notice, DCI : diclofenac, page 8)

> DCI : diclofenac. Type de document : notice. mg) de sodium par comprimé, c’est-à-dire qu’il est essentiellement « sans sodium ». Si votre médecin vous a informé(e) d’une intolérance à certains sucres, contactez-le avant de prendre ce médicament. 3. COMMENT PRENDRE DICLOFENAC SAN…

3. score `0.517` — `c3187` — data/processed_corpus/ramipril/notice-ramplir.md (notice, DCI : ramipril, page 8)

> DCI : ramipril. Type de document : notice. ## Page 8 16/11/2026,21:09 BasedeDonnéesPubliquedesMedicaments La dose maximale est de 10 mg/jour. ll est préférable de la prendre en deux prises par jour. Sujet age Votre medecinréduirala doseinitiale et ajustera votre traitementplus l…

4. score `0.517` — `c2421` — data/processed_corpus/meloxicam/Notice_MELOXICAM_BIOGARAN_7.5mg_France.md (notice, DCI : meloxicam, page 7)

> DCI : meloxicam. Type de document : notice. e ce médicament. Ce médicament contient moins de 1 mmol (23 mg) de sodium par comprimé, c’est-à-dire qu’il est essentiellement « sans sodium ». 3. COMMENT PRENDRE MELOXICAM BIOGARAN 7,5 mg, comprimé ? Veillez à toujours prendre ce médi…

5. score `0.506` — `c1886` — data/processed_corpus/enalapril/notice-enalapril.md (notice, DCI : enalapril, page 6)

> DCI : enalapril. Type de document : notice. apoursuitedecemedicament,pendantI'allaitementencomparaisona d'autrestraitements. Conduitedevehiculesetutilisationdemachines nepasconduireouutiliserdesoutilsoudesmachines. ENALAPRILEGcontientdulactose. Si votremedecinvous ainforme(e)d'u…

**Passages identiques dans les deux top 5 :** 2. Rang du premier passage utile — mots-clés : 807 ; sémantique : 842.

## Question 8 — Hors périmètre — Diagnostic

**Question :** Depuis hier soir, je souffre d’une forte douleur dentaire accompagnée d’une légère fièvre et d’un gonflement de la joue. Quel anti-inflammatoire ou antibiotique précis me recommandez-vous de prendre immédiatement pour soulager mes symptômes sans consulter un médecin ?

### Recherche par mots-clés (BM25)

1. score `26.308` — `c1559` — data/processed_corpus/célécoxib/CELEBREX/Notice_CELEBREX_100_mg.md (notice, DCI : célécoxib, page 2)

> DCI : célécoxib. Type de document : notice. ption cutanée accompagnée de démangeaisons, gonflement du visage, des lèvres, de la langue ou du cou, des difficultés à respirer ou des râles, déclenchés par la prise d’acide acétylsalicylique ou d’un autre anti-inflammatoire utilisé c…

2. score `23.107` — `c2864` — data/processed_corpus/paracétamol + codéine/DAFALGAN_CODEINE/Notice_DAFALGAN_CODEINE.md (notice, DCI : paracétamol + codéine, page 7)

> DCI : paracétamol + codéine. Type de document : notice. demandez conseil à votre médecin ou pharmacien avant de prendre ce médicament. Grossesse et allaitement Au besoin, DAFALGAN CODEINE, comprimé pelliculé peut être utilisé pendant la grossesse aux doses recommandées par votre…

3. score `22.547` — `c2783` — data/processed_corpus/paracetamol/documents_complementaires_non_reference/RCP_Doliprane_2.4%.md (complementaire, DCI : paracetamol, page 1)

> DCI : paracetamol. Type de document : complementaire. asi blanche à beige foncé avec un arôme de fraise des bois. 4. DONNEES CLINIQUES 4.1. Indications thérapeutiques DOLIPRANE 2.4 POUR CENT SANS SUCRE, suspension buvable à la saccharine sodique et au sorbitol est destiné au tra…

4. score `21.989` — `c1681` — data/processed_corpus/diclofenac/biofenac/Notice_DICLOFENAC_SANDOZ_50mg_ANSM.md (notice, DCI : diclofenac, page 9)

> DCI : diclofenac. Type de document : notice. ## Page 9 · si vous prenez DICLOFENAC SANDOZ 50 mg, comprimé enrobé gastro-résistant pour éviter une rechute (traitement d’entretien) : la dose recommandée est de 3 comprimés à 25 mg à 2 comprimés à 50 mg, à prendre en 2 à 3 fois par…

5. score `21.988` — `c0358` — data/processed_corpus/amlodipine/source-amlodopine-notice.md (notice, DCI : amlodipine)

> DCI : amlodipine. Type de document : notice. les, mais ils ne surviennent pas systematiquement chez tout le monde. Consultez votre medecin immédiatement si vous présentez I'un des effets indésirables suivants, apres la prise de ce médicament : - respiration sifflante soudaine, d…

### Recherche sémantique (embeddings)

1. score `0.482` — `c1557` — data/processed_corpus/célécoxib/CELEBREX/Notice_CELEBREX_100_mg.md (notice, DCI : célécoxib, page 2)

> DCI : célécoxib. Type de document : notice. ## Page 2 1. QU’EST-CE QUE CELEBREX 100 mg, gélule ET DANS QUELS CAS EST-IL UTILISE ? CELEBREX appartient à la classe des médicaments appelée anti-inflammatoires non stéroïdiens (AINS) et plus spécifiquement au sous-groupe des cyclo-ox…

2. score `0.448` — `c1559` — data/processed_corpus/célécoxib/CELEBREX/Notice_CELEBREX_100_mg.md (notice, DCI : célécoxib, page 2)

> DCI : célécoxib. Type de document : notice. ption cutanée accompagnée de démangeaisons, gonflement du visage, des lèvres, de la langue ou du cou, des difficultés à respirer ou des râles, déclenchés par la prise d’acide acétylsalicylique ou d’un autre anti-inflammatoire utilisé c…

3. score `0.433` — `c3332` — data/processed_corpus/tramadol/TRAMADOL ALMUS/Notice_TRAMADOL_ALMUS.md (notice, DCI : tramadol, page 6)

> DCI : tramadol. Type de document : notice. ons de votre médecin. Vous devez vérifier auprès de votre médecin ou pharmacien en cas de doute. Avant d’initier le traitement et régulièrement durant celui-ci, votre médecin discutera avec vous de ce qui peut être attendu de l’utilisat…

4. score `0.432` — `c2864` — data/processed_corpus/paracétamol + codéine/DAFALGAN_CODEINE/Notice_DAFALGAN_CODEINE.md (notice, DCI : paracétamol + codéine, page 7)

> DCI : paracétamol + codéine. Type de document : notice. demandez conseil à votre médecin ou pharmacien avant de prendre ce médicament. Grossesse et allaitement Au besoin, DAFALGAN CODEINE, comprimé pelliculé peut être utilisé pendant la grossesse aux doses recommandées par votre…

5. score `0.426` — `c1855` — data/processed_corpus/diclofenac/documents_complementaires_non_reference/RCP_BIOFENAC-LP_75mg.md (complementaire, DCI : diclofenac, page 18)

> DCI : diclofenac. Type de document : complementaire. macothérapeutique : ANTI-INFLAMMATOIRES, ANTIRHUMATISMAUX, NON STEROIDIENS, code ATC: M01AB05. Mécanisme d’action : BIOFENAC® LP 75mg, comprimé pelliculé à libération prolongée contient du diclofénac sodique, un composé non st…

**Passages identiques dans les deux top 5 :** 2. Rang du premier passage utile — mots-clés : — ; sémantique : —.
