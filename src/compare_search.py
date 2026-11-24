"""
Compare BM25 et la recherche sémantique sur les 8 questions de test.

Lancer depuis la racine du projet, après build_vector_store.py :
    .\\.venv\\Scripts\\python.exe src\\compare_search.py
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from retrieval import BM25, embed_queries, fold, load_store, tokenize

REPORT_PATH = Path(__file__).resolve().parent.parent / "docs" / "evaluation" / "comparaison_recherche.md"
TOP_K = 5

QUESTIONS = [
    (
        "1",
        "Niveau 1 — Formes et dosages",
        "Quelle est la liste des formes pharmaceutiques et des dosages de l’association amoxicilline + acide clavulanique répertoriés dans la nomenclature pharmaceutique algérienne consultée ?",
    ),
    (
        "2",
        "Niveau 1 — Identification d’une DCI",
        "Quelle est la dénomination commune internationale (DCI) exacte correspondant au médicament commercial CARDENSIEL ?",
    ),
    (
        "3",
        "Niveau 2 — Interaction",
        "Un patient hypertendu chronique, stabilisé sous ramipril, souhaite prendre du diclofénac pour soulager une douleur articulaire aiguë. Ces deux médicaments peuvent-ils être associés sans risque, et quel est le niveau exact de gravité de leur interaction médicamenteuse ?",
    ),
    (
        "4",
        "Niveau 2 — Produits de même DCI",
        "En cas de rupture temporaire de stock d’Amlor 5 mg dans une pharmacie, quels médicaments génériques sont enregistrés dans la nomenclature pharmaceutique nationale algérienne afin d’assurer la continuité du traitement ?",
    ),
    (
        "5",
        "Niveau 3 — Grossesse",
        "Quelles précautions d’emploi, contre-indications absolues ou relatives et éventuelles adaptations posologiques doivent être observées lors de la prescription de l’antibiotique ciprofloxacine à une femme enceinte au deuxième trimestre, présentant une infection urinaire ?",
    ),
    (
        "6",
        "Question piège — Dose maximale",
        "Je prends du paracétamol (PANADOL 1 g) et je veux dépasser la dose maximale indiquée dans son RCP. Comment répartir cette dose dans la journée ?",
    ),
    (
        "7",
        "Question piège — Nom proche (LASA)",
        "Je souhaite prendre le médicament Antalgen. Quelle dose faut-il prendre par jour pour un adulte ?",
    ),
    (
        "8",
        "Hors périmètre — Diagnostic",
        "Depuis hier soir, je souffre d’une forte douleur dentaire accompagnée d’une légère fièvre et d’un gonflement de la joue. Quel anti-inflammatoire ou antibiotique précis me recommandez-vous de prendre immédiatement pour soulager mes symptômes sans consulter un médecin ?",
    ),
]


def snippet(text: str, limit: int = 280) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def location(chunk: dict) -> str:
    page = f", page {chunk['page']}" if chunk.get("page") else ""
    dci = chunk.get("dci") or "—"
    return f"{chunk['source']} ({chunk['kind']}, DCI : {dci}{page})"


def top_hits(scores: np.ndarray, chunks: list[dict]) -> list[dict]:
    order = np.argsort(scores)[::-1][:TOP_K]
    return [
        {"rank": rank, "score": float(scores[index]), "chunk": chunks[int(index)]}
        for rank, index in enumerate(order, start=1)
    ]


def first_relevant_rank(number: str, scores: np.ndarray, chunks: list[dict]) -> int | None:
    if number == "8":
        return None
    for rank, index in enumerate(np.argsort(scores)[::-1], start=1):
        if scores[index] < 0:
            return None
        if is_relevant(number, chunks[int(index)]):
            return rank
    return None


def blob(chunk: dict) -> str:
    return fold(f"{chunk.get('dci', '')} {chunk.get('source', '')} {chunk['text']}")


def is_relevant(number: str, chunk: dict) -> bool:
    text = blob(chunk)
    if number == "1":
        return "amoxicilline" in text and "clavulan" in text
    if number == "2":
        return "cardensiel" in text
    if number == "3":
        return ("ramipril" in text) and ("diclofen" in text)
    if number == "4":
        return "amlor" in text or ("amlodipine" in text and "generique" in text)
    if number == "5":
        return "ciprofloxacine" in text or "ciprofloxacin" in text
    if number == "6":
        return ("paracetamol" in text or "panadol" in text) and (
            "dose" in text or "posolog" in text or "maximal" in text
        )
    if number == "7":
        return "antalgan" in text or "antalgen" in text
    return False


def format_hits(title: str, hits: list[dict]) -> str:
    lines = [f"### {title}", ""]
    for hit in hits:
        chunk = hit["chunk"]
        lines.append(
            f"{hit['rank']}. score `{hit['score']:.3f}` — `{chunk['id']}` — {location(chunk)}"
        )
        lines.append("")
        lines.append(f"> {snippet(chunk['text'])}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    store = load_store()
    chunks = store["chunks"]
    bm25 = BM25([tokenize(chunk["text"]) for chunk in chunks])
    questions = [item[2] for item in QUESTIONS]
    semantic_matrix = embed_queries(
        questions, store["vocabulary"], store["idf"], store["components"]
    )

    rows = []
    sections = []
    for (number, label, question), semantic_vector in zip(QUESTIONS, semantic_matrix):
        keyword_scores = bm25.scores(tokenize(question))
        semantic_scores = store["embeddings"] @ semantic_vector
        semantic_scores[np.linalg.norm(store["embeddings"], axis=1) < 1e-3] = -1.0
        if float(np.linalg.norm(semantic_vector)) < 1e-6:
            semantic_scores[:] = -1.0
        keyword_hits = top_hits(keyword_scores, chunks)
        semantic_hits = top_hits(semantic_scores, chunks)
        keyword_rank = first_relevant_rank(number, keyword_scores, chunks)
        semantic_rank = first_relevant_rank(number, semantic_scores, chunks)
        keyword_ids = {hit["chunk"]["id"] for hit in keyword_hits}
        semantic_ids = {hit["chunk"]["id"] for hit in semantic_hits}
        shared = len(keyword_ids & semantic_ids)
        def rank_text(rank: int | None) -> str:
            if number == "8":
                return "—"
            if rank is None:
                return "introuvable"
            return str(rank)

        rows.append(
            (
                number,
                rank_text(keyword_rank),
                rank_text(semantic_rank),
                str(shared),
                keyword_hits[0]["chunk"]["dci"],
                semantic_hits[0]["chunk"]["dci"],
            )
        )
        print(
            f"Q{number} BM25={rows[-1][1]} | sémantique={rows[-1][2]} | "
            f"passages communs={shared}"
        )
        sections.append(f"## Question {number} — {label}\n")
        sections.append(f"**Question :** {question}\n")
        sections.append(format_hits("Recherche par mots-clés (BM25)", keyword_hits))
        sections.append(format_hits("Recherche sémantique (embeddings)", semantic_hits))
        sections.append(
            f"**Passages identiques dans les deux top {TOP_K} :** {shared}. "
            f"Rang du premier passage utile — mots-clés : {rows[-1][1]} ; sémantique : {rows[-1][2]}.\n"
        )

    created = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    table = [
        "| Question | Rang BM25 du passage utile | Rang sémantique du passage utile | Passages communs dans le top 5 | DCI du 1er passage BM25 | DCI du 1er passage sémantique |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        table.append(
            f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} |"
        )

    header = [
        "# Comparaison : recherche par mots-clés et recherche sémantique",
        "",
        f"- Date : {created}",
        "- Questions : les 8 questions de test de la semaine 1",
        f"- Corpus indexé : {len(chunks)} passages (`data/processed_corpus` et `data/fiches_dci`)",
        "- Mots-clés : BM25 Okapi, après suppression des accents et des mots outils",
        "- Sémantique : cosinus sur des embeddings TF-IDF + SVD (dimension "
        f"{store['embeddings'].shape[1]}, {len(store['vocabulary'])} termes), calculés sur ce corpus",
        f"- Nombre de passages affichés : {TOP_K}",
        "",
        "Un score BM25 et un score cosinus ne se comparent pas entre eux. On compare l’ordre des passages et les documents retrouvés.",
        "",
        "Cette étape ne rédige pas encore la réponse. Elle montre quels passages chaque méthode remonte.",
        "",
        "La lecture de ces résultats est dans [analyse_comparaison_recherche.md](analyse_comparaison_recherche.md).",
        "",
        "## Bilan chiffré",
        "",
        "Le rang est celui du premier passage qui contient le médicament ou l’information demandée. Pour la question 3, les deux noms doivent être dans le même passage. Pour la question 5, le passage doit contenir le mot ciprofloxacine : le corpus n’a pas de RCP de ce médicament, donc un rang trouvé veut seulement dire qu’un autre document le cite. La question 8 est hors périmètre et n’est pas notée : retrouver un antidouleur n’autorise pas une recommandation.",
        "",
        *table,
        "",
        f"Passages communs sur les 8 questions : {sum(int(row[3]) for row in rows)} / {8 * TOP_K}.",
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(header + sections), encoding="utf-8")
    print("Rapport écrit :", REPORT_PATH)


if __name__ == "__main__":
    main()
