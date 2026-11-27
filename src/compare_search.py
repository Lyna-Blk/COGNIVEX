
import csv
import json
import math
import re
import sys
from collections import Counter

from noms_commerciaux import charger_table, etendre_question

from rag_config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EVAL_DIR ,
    EXPERIENCE,
    MAX_WORDS,
    OVERLAP_WORDS,
    QUESTIONS_FILE,
    REFERENCES_FILE,
    ROOT,
    TOP_K,
    VECTOR_DB_DIR,
    canon_dci,
    charger_chunks,
    normalize,
    provenance,
    query_prefix,
    texte_indexe,
)

from recherche_hybride import RechercheHybride


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# CONFIGURATION

K_HIT = 3

BM25_SEUL = "--bm25-only" in sys.argv

SUFFIXE = "_bm25" if BM25_SEUL else ""

RAPPORT_FILE = (
    EVAL_DIR /
    f"comparaison_recherche_exp{EXPERIENCE}{SUFFIXE}.md"
)

CSV_FILE = (
    EVAL_DIR /
    f"hit_at_3_exp{EXPERIENCE}{SUFFIXE}.csv"
)

# CHARGEMENT DES QUESTIONS

def charger_questions() -> list[dict]:

    if not QUESTIONS_FILE.is_file():

        raise FileNotFoundError(
            f"Fichier de questions introuvable : {QUESTIONS_FILE}"
        )

    blocs = []
    courant = None

    for ligne in QUESTIONS_FILE.read_text(
        encoding="utf-8-sig"
    ).splitlines():

        ligne = ligne.strip()

        titre = re.match(
            r"^##\s*(\d+)\s*\.\s*(.+?)\s*$",
            ligne
        )

        if titre:

            courant = {
                "numero": int(titre.group(1)),
                "titre": titre.group(2),
                "lignes": []
            }

            blocs.append(courant)

        elif courant is not None and not re.match(
            r"^<!--.*-->$",
            ligne
        ):

            courant["lignes"].append(ligne)

    questions = []

    for b in blocs:

        paragraphe = []

        for l in b["lignes"]:

            if l:
                paragraphe.append(l)

            elif paragraphe:
                break

        if paragraphe:

            questions.append({

                "id": f"Q{b['numero']}",

                "type": b["titre"],

                "texte": " ".join(paragraphe)

            })

    return questions

# BM25 : RECHERCHE PAR MOTS-CLES

STOPWORDS = set("""
a au aux avec ce ces dans de des du elle en et il ils je la le les leur
lui ma mais me mes moi mon ne nos notre nous on ou par pas pour qu que
qui sa se ses si son sur ta te tes toi ton tu un une vos votre vous est
sont etre avoir faut peut peuvent puis dois doit quel quelle quels quelles
comment quand ou ce cette cet ete fait faire sans plus tout tous
""".split())


def tokens(texte: str) -> list[str]:

    mots = normalize(texte).split()

    return [

        m[:-1] if len(m) > 4 and m.endswith("s") else m

        for m in mots

        if m not in STOPWORDS

    ]


class BM25:

    def __init__(
        self,
        documents: list[str],
        k1=1.5,
        b=0.75
    ):

        self.k1 = k1
        self.b = b

        self.docs = [
            Counter(tokens(d))
            for d in documents
        ]

        self.len = [
            sum(c.values())
            for c in self.docs
        ]

        self.avg = (
            sum(self.len) / len(self.len)
            if self.len
            else 0
        )

        df = Counter(
            t
            for c in self.docs
            for t in c
        )

        n = len(self.docs)

        self.idf = {

            t: math.log(
                1 + (n - f + 0.5) / (f + 0.5)
            )

            for t, f in df.items()

        }

    def search(
        self,
        question: str,
        k: int
    ):

        if not self.docs or self.avg == 0:
            return []

        q = tokens(question)

        scores = []

        for i, c in enumerate(self.docs):

            s = 0.0

            for t in q:

                f = c.get(t, 0)

                if f:

                    s += (

                        self.idf[t] * f * (self.k1 + 1)

                        /

                        (
                            f + self.k1 * (
                                1 - self.b
                                + self.b * self.len[i] / self.avg
                            )
                        )

                    )

            scores.append(s)

        ordre = sorted(
            range(len(scores)),
            key=lambda i: -scores[i]
        )[:k]

        return [
            (i, scores[i])
            for i in ordre
            if scores[i] > 0
        ]

# RECHERCHE SEMANTIQUE

class RechercheSemantique:

    def __init__(self, chunks):

        import chromadb

        from sentence_transformers import SentenceTransformer

        self.index = {

            c["chunk_id"]: i

            for i, c in enumerate(chunks)

        }

        self.modele = SentenceTransformer(
            EMBEDDING_MODEL
        )

        self.collection = (

            chromadb.PersistentClient(
                path=str(VECTOR_DB_DIR)
            )

            .get_collection(COLLECTION_NAME)

        )

        if self.collection.count() != len(chunks):

            sys.exit(

                f"La base vectorielle contient "
                f"{self.collection.count()} passages mais il y en a "
                f"{len(chunks)} dans les chunks : elle est périmée.\n"

                "Reconstruisez-la : "
                "python src/build_vectordb.py --recalculer"

            )

    def search(
        self,
        question: str,
        k: int
    ):

        emb = self.modele.encode(

            [query_prefix() + question],

            normalize_embeddings=True

        )

        total = self.collection.count()

        if total == 0:
            return []

        res = self.collection.query(

            query_embeddings=emb.tolist(),

            n_results=min(total, k * 5)

        )

        resultats = []
        inconnus = 0

        for cid, dist in zip(
            res["ids"][0],
            res["distances"][0]
        ):

            indice = self.index.get(cid)

            if indice is None:

                inconnus += 1

                continue

            resultats.append(
                (indice, 1 - dist)
            )

            if len(resultats) >= k:
                break

        if inconnus:

            print(

                f"\n[AVERTISSEMENT] {inconnus} ID(s) "
                "ChromaDB ne correspondent pas aux chunks actuels. "

                "Reconstruisez la base : "
                "python src/build_vectordb.py --recalculer"

            )

        return resultats

# HIT@3 : EVALUATION

def charger_references() -> dict:

    if not REFERENCES_FILE.is_file():

        print(
            f"[AVERTISSEMENT] {REFERENCES_FILE.name} "
            "introuvable : pas de Hit@3."
        )

        return {}

    return json.loads(

        REFERENCES_FILE.read_text(
            encoding="utf-8"
        )

    ).get("questions", {})


def est_pertinent(
    chunk: dict,
    entrees: list[dict]
) -> bool:

    texte = normalize(chunk["text"])

    for e in entrees:

        if (
            "dci" in e
            and canon_dci(chunk["dci"]) != canon_dci(e["dci"])
        ):

            continue

        if (
            "doc_type" in e
            and normalize(chunk["doc_type"]) != normalize(e["doc_type"])
        ):

            continue

        if (
            "fichier" in e
            and normalize(e["fichier"]) not in normalize(chunk["fichier"])
        ):

            continue

        if (
            "contient" in e
            and not any(
                normalize(m) in texte
                for m in e["contient"]
            )
        ):

            continue

        return True

    return False


def hit_at_k(
    resultats,
    chunks,
    ref,
    k=K_HIT
):

    """
    1 / 0
    None si la question attend un refus.
    """

    if (
        not ref
        or ref.get("attendu") == "refus"
        or not ref.get("pertinent")
    ):

        return None

    return int(

        any(

            est_pertinent(chunks[i], ref["pertinent"])

            for i, _ in resultats[:k]

        )

    )

# AFFICHAGE DES RESULTATS

def extrait(
    chunk,
    n=130
):

    return (

        " ".join(chunk["text"].split())[:n]

        .replace("|", "/")

    )


def resume_dci(
    resultats,
    chunks
):

    """
    Médicaments retrouvés dans le top-K.
    Exemple : DICLOFENAC ×3.
    """

    if not resultats:
        return "aucun résultat"

    compte = Counter(

        chunks[i]["dci"]

        for i, _ in resultats

    )

    return ", ".join(

        f"{d} ×{n}"

        for d, n in compte.most_common()

    )

def symbole(hit):

    return (

        "n/a"

        if hit is None

        else ("✅ 1" if hit else "❌ 0")

    )

# COMPARAISON DES METHODES

def lancer_configs(
    question,
    etendue,
    methodes
):

    """
    Exécute chaque méthode :
    - question originale
    - question étendue avec la DCI
    """

    sortie = {}

    for mode, texte in (

        ("", question),

        ("+N", etendue)

    ):

        for nom, f in methodes.items():

            sortie[nom + mode] = f(texte)

    return sortie

# PROGRAMME PRINCIPAL

def main():

    # Chargement des questions et des chunks
    
    try:

        questions = charger_questions()

        chunks = charger_chunks()

    except (FileNotFoundError, ValueError) as e:

        sys.exit(str(e))

    # Chargement de la table des noms commerciaux

    table = charger_table()

    references = charger_references()

    # Question libre
 
    if "--question" in sys.argv:

        pos = sys.argv.index("--question")

        if pos + 1 >= len(sys.argv):

            sys.exit(
                "Veuillez fournir une question après --question."
            )

        questions = [{

            "id": "Q?",

            "type": "question libre",

            "texte": sys.argv[pos + 1]

        }]

        references = {}

    # Initialisation de BM25
    
    bm25 = BM25(

        [
            texte_indexe(c)
            for c in chunks
        ]

    )

    sem = None

    hybride = None

    # Initialisation de la recherche sémantique et hybride
   
    if not BM25_SEUL:

        if not VECTOR_DB_DIR.exists():

            sys.exit(

                "Base vectorielle introuvable : "
                "lancez d'abord python src/build_vectordb.py"

            )

        sem = RechercheSemantique(chunks)

        hybride = RechercheHybride(
            bm25,
            sem
        )

    # Méthodes de recherche
    
    methodes = {

        "BM25": lambda t: bm25.search(t, TOP_K)

    }

    if sem:

        methodes["Sémantique"] = (
            lambda t: sem.search(t, TOP_K)
        )

        methodes["Hybride"] = (
            lambda t: hybride.search(t, TOP_K)
        )

    configs = [

        n + m

        for m in ("", "+N")

        for n in methodes

    ]

    # Initialisation des résultats

    lignes_hit = []

    lignes_norm = []

    bloc_prov = []

    details = []

    csv_rows = []

    totaux = {

        c: [0, 0]

        for c in configs

    }

    meilleure = (

        "Hybride" if sem else "BM25"

    ) + "+N"

    # TRAITEMENT DE CHAQUE QUESTION
    
    for q in questions:

        # Extension de la question avec les DCI
       
        ext = etendre_question(
            q["texte"],
            table
        )

        # Recherche sur question brute et étendue
       
        res = lancer_configs(

            q["texte"],

            ext["question_etendue"],

            methodes

        )

        # Calcul de Hit@3
        
        ref = references.get(q["id"])

        hits = {

            c: hit_at_k(
                res[c],
                chunks,
                ref
            )

            for c in configs

        }

        for c in configs:

            if hits[c] is not None:

                totaux[c][0] += hits[c]

                totaux[c][1] += 1

        # Tableau Hit@3
       
        lignes_hit.append(

            f"| {q['id']} | "
            f"{q['type'].split('—')[-1].strip()[:42]} | "

            + " | ".join(

                symbole(hits[c])

                for c in configs

            )

            + " |"

        )

        csv_rows.append({

            "question": q["id"],

            **{

                c: (
                    ""
                    if hits[c] is None
                    else hits[c]
                )

                for c in configs

            }

        })

        # Résultats de normalisation des noms commerciaux
       
        corr = ", ".join(

            f"{c['nom']} → {c['dci']}"

            for c in ext["correspondances"]

            if c["ajoute"]

        ) or "—"

        proches = ", ".join(

            f"{p['mot'].upper()} ≈ "
            f"{p['proche_de']} "
            f"({p['dci']}, {p['similarite']})"

            for p in ext["proches"]

        ) or "—"

        etendue = (

            ext["question_etendue"]

            if ext["question_etendue"] != q["texte"]

            else "(inchangée)"

        )

        lignes_norm.append(

            f"| {q['id']} | {corr} | {proches} | "
            f"{etendue[len(q['texte']):].strip() or etendue} |"

        )

        # Provenance des meilleurs passages
        
        bloc_prov.append(

            f"**{q['id']}** — {q['texte'][:110]}"

            f"{'…' if len(q['texte']) > 110 else ''}"

        )

        bloc_prov += [

            "",

            "| # | pertinent | DCI | produit | type de document | "
            "fichier | page | section | type de source | niveau |",

            "|---|---|---|---|---|---|---|---|---|---|"

        ]

        top = res[meilleure][:K_HIT]

        if not top:

            bloc_prov.append(

                "| – | – | aucun passage retrouvé | | | | | | | |"

            )

        for rang, (i, _) in enumerate(top, 1):

            c = chunks[i]

            type_src, niveau = provenance(c)

            ok = (

                "n/a"

                if not ref or not ref.get("pertinent")

                else (

                    "✅"

                    if est_pertinent(c, ref["pertinent"])

                    else "❌"

                )

            )

            bloc_prov.append(

                f"| {rang} | {ok} | {c['dci']} | "
                f"{c['produit']} | {c['doc_type']} | "

                f"{c['fichier'].split('/')[-1]} | "
                f"{c['page']} | {c['section'][:45]} | "
                f"{type_src} | {niveau} |"

            )

        bloc_prov.append("")

        # ----------------------------------------------------
        # G. Détail des résultats
        # ----------------------------------------------------

        bloc = [

            f"### {q['id']} — {q['type']}",

            f"**Question :** {q['texte']}",

            ""

        ]

        if ext["question_etendue"] != q["texte"]:

            bloc += [

                f"**Question étendue :** "
                f"{ext['question_etendue']}",

                ""

            ]

        for c in configs:

            bloc += [

                f"**{c}** — Hit@3 : {symbole(hits[c])}",

                "",

                "| # | score | DCI | produit | doc | page | extrait |",

                "|---|---|---|---|---|---|---|"

            ]

            if not res[c]:

                bloc.append(

                    "| – | – | aucun résultat | | | | |"

                )

            for rang, (i, s) in enumerate(res[c], 1):

                ch = chunks[i]

                bloc.append(

                    f"| {rang} | {s:.3f} | "
                    f"{ch['dci']} | {ch['produit']} | "
                    f"{ch['doc_type']} | {ch['page']} | "
                    f"{extrait(ch)} |"

                )

            bloc.append("")

        details.append(
            "\n".join(bloc)
        )

        # Affichage dans le terminal
       
        print(
            f"\n{q['id']} — {q['type']}"
        )

        if ext["correspondances"]:

            print(
                f"   normalisation : {corr}"
            )

        if ext["proches"]:

            print(
                f"   ⚠ noms proches (LASA) : {proches}"
            )

        for c in configs:

            print(

                f"   {c:<16} "
                f"Hit@3 {symbole(hits[c]):<5} "
                f"{resume_dci(res[c], chunks)}"

            )

    # TOTAL HIT@3

    ligne_total = (

        "| **Total** | Hit@3 (questions évaluables) | "

        + " | ".join(

            f"**{h}/{n}**"

            for h, n in (
                totaux[c]
                for c in configs
            )

        )

        + " |"

    )

    # GENERATION DU RAPPORT MARKDOWN

    EVAL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    rapport = [

        "# Comparaison : mots-clés, sémantique et hybride "
        "— avec et sans normalisation des noms commerciaux",

        "",

        f"- Questions : {len(questions)} "
        "(docs/evaluation/questions_llm.md) "
        "— références : docs/evaluation/references_hit_at_3.json",

        f"- Expérience : {EXPERIENCE} "
        f"({MAX_WORDS} mots max, chevauchement {OVERLAP_WORDS}) "
        f"— {len(chunks)} passages dont "
        f"{sum(c['doc_type'] == 'Nomenclature' for c in chunks)} "
        "de nomenclature",

        "- BM25 : sans accents, sans mots vides. " + (

            f"Sémantique : `{EMBEDDING_MODEL}` + ChromaDB "
            "(cosinus). Hybride : fusion RRF des rangs "
            "BM25 et sémantique."

            if sem

            else

            "Sémantique et hybride : NON exécutés "
            "dans ce rapport (option --bm25-only)."

        ),

        "- Suffixe **+N** = la question est étendue "
        "avec la DCI du nom commercial avant la recherche.",

        f"- Hit@3 = 1 si l'un des {K_HIT} premiers passages "
        "contient la réponse attendue "
        "(définition dans le JSON de références).",

        "",

        "## 1. Hit@3 par question",

        "",

        "| Question | Type | "
        + " | ".join(configs)
        + " |",

        "|---|---|"
        + "---|" * len(configs),

        *lignes_hit,

        ligne_total,

        "",

        "> n/a : question dont la bonne réaction est un refus "
        "(Q7 nom inexistant, Q8 hors périmètre) ; "
        "il n'y a pas de passage de référence. "
        "Le seuil de refus fera l'objet d'un travail séparé.",

        "",

        "## 2. Normalisation des noms commerciaux",

        "",

        "| Question | Nom commercial reconnu → DCI | "
        "Noms proches non reconnus (risque LASA) | "
        "Texte ajouté à la question |",

        "|---|---|---|---|",

        *lignes_norm,

        "",

        f"## 3. Tableau de provenance ({meilleure}, top-{K_HIT})",

        "",

        "Niveau d'autorité : 1 = officielle algérienne ; "
        "2 = RCP/notice de produit ou export de nomenclature ; "
        "3 = institutionnelle étrangère ; "
        "4 = site professionnel ; "
        "5 = hors référence ; 6 = article/image.",

        "",

        *bloc_prov,

        "## 4. Détail des résultats",

        "",

        *details,

    ]

    RAPPORT_FILE.write_text(

        "\n".join(rapport),

        encoding="utf-8"

    )

    # GENERATION DU CSV HIT@3
    
    with CSV_FILE.open(

        "w",

        encoding="utf-8-sig",

        newline=""

    ) as f:

        w = csv.DictWriter(

            f,

            fieldnames=["question"] + configs

        )

        w.writeheader()

        w.writerows(csv_rows)

    # AFFICHAGE FINAL

    print("\n========== TOTAL HIT@3 ==========")

    print(

        " ; ".join(

            f"{c} {totaux[c][0]}/{totaux[c][1]}"

            for c in configs

        )

    )

    print(
        f"\nRapport écrit : {RAPPORT_FILE.relative_to(ROOT)}"
    )

    print(
        f"Tableau Hit@3 : {CSV_FILE.relative_to(ROOT)}"
    )


if __name__ == "__main__":

    main()

