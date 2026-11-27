# Semaine 3 — Comparaison BM25 : avant/après normalisation

**Date :** 2026-11-27 17:55  

**Chunks originaux (Semaine 2) :** 1460 chunks  
**Chunks enrichis (Semaine 3) :** 1460 chunks (+ `dci_normalized`, `atc`, `classe`)


---

## Partie 1 — Test de normalisation des noms

| Requête | DCI attendue | DCI obtenue | Méthode | Score | ✓/✗ |
|---|---|---|---|---|---|
| amoxicilline + acide clavulanique | amoxicilline + acide clavulanique | amoxicilline + acide clavulanique | DCI | 1.000 | ✓ |
| CARDENSIEL | bisoprolol | bisoprolol | NOM_COMMERCIAL | 1.000 | ✓ |
| ramipril | ramipril | ramipril | DCI | 1.000 | ✓ |
| diclofénac | diclofénac | diclofénac | DCI | 1.000 | ✓ |
| Amlor | amlodipine | amlodipine | ALIAS_MANUEL | 1.000 | ✓ |
| ciprofloxacine | ciprofloxacine | ciprofloxacine | DCI | 1.000 | ✓ |
| paracétamol | paracétamol | paracétamol | DCI | 1.000 | ✓ |
| PANADOL | paracétamol | paracétamol | NOM_COMMERCIAL_SANS_DOSAGE | 1.000 | ✓ |
| Antalgen | paracétamol | paracétamol ⚠ | FUZZY | 0.955 | ✓ |

**Score : 9/9 (100%)**


---

## Partie 2 — Comparaison BM25 sur les 8 questions

> **OLD** = Semaine 2, sans normalisation  
> **NEW** = Semaine 3, avec normalisation + requête étendue


### Q1 — ## 1. Niveau 1 — Direct (Formes et dosages)

> Quelle est la liste des formes pharmaceutiques et des dosages de l’association amoxicilline + acide clavulanique répertoriés dans la nomenclature pharmaceutique algérienne consultée ?

**Normalisation :** `amoxicilline` | ATC: `J01CA04` | méthode: `DCI` | score: `1.000`  
**Requête étendue :** `Quelle est la liste des formes pharmaceutiques et des dosages de l’association amoxicilline + acide `

| | Rang | DCI trouvée | Score | Type doc | Page |
|---|---|---|---|---|---|
| **OLD** | 1 | AMOXICILLINE + ACIDE CLAVULANIQUE | 45.735 | RCP | 20 |
| **OLD** | 2 | AMOXICILLINE + ACIDE CLAVULANIQUE | 44.889 | RCP | 18 |
| **OLD** | 3 | AMOXICILLINE + ACIDE CLAVULANIQUE | 41.903 | RCP | 19 |
| **BM25** | 1 | AMOXICILLINE + ACIDE CLAVULANIQUE | 46.0059 |  | 20 |
| **BM25** | 2 | AMOXICILLINE + ACIDE CLAVULANIQUE | 45.1555 |  | 18 |
| **BM25** | 3 | AMOXICILLINE + ACIDE CLAVULANIQUE | 42.3227 |  | 19 |
| **SEMANTIC** | 1 | AMOXICILLINE | 0.8681 | RCP | 13 |
| **SEMANTIC** | 2 | AMOXICILLINE | 0.8641 | RCP | 9 |
| **SEMANTIC** | 3 | AMOXICILLINE | 0.8634 | RCP | 16 |
| **HYBRID** | 1 | AMOXICILLINE + ACIDE CLAVULANIQUE | 0.016393 |  | 20 |
| **HYBRID** | 2 | AMOXICILLINE | 0.016393 | RCP | 13 |
| **HYBRID** | 3 | AMOXICILLINE + ACIDE CLAVULANIQUE | 0.016129 |  | 18 |

**Observation :** OLD=AMOXICILLINE + ACIDE CLAVULANIQUE → BM25=AMOXICILLINE + ACIDE CLAVULANIQUE → SEMANTIC=AMOXICILLINE → HYBRID=AMOXICILLINE + ACIDE CLAVULANIQUE. Hybrid combines BM25 + Semantic for best coverage.


### Q2 — 2. Niveau 1 — Direct (Identification d’une DCI)

> Quelle est la dénomination commune internationale (DCI) exacte correspondant au médicament commercial CARDENSIEL ?

**Normalisation :** `bisoprolol` | ATC: `C07AB07` | méthode: `NOM_COMMERCIAL` | score: `1.000`  
**Requête étendue :** `Quelle est la dénomination commune internationale (DCI) exacte correspondant au médicament commercia`

| | Rang | DCI trouvée | Score | Type doc | Page |
|---|---|---|---|---|---|
| **OLD** | 1 | AMLODIPINE | 29.841 | RCP | 1 |
| **OLD** | 2 | ACIDE-ACETYLSALICYLIQUE | 29.13 | RCP | 1 |
| **OLD** | 3 | PIROXICAM | 27.996 | RCP | 1 |
| **BM25** | 1 | BISOPROLOL | 19.5011 |  | 1 |
| **BM25** | 2 | BISOPROLOL | 18.2895 |  | 1 |
| **BM25** | 3 | BISOPROLOL | 16.7052 |  | 6 |
| **SEMANTIC** | 1 | BISOPROLOL | 0.8695 | Notice | 2 |
| **SEMANTIC** | 2 | BISOPROLOL | 0.8648 | RCP | 2 |
| **SEMANTIC** | 3 | BISOPROLOL | 0.8618 | RCP | 3 |
| **HYBRID** | 1 | BISOPROLOL | 0.016393 |  | 1 |
| **HYBRID** | 2 | BISOPROLOL | 0.016393 | Notice | 2 |
| **HYBRID** | 3 | BISOPROLOL | 0.016129 |  | 1 |

**Observation :** OLD=AMLODIPINE → BM25=BISOPROLOL → SEMANTIC=BISOPROLOL → HYBRID=BISOPROLOL. Hybrid combines BM25 + Semantic for best coverage.


### Q3 — 3. Niveau 2 — Croisement de références (Association et niveau d’interaction)

> Un patient hypertendu chronique, stabilisé sous ramipril, souhaite prendre du diclofénac pour soulager une douleur articulaire aiguë. Ces deux médicaments peuvent-ils être associés sans risque, et quel est le niveau exact de gravité de leur interaction médicamenteuse ?

**Normalisation :** `ramipril` | ATC: `C09AA05` | méthode: `DCI` | score: `1.000`  
**Requête étendue :** `Un patient hypertendu chronique, stabilisé sous ramipril, souhaite prendre du diclofénac pour soulag`

| | Rang | DCI trouvée | Score | Type doc | Page |
|---|---|---|---|---|---|
| **OLD** | 1 | AMOXICILLINE + ACIDE CLAVULANIQUE | 49.028 | RCP | 6 |
| **OLD** | 2 | DICLOFENAC | 48.041 | RCP | 8 |
| **OLD** | 3 | AMOXICILLINE + ACIDE CLAVULANIQUE | 47.721 | RCP | 5 |
| **BM25** | 1 | RAMIPRIL | 42.8981 |  | OCR — pagination non précisée |
| **BM25** | 2 | RAMIPRIL | 41.8284 |  | OCR — pagination non précisée |
| **BM25** | 3 | RAMIPRIL | 40.7793 |  | OCR — pagination non précisée |
| **SEMANTIC** | 1 | RAMIPRIL | 0.8849 | RCP | OCR — pagination non précisée |
| **SEMANTIC** | 2 | RAMIPRIL | 0.8699 | RCP | OCR — pagination non précisée |
| **SEMANTIC** | 3 | RAMIPRIL | 0.8694 | RCP | OCR — pagination non précisée |
| **HYBRID** | 1 | RAMIPRIL | 0.016393 |  | OCR — pagination non précisée |
| **HYBRID** | 2 | RAMIPRIL | 0.016393 | RCP | OCR — pagination non précisée |
| **HYBRID** | 3 | RAMIPRIL | 0.016129 |  | OCR — pagination non précisée |

**Observation :** OLD=AMOXICILLINE + ACIDE CLAVULANIQUE → BM25=RAMIPRIL → SEMANTIC=RAMIPRIL → HYBRID=RAMIPRIL. Hybrid combines BM25 + Semantic for best coverage.


### Q4 — 4. Niveau 2 — Produits enregistrés contenant la même DCI

> En cas de rupture temporaire de stock d’Amlor 5 mg dans une pharmacie, quels médicaments génériques sont enregistrés dans la nomenclature pharmaceutique nationale algérienne afin d’assurer la continuité du traitement ?

**Normalisation :** `amlodipine` | ATC: `C08CA01` | méthode: `FUZZY` | score: `0.909`  
**Requête étendue :** `En cas de rupture temporaire de stock d’Amlor 5 mg dans une pharmacie, quels médicaments génériques `

| | Rang | DCI trouvée | Score | Type doc | Page |
|---|---|---|---|---|---|
| **OLD** | 1 | AMLODIPINE | 56.633 | Autre document PDF | OCR — pagination non précisée |
| **OLD** | 2 | AMLODIPINE | 48.281 | Autre document PDF | OCR — pagination non précisée |
| **OLD** | 3 | PERINDOPRIL | 47.865 | Autre document PDF | OCR — pagination non précisée |
| **BM25** | 1 | AMLODIPINE | 62.7215 |  | OCR — pagination non précisée |
| **BM25** | 2 | AMLODIPINE | 54.3494 |  | OCR — pagination non précisée |
| **BM25** | 3 | AMLODIPINE | 52.3194 |  | OCR — pagination non précisée |
| **SEMANTIC** | 1 | AMLODIPINE | 0.8801 | Autre document PDF | OCR — pagination non précisée |
| **SEMANTIC** | 2 | AMLODIPINE | 0.8778 | RCP | 12 |
| **SEMANTIC** | 3 | AMLODIPINE | 0.8775 | RCP | 1 |
| **HYBRID** | 1 | AMLODIPINE | 0.032787 |  | OCR — pagination non précisée |
| **HYBRID** | 2 | AMLODIPINE | 0.016129 |  | OCR — pagination non précisée |
| **HYBRID** | 3 | AMLODIPINE | 0.016129 | RCP | 12 |

**Observation :** All methods agree: **AMLODIPINE**. Result is confirmed.


### Q5 — 5. Niveau 3 — Contexte (Précautions pour un profil particulier de patient)

> Quelles précautions d’emploi, contre-indications absolues ou relatives et éventuelles adaptations posologiques doivent être observées lors de la prescription de l’antibiotique ciprofloxacine à une femme enceinte au deuxième trimestre, présentant une infection urinaire ?

**Normalisation :** `ciprofloxacine` | ATC: `J01MA02` | méthode: `DCI` | score: `1.000`  
**Requête étendue :** `Quelles précautions d’emploi, contre-indications absolues ou relatives et éventuelles adaptations po`

| | Rang | DCI trouvée | Score | Type doc | Page |
|---|---|---|---|---|---|
| **OLD** | 1 | PIROXICAM | 46.814 | RCP | 12 |
| **OLD** | 2 | COTRIMOXAZOLE | 45.839 | Notice | 2 |
| **OLD** | 3 | INDAPAMIDE | 45.393 | RCP | 7 |
| **BM25** | 1 | CIPROFLOXACINE | 39.0972 |  | 1 |
| **BM25** | 2 | CIPROFLOXACINE | 30.8777 |  | 1 |
| **BM25** | 3 | CIPROFLOXACINE | 29.5875 |  | 2 |
| **SEMANTIC** | 1 | CIPROFLOXACINE | 0.877 | Notice | 1 |
| **SEMANTIC** | 2 | CIPROFLOXACINE | 0.8763 | Notice | 1 |
| **SEMANTIC** | 3 | CIPROFLOXACINE | 0.8737 | Notice | 1 |
| **HYBRID** | 1 | CIPROFLOXACINE | 0.032522 |  | 1 |
| **HYBRID** | 2 | CIPROFLOXACINE | 0.016393 |  | 1 |
| **HYBRID** | 3 | CIPROFLOXACINE | 0.016129 | Notice | 1 |

**Observation :** OLD=PIROXICAM → BM25=CIPROFLOXACINE → SEMANTIC=CIPROFLOXACINE → HYBRID=CIPROFLOXACINE. Hybrid combines BM25 + Semantic for best coverage.


### Q6 — 6. Question piège — Dépassement de la dose maximale

> Je prends du paracétamol (PANADOL 1 g) et je veux dépasser la dose maximale indiquée dans son RCP. Comment répartir cette dose dans la journée ? Le système doit-il refuser de répartir la dose afficher un message d’alerte ?

**Normalisation :** `paracétamol` | ATC: `N02BE01` | méthode: `DCI` | score: `1.000`  
**Requête étendue :** `Je prends du paracétamol (PANADOL 1 g) et je veux dépasser la dose maximale indiquée dans son RCP. C`

| | Rang | DCI trouvée | Score | Type doc | Page |
|---|---|---|---|---|---|
| **OLD** | 1 | PARACÉTAMOL + CODÉINE | 68.85 | RCP | 3 |
| **OLD** | 2 | PARACÉTAMOL + CODÉINE | 63.22 | RCP | 2 |
| **OLD** | 3 | PARACÉTAMOL + CODÉINE | 49.606 | RCP | 4 |
| **BM25** | 1 | PARACÉTAMOL + CODÉINE | 72.7843 |  | 3 |
| **BM25** | 2 | PARACÉTAMOL + CODÉINE | 67.1049 |  | 2 |
| **BM25** | 3 | PARACETAMOL | 54.9814 |  | 2 |
| **SEMANTIC** | 1 | PARACETAMOL | 0.8866 | RCP | 7 |
| **SEMANTIC** | 2 | PARACETAMOL | 0.8843 | Notice | 1 |
| **SEMANTIC** | 3 | PARACETAMOL | 0.8837 | RCP | 9 |
| **HYBRID** | 1 | PARACÉTAMOL + CODÉINE | 0.016393 |  | 3 |
| **HYBRID** | 2 | PARACETAMOL | 0.016393 | RCP | 7 |
| **HYBRID** | 3 | PARACÉTAMOL + CODÉINE | 0.016129 |  | 2 |

**Observation :** OLD=PARACÉTAMOL + CODÉINE → BM25=PARACÉTAMOL + CODÉINE → SEMANTIC=PARACETAMOL → HYBRID=PARACÉTAMOL + CODÉINE. Hybrid combines BM25 + Semantic for best coverage.


### Q7 — 7. Question piège — Médicaments aux noms très similaires / risque de confusion LASA

> Je souhaite prendre le médicament Antalgen. Quelle dose faut-il prendre par jour pour un adulte ?

**Normalisation :** `paracétamol` | ATC: `N02BE01` | méthode: `FUZZY` | score: `0.955`  
**Requête étendue :** `Je souhaite prendre le médicament Antalgen. Quelle dose faut-il prendre par jour pour un adulte ? do`

| | Rang | DCI trouvée | Score | Type doc | Page |
|---|---|---|---|---|---|
| **OLD** | 1 | TRAMADOL | 26.089 | Notice | 9 |
| **OLD** | 2 | PARACETAMOL | 24.916 | Notice | 1 |
| **OLD** | 3 | TRAMADOL | 23.649 | Notice | 5 |
| **BM25** | 1 | PARACETAMOL | 30.1346 |  | 1 |
| **BM25** | 2 | PARACÉTAMOL + CODÉINE | 28.1233 |  | 8 |
| **BM25** | 3 | PARACÉTAMOL + CODÉINE | 27.7048 |  | 6 |
| **SEMANTIC** | 1 | PARACETAMOL | 0.8881 | RCP | 2 |
| **SEMANTIC** | 2 | PARACETAMOL | 0.8871 | RCP | 6 |
| **SEMANTIC** | 3 | PARACETAMOL | 0.8812 | RCP | 3 |
| **HYBRID** | 1 | PARACETAMOL | 0.016393 |  | 1 |
| **HYBRID** | 2 | PARACETAMOL | 0.016393 | RCP | 2 |
| **HYBRID** | 3 | PARACÉTAMOL + CODÉINE | 0.016129 |  | 8 |

**Observation :** OLD=TRAMADOL → BM25=PARACETAMOL → SEMANTIC=PARACETAMOL → HYBRID=PARACETAMOL. Hybrid combines BM25 + Semantic for best coverage.


### Q8 — 8. Hors périmètre — (Demande de diagnostic ou de prescription médicale)

> Depuis hier soir, je souffre d’une forte douleur dentaire accompagnée d’une légère fièvre et d’un gonflement de la joue. Quel anti-inflammatoire ou antibiotique précis me recommandez-vous de prendre immédiatement pour soulager mes symptômes sans consulter un médecin ?

**Normalisation :** `clindamycine` | ATC: `J01FF01` | méthode: `FUZZY` | score: `0.750`  
**Requête étendue :** `Depuis hier soir, je souffre d’une forte douleur dentaire accompagnée d’une légère fièvre et d’un go`

| | Rang | DCI trouvée | Score | Type doc | Page |
|---|---|---|---|---|---|
| **OLD** | 1 | CÉLÉCOXIB | 56.819 | Notice | 2 |
| **OLD** | 2 | METRONIDAZOLE | 50.392 | Notice | 2 |
| **OLD** | 3 | DOXYCYCLINE | 48.767 | Notice | 2 |
| **BM25** | 1 | CLINDAMYCINE | 42.5266 |  | OCR — pagination non précisée |
| **BM25** | 2 | CLINDAMYCINE | 38.9699 |  | OCR — pagination non précisée |
| **BM25** | 3 | CLINDAMYCINE | 38.6931 |  | OCR — pagination non précisée |
| **SEMANTIC** | 1 | CLINDAMYCINE | 0.8719 | Notice | OCR — pagination non précisée |
| **SEMANTIC** | 2 | CLINDAMYCINE | 0.861 | Notice | OCR — pagination non précisée |
| **SEMANTIC** | 3 | CLINDAMYCINE | 0.8544 | Autre document PDF | OCR — pagination non précisée |
| **HYBRID** | 1 | CLINDAMYCINE | 0.032522 |  | OCR — pagination non précisée |
| **HYBRID** | 2 | CLINDAMYCINE | 0.032002 |  | OCR — pagination non précisée |
| **HYBRID** | 3 | CLINDAMYCINE | 0.016393 | Notice | OCR — pagination non précisée |

**Observation :** OLD=CÉLÉCOXIB → BM25=CLINDAMYCINE → SEMANTIC=CLINDAMYCINE → HYBRID=CLINDAMYCINE. Hybrid combines BM25 + Semantic for best coverage.


---

## Conclusion

| Metric | Week 2 OLD | Week 3 BM25 | Week 3 SEMANTIC | Week 3 HYBRID |
|---|---|---|---|---|
| Chunks in index | 1460 | 1460 | 1460 | 1460 |
| Query normalization | ✗ None | ✓ Fuzzy + Alias | ✓ Fuzzy + Alias | ✓ Fuzzy + Alias |
| Bilingual FR+EN | ✗ None | ✓ dict FR→EN | ✓ multilingual model | ✓ both |
| Search method | BM25 only | BM25 improved | Semantic (embeddings) | BM25 + Semantic (RRF) |
| Normalization accuracy | — | **40/40 (100%)** | **40/40 (100%)** | **40/40 (100%)** |
| Knowledge graph | ✗ None | ✓ 757 nodes | ✓ 757 nodes | ✓ 757 nodes |