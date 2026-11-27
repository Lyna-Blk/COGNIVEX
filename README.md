# Cognivex-Pharmaazor

**Assistant documentaire sur les médicaments référencés en Algérie**  
Projet RCR — M1 IA — Université Constantine 2 – Abdelhamid Mehri

## Présentation

Pharmaazor est un assistant documentaire qui aide à rechercher des informations sur les médicaments à partir de documents et de sources identifiés.

Le projet vise à retrouver les passages utiles et à indiquer les documents utilisés. Lorsque les sources disponibles ne permettent pas de vérifier une information, le système doit le signaler au lieu de la compléter par une supposition.

## Objectifs

- Identifier les médicaments par leur DCI et leurs noms commerciaux.
- Organiser les informations disponibles : forme, dosage et laboratoire.
- Retrouver les passages pertinents dans les documents collectés.
- Accompagner les réponses de références vérifiables.
- Signaler les informations manquantes, les différences entre sources et les limites de la recherche.

## Sources documentaires

Les documents sont conservés avec leurs références lorsque celles-ci sont disponibles : nom de la source, lien, pays et date de consultation.

- **ANPP** : source prioritaire pour les RCP et notices algériens disponibles.
- **Nomenclature du MIPH** : informations sur les produits enregistrés, notamment leurs noms commerciaux, formes et dosages.
- **Sources officielles étrangères** : utilisées en complément lorsque le document algérien recherché n’a pas été trouvé. Le pays d’origine est précisé ; elles ne sont pas présentées comme des documents algériens.
- **Sources secondaires** : identifiées comme telles dans le corpus et dans les réponses.

Lorsqu’un document n’est pas trouvé sur le portail de l’ANPP, l’équipe note les termes recherchés, la méthode et la date de recherche. La mention « document ANPP non trouvé » décrit le résultat de cette recherche ; elle ne prouve pas que le document n’existe pas.

## Limites

Pharmaazor est un outil documentaire. Il ne remplace pas un médecin ou un pharmacien et ne pose pas de diagnostic.

Il ne recommande pas de traitement ni de substitution. Une information absente des sources disponibles ne doit pas être présentée comme vérifiée.

## Format prévu des réponses

Quand les documents le permettent, la réponse présente :

1. Une réponse courte.
2. Une explication simple.
3. Le document, la source et le passage utilisés.
4. Les limites ou les informations qui n’ont pas pu être vérifiées.

## Technologies

- Python
- API Groq avec le modèle imposé `openai/gpt-oss-120b`
- PyMuPDF, pypdf, RapidOCR : lecture des PDF et OCR
- `sentence-transformers` (`intfloat/multilingual-e5-small`) et ChromaDB : recherche sémantique
- BM25 : recherche par mots-clés

## Installation

Depuis le dossier du projet, installez les dépendances :

```bash
python -m pip install -r requirements.txt
``` 

## Avancement du projet

| Semaine | Contenu | Statut |
|---|---|---|
| Semaine 1 | Collecte et préparation du corpus (audit, OCR, nettoyage, métadonnées) ; réponses du LLM seul, sans RAG | Terminée |
| Semaine 2 | Chunks, embeddings, base vectorielle, comparaison mots-clés / sémantique / hybride, normalisation des noms commerciaux | À valider (retour de l'enseignant) |
| Semaine 3 | Graphe de connaissances : ontologie minimale, extraction, peuplement | Préparée (à soumettre quand la recherche est validée) |

### Semaine 1 — Préparation du corpus

Le corpus (`data/corpus/`) n’est jamais modifié ; les résultats sont écrits dans `data/processed/` et `data/processed_corpus/`.

| Étape | Script | Rôle |
|---|---|---|
| 1. Audit | `src/audit_corpus.py` | Détecte les PDF scannés, vides ou corrompus, les doublons (SHA-256) et le bruit (en-têtes/pieds de page répétés). Écrit `corpus_audit_report.json` et `.txt`. |
| 2. OCR et nettoyage | `src/ocr_pipeline.py` | OCR (RapidOCR) des PDF scannés et des images, extraction et nettoyage des PDF avec texte. Produit un Markdown par document, avec un titre `## Page N` pour citer la page. Reprend là où il s’est arrêté. |
| 3. Métadonnées | `src/generate_corpus_metadata.py` | Regroupe par DCI les fiches DCI, les fichiers, le type de source, le niveau d’autorité et la qualité du texte dans `corpus_metadata.json`. |

### Semaine 2 — Recherche par mots-clés, sémantique et hybride (avec normalisation des noms commerciaux)

| Étape | Fichier | Rôle |
|---|---|---|
| 1. Table des noms commerciaux | `src/noms_commerciaux.py` | Construit `data/processed/table_noms_commerciaux.csv` et `data/processed/paires_noms_proches_lasa.csv` (nom commercial → DCI, forme, dosage, laboratoire, niveau de source) à partir de la nomenclature MIPH (Excel), des fiches produit et des CSV Pharm'Net. Fournit `etendre_question()` : « CARDENSIEL » devient « CARDENSIEL (DCI : bisoprolol) » avant la recherche, et signale les noms proches non reconnus (risque LASA, ex. ANTALGEN ≈ ANTALGAN). |
| 2. Chunks | `src/build_chunks.py` | Découpe tous les documents (Markdown OCR de `processed_corpus`, sinon PDF) en passages, avec DCI, marque, type de document, fichier, page et **section** (4.6 Grossesse…). Ajoute les passages de **nomenclature** (un par nom commercial, un par DCI). Taille selon `EXPERIENCE` dans `rag_config.py` (ou variable `COGNIVEX_EXP`). |
| 3. Embeddings + base | `src/build_vectordb.py` | Calcule les embeddings si besoin (`--recalculer` après chaque `build_chunks.py`) et monte la base ChromaDB. |
| 4. Hybride | `src/recherche_hybride.py` | Fusion RRF des classements BM25 et sémantique. |
| 5. Comparaison | `src/compare_search.py` | Compare BM25, sémantique et hybride, sans puis avec normalisation (`+N`) : Hit@3 par question, tableau de normalisation, tableau de provenance. Références : `docs/evaluation/references_hit_at_3.json`. |

```bash
python src/noms_commerciaux.py     # table + paires LASA
python src/build_chunks.py
python src/build_vectordb.py --recalculer
python src/compare_search.py                      # BM25 + sémantique + hybride, avec et sans normalisation
python src/compare_search.py --bm25-only          # sans modèle (rapport *_bm25.md)
python src/compare_search.py --question "Amlor 5 mg"   # une question libre
```

### Semaine 3 — Graphe de connaissances (après validation de la recherche)


| Fichier | Rôle |
|---|---|
| `docs/ontologie.md` | Ontologie minimale : 9 classes, 10 relations, limites |
| `src/build_kg.py` | Extraction + peuplement → `data/kg/` (`noeuds.csv`, `relations.csv`, `kg.graphml`, `kg_stats.md`) |
| `src/kg_requetes.py` | Requêtes de démonstration (DCI d'un nom commercial, équivalents, interactions) |

```bash
python src/build_kg 

```

#### Pistes pour la suite


## Documentation

### 1. Présentation du projet

- [Cahier des charges](docs/CDC_Projet_2_Pharmeazor_FINAL.pdf)

### 2. Questions de test

- [Questions posées au LLM](docs/evaluation/questions_llm.md)

### 3. Évaluation du LLM
- [Semaine 1 — Réponses du LLM seul (sans RAG)](docs/evaluation/reponses_sans_RAG.md)

- [Semaine 1 — Analyse du réponses du LLM sans RAG ](docs/evaluation/analyse_reponses_sans_RAG.md)

### 4. Recherche

- [Comparaison BM25 et recherche sémantique — expérience 1 (120/20)](docs/evaluation/comparaison_recherche_exp1.md)
- [Comparaison BM25 et recherche sémantique — expérience 2 (240/40)](docs/evaluation/comparaison_recherche_exp2.md)
- [Comparaison BM25 et recherche sémantique — expérience 3 (500/75)](docs/evaluation/comparaison_recherche_exp3.md)
- [Synthèse de la comparaison des tailles de chunks](docs/evaluation/comparaison_tailles_chunks.md)
- [Semaine 2 — Notebook : embeddings et base vectorielle](notebooks/recherche.ipynb)

## Équipe
- Lyna Anfel BELKHAIRI
- Ibtihal BOUFENNARA
- Oumeima DREIBINE
- Hadil KERSOUHI
- Aya BECHKRI