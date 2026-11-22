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
| Semaine 2 | Découpage en chunks, embeddings, base vectorielle, comparaison mots-clés / sémantique | Terminée |

### Semaine 1 — Préparation du corpus

Le corpus (`data/corpus/`) n’est jamais modifié ; les résultats sont écrits dans `data/processed/` et `data/processed_corpus/`.

| Étape | Script | Rôle |
|---|---|---|
| 1. Audit | `src/audit_corpus.py` | Détecte les PDF scannés, vides ou corrompus, les doublons (SHA-256) et le bruit (en-têtes/pieds de page répétés). Écrit `corpus_audit_report.json` et `.txt`. |
| 2. OCR et nettoyage | `src/ocr_pipeline.py` | OCR (RapidOCR) des PDF scannés et des images, extraction et nettoyage des PDF avec texte. Produit un Markdown par document, avec un titre `## Page N` pour citer la page. Reprend là où il s’est arrêté. |
| 3. Métadonnées | `src/generate_corpus_metadata.py` | Regroupe par DCI les fiches DCI, les fichiers, le type de source, le niveau d’autorité et la qualité du texte dans `corpus_metadata.json`. |

### Semaine 2 — Recherche par mots-clés et recherche sémantique

| Étape | Fichier | Rôle |
|---|---|---|
| 1. Chunks | `src/build_chunks.py` | Découpe le texte page par page en passages de 120 mots (chevauchement 20) avec DCI, marque, type de document, fichier et page. Sortie : `chunks.jsonl` (**4 411 chunks**). |
| 2. Embeddings | `notebooks/recherche.ipynb` | Calcule les embeddings (`multilingual-e5-small`, 384 dimensions) et monte la base ChromaDB (cosinus). |
| 3. Comparaison | `src/compare_search.py` | Pose les 8 questions de `questions_llm.md` à BM25 et à la recherche sémantique (top-5) et écrit le rapport de comparaison. |

```bash
python src/compare_search.py              # mots-clés + sémantique
python src/compare_search.py --bm25-only  # mots-clés seulement
```

#### Premières observations (8 questions, top-5)
- Les deux méthodes retrouvent souvent des passages différents (0 à 2 chunks communs sur 5) : elles sont complémentaires.
- Pour une DCI précise (Q1), les deux retrouvent la bonne DCI. Pour une marque absente (Q2, CARDENSIEL), aucune ne retrouve de passage qui répond.
- Pour les questions hors périmètre ou pièges (Q7, Q8), elles retournent quand même 5 résultats sans rapport clair.
- Les scores sémantiques sont très proches (0,85 à 0,91) : un score élevé ne prouve pas que la réponse est dans le corpus.

**Suite prévue** : seuil pour répondre « information non trouvée », recherche hybride, puis liaison avec le LLM.

#### Pistes pour la suite

- Ajouter un **seuil** ou une règle de décision pour répondre « information non trouvée dans les sources » quand les passages ne répondent pas à la question.
- Tester une recherche **hybride** (BM25 + sémantique) et un filtrage par DCI.
- Relier la recherche au LLM (Groq) avec le format de réponse prévu et les références (document, page).

## Documentation

### 1. Présentation du projet

- [Cahier des charges](docs/CDC_Projet_2_Pharmeazor_FINAL.pdf)

### 2. Questions de test

- [Questions posées au LLM](docs/evaluation/questions_llm.md)

### 3. Évaluation du LLM
- [Semaine 1 — Réponses du LLM seul (sans RAG)](docs/evaluation/reponses_sans_RAG.md)

- [Semaine 1 — Analyse du réponses du LLM sans RAG ](docs/evaluation/analyse_reponses_sans_RAG.md)

### 4. Recherche

- [Semaine 2 — Comparaison recherche par mots-clés / recherche sémantique](docs/evaluation/comparaison_recherche.md)
- [Semaine 2 — Notebook : embeddings et base vectorielle](notebooks/recherche.ipynb)

## Équipe
- Lyna Anfel BELKHAIRI
- Ibtihal BOUFENNARA
- Oumeima DREIBINE
- Hadil KERSOUHI
- Aya BECHKRI
