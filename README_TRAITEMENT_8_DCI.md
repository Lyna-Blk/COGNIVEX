# Traitement des 8 DCI antibiotiques (même format que les 8 antihypertenseurs)

## Ce que fait `process_my_dci.py`
Pour chaque DCI (ceftriaxone, azithromycine, clarithromycine, ciprofloxacine, lévofloxacine,
doxycycline, cotrimoxazole, métronidazole) :

1. **Corpus** : copie les RCP/Notice vers `data/corpus/<dci>/<dci>_RCP_<SOURCE>.pdf` et `<dci>_Notice_<SOURCE>.pdf`
   (SOURCE = `EMC` ou `ANSM`, détectée automatiquement depuis le contenu du PDF).
2. **Fiche** : génère `data/fiches_dci/<dci>.md` au format du modèle (ATC, noms commerciaux issus de l'Excel,
   documents de référence, recherche ANPP, sources consultées, précision).
3. **Compléments** : range articles, fiches produit et notes dans
   `data/documents_complementaires_non_reference/<dci>/` (dossier ignoré par `generate_corpus_metadata.py`).
4. **Détails produits** : `data/processed/produits_details.json` (laboratoire, n° d'enregistrement, dates, conditionnement).
5. **JSON global** : relance `generate_corpus_metadata.py` -> `data/processed/corpus_metadata.json` (16 DCI).
6. **Contrôle qualité** : `data/processed/rapport_qualite_8_dci.md`.

## Utilisation
```bash
pip install pandas openpyxl
python process_my_dci.py --src "chemin/vers/PHARMEAZOR_MY_8_DCI"
```
Rejouable sans doublons. Nécessite `pdftotext`/`pdfinfo` (poppler) pour identifier les PDF.

## Modification de `generate_corpus_metadata.py`
Ajout de `"electronic medicines compendium": 3` et `"journal officiel": 3` dans `SOURCE_LEVELS`
(sinon les fiches s'appuyant sur eMC (UK) obtenaient `authority_level = 0`).
Les 8 enregistrements existants du JSON restent strictement identiques.

## Corrections apportées après relecture
- Articles : ceftriaxone (était vide), clarithromycine (copie de l'azithromycine) et métronidazole
  (copie de l'article du cotrimoxazole) remplacés par des références vérifiées. L'article cotrimoxazole d'origine,
  correct, est conservé. Les champs non retrouvés sont marqués « non vérifié » (rien d'inventé).
- Ceftriaxone : `SOURCE.txt` rédigé ; `CETRIAL.txt` créé avec les seules infos vérifiées (laboratoire et n° d'enregistrement « à confirmer »).
- Le résultat de la recherche ANPP n'est plus affirmé par défaut : « non trouvé » seulement si les notes sources le disent.
- Faux positif corrigé : les notices eMC (azithromycine, clarithromycine, ciprofloxacine) couvrent bien 250 et 500 mg.
