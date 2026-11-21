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
- PyMuPDF (`fitz`) et pypdf : lecture des PDF
- RapidOCR (`rapidocr_onnxruntime`) : OCR des documents scannés et des images
- `sentence-transformers` avec le modèle `intfloat/multilingual-e5-small` : embeddings
- ChromaDB : base vectorielle (similarité cosinus)
- BM25 (implémenté dans `src/compare_search.py`, sans dépendance externe) : recherche par mots-clés

## Installation

Depuis le dossier du projet, installez les dépendances :

```bash
python -m pip install -r requirements.txt
```

## Avancement du projet

| Semaine | Contenu | Statut |
|---|---|---|
| Semaine 1 | Collecte et préparation du corpus (audit, OCR, nettoyage, métadonnées) ; réponses du LLM seul, sans RAG | Terminée |
| Semaine 2 | Découpage en chunks, embeddings, base vectorielle, comparaison mots-clés / sémantique | Terminée |

### Semaine 1 — Préparation du corpus

Le corpus est stocké dans `data/corpus/`, organisé par **DCI** puis par **nom commercial** (`data/corpus/<DCI>/<marque>/fichier.pdf`). Les fichiers originaux ne sont jamais modifiés : tous les résultats sont écrits dans `data/processed/` et `data/processed_corpus/`.

Chaîne de traitement (à lancer depuis la racine du projet, dans cet ordre) :

```bash
python src/audit_corpus.py            # 1. audit de la qualité du corpus
python src/ocr_pipeline.py            # 2. OCR + nettoyage -> Markdown
python src/generate_corpus_metadata.py  # 3. métadonnées unifiées du corpus
```

#### 1. Audit du corpus — `src/audit_corpus.py`

Analyse chaque fichier de `data/corpus/` pour savoir s’il est exploitable par le RAG :

- **Extractibilité du texte** : PDF avec vrai texte ou PDF scanné (image seule).
- **Nombre de caractères** : détection des documents vides ou presque vides (moins de 100 caractères au total, moins de 200 par page pour les pages « courtes »).
- **Fichiers corrompus** : PDF illisibles ou sans page.
- **Doublons** : comparaison par taille puis par empreinte SHA-256.
- **Bruit** : en-têtes et pieds de page répétés (bloc présent au moins 5 fois).
- **Documents à passer à l’OCR** : PDF dont au moins 50 % des pages n’ont aucun texte extractible.

Sorties : `data/processed/corpus_audit_report.json` (exploitable par les scripts suivants) et `data/processed/corpus_audit_report.txt` (lisible par l’équipe).

#### 2. OCR et nettoyage — `src/ocr_pipeline.py`

Lit le rapport d’audit et produit une version texte (Markdown) de chaque document dans `data/processed_corpus/`, en miroir de l’arborescence du corpus :

| Type de fichier | Traitement |
|---|---|
| PDF scannés ou peu de texte | Rendu des pages (200 DPI) avec PyMuPDF, puis OCR avec RapidOCR |
| Images (`.png`, `.jpg`, …) | OCR direct avec RapidOCR |
| PDF avec texte | Extraction du texte intégré, puis suppression du bruit (en-têtes, pieds de page, coordonnées du laboratoire) |
| CSV | Copiés tels quels (données structurées) |

Points importants :

- Chaque page est écrite sous un titre `## Page N`, ce qui permet de **citer la page** dans les réponses.
- Chaque fichier `.md` commence par un en-tête (source, DCI, marque, méthode utilisée, date, nombre de caractères).
- Le script **reprend là où il s’est arrêté** : les fichiers déjà traités sont ignorés. Un journal est écrit dans `data/processed/ocr_pipeline_log.json`.
- Les motifs de bruit viennent d’une liste fixe et des blocs répétés repérés par l’audit.

#### 3. Métadonnées du corpus — `src/generate_corpus_metadata.py`

Construit un seul fichier, `data/processed/corpus_metadata.json`, à partir du corpus, des textes traités, des fiches DCI (`data/fiches_dci/`), du rapport d’audit et du journal OCR.

Pour chaque DCI, il regroupe :

- les **fiches DCI** : code ATC, présence dans la nomenclature MIPH, version consultée, produits (marque, forme, dosage, laboratoire), sources et remarques ;
- les **fichiers sources** classés par marque, avec type de document (RCP, notice, nomenclature, image, article…), type de source, **niveau d’autorité** (1 = source officielle algérienne, jusqu’à 6 = source la moins fiable), taille, empreinte, nombre de pages, statut d’audit et d’OCR, chemin du texte traité, nombre de caractères et **qualité du texte** (`ok`, `low_text`, `no_text`…) ;
- les statistiques par DCI, les doublons, les fichiers à faible quantité de texte et les fiches DCI sans dossier correspondant dans le corpus.

### Semaine 2 — Recherche par mots-clés et recherche sémantique

Objectif : retrouver les bons passages dans les documents, avant d’utiliser le LLM. Deux méthodes sont mises en place puis comparées.

```text
processed_corpus/*.md  ──►  build_chunks.py  ──►  chunks.jsonl  ──►  notebook (embeddings + ChromaDB)
                                                        │                         │
                                                        └──────►  compare_search.py  ◄──────┘
                                                                          │
                                                       docs/evaluation/comparaison_recherche.md
```

#### 1. Découpage en chunks — `src/build_chunks.py`

- Source du texte : le Markdown de `data/processed_corpus/` s’il existe et contient du texte ; sinon extraction directe du PDF original avec pypdf. Le champ `text_source` garde cette information.
- Découpage en passages de **120 mots maximum** avec un **chevauchement de 20 mots**, page par page (un chunk ne traverse jamais deux pages).
- Chaque chunk reçoit un identifiant (`<DCI>_<marque>_<fichier>_p<page>_c<numéro>`) et ses métadonnées : DCI, marque, type de document (RCP, Notice, autre), fichier, page.
- Les pages sans texte sont comptées et signalées.
- Sortie : `data/processed/chunks.jsonl` — **4 411 chunks** pour le corpus actuel.

#### 2. Embeddings et base vectorielle — `notebooks/recherche.ipynb`

- Modèle : `intfloat/multilingual-e5-small` (multilingue, bon en français, vecteurs de 384 dimensions, 512 tokens maximum).
- Le modèle demande le préfixe `passage: ` côté documents et `query: ` côté questions.
- Les vecteurs sont normalisés et stockés dans **ChromaDB** (`data/vectordb`, distance cosinus) avec le texte et les métadonnées (DCI, produit, type de document, fichier, page, section), pour pouvoir citer la source.
- La base est reconstruite à chaque exécution : pas de doublons. Le notebook contient aussi un test rapide de recherche.

#### 3. Comparaison des deux méthodes — `src/compare_search.py`

```bash
python src/compare_search.py              # mots-clés + sémantique
python src/compare_search.py --bm25-only  # mots-clés seulement
```

Pour chaque question de `docs/evaluation/questions_llm.md` (8 questions), le script retourne les 5 meilleurs passages avec :

- **BM25** : recherche par mots-clés (sans accents, sans mots vides, pluriels simplifiés) ;
- **recherche sémantique** : embeddings + ChromaDB.

Aucune réponse de référence n’est nécessaire : on compare les passages retrouvés, les DCI retrouvées et le nombre de chunks communs. Le script signale aussi si la base vectorielle contient d’anciens chunks qui ne correspondent plus à `chunks.jsonl`. Le rapport complet est dans [`docs/evaluation/comparaison_recherche.md`](docs/evaluation/comparaison_recherche.md).

#### Premières observations (8 questions, top-5)

- **Les deux méthodes retrouvent souvent des passages différents** : 0 à 2 chunks communs sur 5. Elles sont donc complémentaires.
- **Question sur une DCI précise (Q1, amoxicilline + acide clavulanique)** : les deux méthodes retrouvent la bonne DCI à chaque rang.
- **Question sur une marque absente ou peu présente (Q2, CARDENSIEL)** : aucune des deux méthodes ne retrouve de passage qui répond à la question ; les résultats sont des RCP d’autres médicaments. La recherche seule ne suffit pas à dire que l’information est absente.
- **Question croisant deux médicaments (Q3, ramipril + diclofénac)** : la recherche sémantique ne retourne que du diclofénac (5/5), alors que BM25 retourne des DCI plus variées.
- **Questions hors périmètre ou pièges (Q7, Q8)** : les deux méthodes retournent quand même 5 résultats, sans rapport clair avec la question.
- **Les scores sémantiques sont très proches** (environ 0,85 à 0,91 pour toutes les questions) : un score élevé ne prouve pas que la réponse est dans le corpus. Les scores BM25 et cosinus ne sont pas comparables entre eux.

#### Pistes pour la suite

- Ajouter un **seuil** ou une règle de décision pour répondre « information non trouvée dans les sources » quand les passages ne répondent pas à la question.
- Tester une recherche **hybride** (BM25 + sémantique) et un filtrage par DCI.
- Relier la recherche au LLM (Groq) avec le format de réponse prévu et les références (document, page).

## Structure du projet

```text
data/
  corpus/              documents originaux (par DCI / marque) — jamais modifiés
  processed_corpus/    texte extrait par OCR / nettoyage (Markdown, une section par page)
  fiches_dci/          fiches DCI (code ATC, noms commerciaux, sources)
  processed/           rapports d'audit, journal OCR, corpus_metadata.json, chunks.jsonl
  vectordb/            base vectorielle ChromaDB
docs/
  evaluation/          questions, réponses du LLM, comparaison de recherche
notebooks/
  recherche.ipynb      embeddings + base vectorielle
src/
  audit_corpus.py            audit de la qualité du corpus
  ocr_pipeline.py            OCR + nettoyage
  generate_corpus_metadata.py  métadonnées du corpus
  build_chunks.py            découpage en chunks
  rag_config.py              paramètres communs de la recherche
  compare_search.py          comparaison mots-clés / sémantique
```

## Documentation

### 1. Présentation du projet

- [Cahier des charges](docs/CDC_Projet_2_Pharmeazor_FINAL.pdf)

### 2. Questions de test

- [Questions posées au LLM](docs/evaluation/questions_llm.md)

### 3. Évaluation du LLM

- [Semaine 1 — Réponses du LLM seul (sans RAG)](docs/evaluation/reponses_sans_RAG.md)
- [Semaine 1 — Analyse des réponses du LLM sans RAG](docs/evaluation/analyse_reponses_sans_RAG.md)

### 4. Recherche

- [Semaine 2 — Comparaison recherche par mots-clés / recherche sémantique](docs/evaluation/comparaison_recherche.md)
- [Semaine 2 — Notebook : embeddings et base vectorielle](notebooks/recherche.ipynb)

## Équipe

- Lyna Anfel BELKHAIRI
- Ibtihal BOUFENNARA
- Oumeima DREIBINE
- Hadil KERSOUHI
- Aya BECHKRI


