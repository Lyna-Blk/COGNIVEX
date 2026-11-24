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

## Installation

Depuis le dossier du projet, installez les dépendances :

```bash
python -m pip install -r requirements.txt
``` 
## Documentation

### 1. Présentation du projet

- [Cahier des charges](docs/CDC_Projet_2_Pharmeazor_FINAL.pdf)

### 2. Questions de test

- [Questions posées au LLM](docs/evaluation/questions_llm.md)

### 3. Évaluation du LLM
- [Semaine 1 — Réponses du LLM seul (sans RAG)](docs/evaluation/reponses_sans_RAG.md)

- [Semaine 1 — Analyse du réponses du LLM sans RAG ](docs/evaluation/analyse_reponses_sans_RAG.md)

### 4. Recherche dans le corpus (semaine 2)

Découpage des documents, embeddings sémantiques (TF-IDF + SVD, calculés localement) et comparaison avec la recherche BM25 :

```bash
.\.venv\Scripts\python.exe src\build_vector_store.py
.\.venv\Scripts\python.exe src\compare_search.py
```

- [Semaine 2 — Résultats de la comparaison](docs/evaluation/resultats_comparaison.md)
- [Semaine 2 — Comparaison mots-clés et recherche sémantique](docs/evaluation/comparaison_recherche.md)
- [Semaine 2 — Analyse de la comparaison](docs/evaluation/analyse_comparaison_recherche.md)


## Équipe
- Lyna Anfel BELKHAIRI
- Ibtihal BOUFENNARA
- Oumeima DREIBINE
- Hadil KERSOUHI
- Aya BECHKRI
