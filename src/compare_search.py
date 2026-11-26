import math
import re
import sys
from collections import Counter

from rag_config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EVAL_DIR,
    QUESTIONS_FILE,
    ROOT,
    TOP_K,
    VECTOR_DB_DIR,
    EXPERIENCE,
    MAX_WORDS,
    OVERLAP_WORDS,
    charger_chunks,
    normalize,
    query_prefix,
    texte_indexe,
) 
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAPPORT_FILE = EVAL_DIR / f"comparaison_recherche_exp{EXPERIENCE}.md"

def charger_questions() -> list[dict]:
   
    if not QUESTIONS_FILE.is_file():
        raise FileNotFoundError(f"Fichier de questions introuvable : {QUESTIONS_FILE}")

    blocs, courant = [], None
    for ligne in QUESTIONS_FILE.read_text(encoding="utf-8-sig").splitlines():
        ligne = ligne.strip()
        titre = re.match(r"^##\s*(\d+)\s*\.\s*(.+?)\s*$", ligne)
        if titre:
            courant = {"numero": int(titre.group(1)), "titre": titre.group(2), "lignes": []}
            blocs.append(courant)
        elif courant is not None and not re.match(r"^<!--.*-->$", ligne):
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
            questions.append({"id": f"Q{b['numero']}", "type": b["titre"], "texte": " ".join(paragraphe)})
    return questions

STOPWORDS = set("""
a au aux avec ce ces dans de des du elle en et il ils je la le les leur lui ma mais me mes moi mon
ne nos notre nous on ou par pas pour qu que qui sa se ses si son sur ta te tes toi ton tu un une
vos votre vous est sont etre avoir faut peut peuvent puis dois doit quel quelle quels quelles
comment quand ou ce cette cet ete fait faire sans plus tout tous
""".split())


def tokens(texte: str) -> list[str]:
    mots = normalize(texte).split()
    # retire les mots vides et le 's' final (pluriel) pour rapprocher "contre-indications"/"contre-indication"
    return [m[:-1] if len(m) > 4 and m.endswith("s") else m for m in mots if m not in STOPWORDS]


class BM25:
    def __init__(self, documents: list[str], k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokens(d)) for d in documents]
        self.len = [sum(c.values()) for c in self.docs]
        self.avg = (sum(self.len) / len(self.len)) if self.len else 0
        df = Counter(t for c in self.docs for t in c)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, question: str, k: int):
        if not self.docs or self.avg == 0:
            return []
        q = tokens(question)
        scores = []
        for i, c in enumerate(self.docs):
            s = 0.0
            for t in q:
                f = c.get(t, 0)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
            scores.append(s)
        ordre = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [(i, scores[i]) for i in ordre if scores[i] > 0]

class RechercheSemantique:
    def __init__(self, chunks):
        import chromadb
        from sentence_transformers import SentenceTransformer
        self.index = {c["chunk_id"]: i for i, c in enumerate(chunks)}
        self.modele = SentenceTransformer(EMBEDDING_MODEL)
        self.collection = chromadb.PersistentClient(path=str(VECTOR_DB_DIR)).get_collection(COLLECTION_NAME)

    def search(self, question: str, k: int):
        emb = self.modele.encode([query_prefix() + question], normalize_embeddings=True)

        total = self.collection.count()
        if total == 0:
            return []
        res = self.collection.query(query_embeddings=emb.tolist(), n_results=min(total, k * 5))

        resultats, inconnus = [], 0
        for cid, dist in zip(res["ids"][0], res["distances"][0]):
            indice = self.index.get(cid)
            if indice is None:
                inconnus += 1
                continue
            resultats.append((indice, 1 - dist))  # distance cosinus -> similarité (1 = identique)
            if len(resultats) >= k:
                break
        if inconnus:
            print(f"\n[AVERTISSEMENT] {inconnus} ID(s) ChromaDB ne correspondent pas aux chunks actuels. "
                  "Reconstruisez la base : python src/build_vector_db.py (ou le notebook).")
        return resultats

def extrait(chunk, n=130):
    return " ".join(chunk["text"].split())[:n].replace("|", "/")


def resume_dci(resultats, chunks):
    """Médicaments (DCI) retrouvés dans le top-K, ex. 'DICLOFENAC ×3, PARACETAMOL ×2'."""
    if not resultats:
        return "aucun résultat"
    compte = Counter(chunks[i]["dci"] for i, _ in resultats)
    return ", ".join(f"{d} ×{n}" for d, n in compte.most_common())


def main():
    bm25_seulement = "--bm25-only" in sys.argv
    try:
        questions = charger_questions()
        chunks = charger_chunks()
    except (FileNotFoundError, ValueError) as e:
        sys.exit(str(e))

    mots = BM25([texte_indexe(c) for c in chunks])
    sem = None
    if not bm25_seulement:
        if not VECTOR_DB_DIR.exists():
            sys.exit("Base vectorielle introuvable : lancez d'abord  python src/build_vector_db.py (ou le notebook)")
        sem = RechercheSemantique(chunks)

    resume, details = [], []
    for q in questions:
        r_mots = mots.search(q["texte"], TOP_K)
        r_sem = sem.search(q["texte"], TOP_K) if sem else []
        communs = len({i for i, _ in r_mots} & {i for i, _ in r_sem}) if sem else None
        top_mots = f"{r_mots[0][1]:.2f}" if r_mots else "—"
        top_sem = f"{r_sem[0][1]:.2f}" if r_sem else "—"

        resume.append(f"| {q['id']} | {q['type']} | {resume_dci(r_mots, chunks)} | "
                      f"{resume_dci(r_sem, chunks) if sem else 'n/a'} | "
                      f"{f'{communs}/{TOP_K}' if sem else 'n/a'} | {top_mots} | {top_sem if sem else 'n/a'} |")

        bloc = [f"### {q['id']} — {q['type']}", f"**Question :** {q['texte']}", ""]
        for nom, res, score_nom in (("Mots-clés (BM25)", r_mots, "score BM25"),
                                    ("Sémantique (embeddings)", r_sem, "similarité cosinus")):
            if nom.startswith("Sémantique") and not sem:
                continue
            bloc += [f"**{nom}**", "", f"| # | {score_nom} | DCI | produit | doc | page | extrait |",
                     "|---|---|---|---|---|---|---|"]
            if not res:
                bloc.append("| – | – | aucun résultat (aucun mot de la question dans les documents) | | | | |")
            for rang, (i, s) in enumerate(res, 1):
                c = chunks[i]
                bloc.append(f"| {rang} | {s:.3f} | {c['dci']} | {c['produit']} | {c['doc_type']} | {c['page']} | {extrait(c)} |")
            bloc.append("")
        details.append("\n".join(bloc))

        print(f"\n{q['id']} — {q['type']}")
        print(f"   mots-clés  : {resume_dci(r_mots, chunks)}")
        if sem:
            print(f"   sémantique : {resume_dci(r_sem, chunks)}   (chunks communs : {communs}/{TOP_K})")

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    rapport = [
        "# Comparaison : recherche par mots-clés vs recherche sémantique", "",
        f"- Questions : {len(questions)} (docs/evaluation/questions_llm.md)",
        f"- Expérience : {EXPERIENCE}",
f"- Chunks chargés : {len(chunks)}",
f"- Découpage : {MAX_WORDS} mots max, chevauchement de {OVERLAP_WORDS} mots",
        f"- Mots-clés : BM25 (sans accents, sans mots vides) — Sémantique : `{EMBEDDING_MODEL}` + ChromaDB (cosinus)" if sem
        else "- Mots-clés : BM25 (sans accents, sans mots vides) — recherche sémantique non exécutée dans ce rapport",
        f"- Top-K = {TOP_K} résultats par méthode. Aucune réponse de référence : on compare les extraits retrouvés.", "",
        "## Synthèse", "",
        "| Question | Type | DCI retrouvées (mots-clés) | DCI retrouvées (sens) | Chunks communs | Score top-1 mots-clés | Score top-1 sens |",
        "|---|---|---|---|---|---|---|", *resume, "",
        "> Les scores ne sont pas comparables entre les deux méthodes (BM25 n'est pas borné, le cosinus va de 0 à 1) "
        "et un score élevé ne prouve pas que la réponse est dans le corpus : pour juger, lire les extraits "
        "dans le détail ci-dessous.", "",
        "## Détail des résultats", "", *details,
    ]
    RAPPORT_FILE.write_text("\n".join(rapport), encoding="utf-8")
    print(f"\nRapport écrit : {RAPPORT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
