"""
ÉTAPE 3 — Comparer recherche par MOTS-CLÉS (BM25) et recherche SÉMANTIQUE (embeddings).

Pour chaque question chargée depuis docs/evaluation/questions_llm.md :
  - top-K par mots-clés (BM25, implémenté ici, sans dépendance)
  - top-K par le sens (ChromaDB + embeddings)
  - hit@K : est-ce qu'au moins un des K résultats vient d'un dossier DCI attendu ?
Sortie : affichage console + docs/evaluation/comparaison_recherche.md

Lancer depuis la racine du projet :
    python src/compare_search.py              # mots-clés + sémantique
    python src/compare_search.py --bm25-only  # mots-clés seulement (ne demande pas chromadb)
    python src/compare_search.py --extra      # ajoute les 7 questions de démonstration
"""
import math
import re
import sys
from collections import Counter

from rag_config import (COLLECTION_NAME, EMBEDDING_MODEL, EVAL_DIR, QUESTIONS_FILE, ROOT, TOP_K,
                        VECTOR_DB_DIR, charger_chunks, normalize, query_prefix, texte_indexe)


def charger_questions(avec_extra: bool = False) -> list[dict]:
    """Lit les questions et les DCI attendues directement depuis le Markdown."""
    if not QUESTIONS_FILE.is_file():
        raise FileNotFoundError(f"Fichier de questions introuvable : {QUESTIONS_FILE}")

    blocs = []
    courant = None
    attendu = None
    for ligne in QUESTIONS_FILE.read_text(encoding="utf-8-sig").splitlines():
        titre = re.match(r"^##\s*(\d+)\s*\.\s*(.+?)\s*$", ligne.strip())
        meta = re.match(r"^<!--\s*attendu:\s*(.*?)\s*-->$", ligne.strip(), re.I)
        if titre:
            courant = {"numero": int(titre.group(1)), "titre": titre.group(2), "lignes": [], "attendu": None}
            blocs.append(courant)
        elif meta and courant is not None:
            valeur = meta.group(1).strip()
            courant["attendu"] = None if valeur.upper() == "ABSENT" else [x.strip() for x in valeur.split(";") if x.strip()]
        elif courant is not None:
            courant["lignes"].append(ligne.strip())

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
                "texte": " ".join(paragraphe),
                "attendu": b["attendu"],
            })

    if avec_extra:
        questions.extend(QUESTIONS_EXTRA)
    return questions


QUESTIONS_EXTRA = [
    {"id": "C1", "type": "Extra — mots communs",
     "texte": "Quelle est la dose maximale journalière de tramadol chez l'adulte ?",
     "attendu": ["tramadol"]},
    {"id": "C2", "type": "Extra — mots communs",
     "texte": "Quelles sont les contre-indications du céfixime ?",
     "attendu": ["céfixime"]},
    {"id": "S1", "type": "Extra — paraphrase",
     "texte": "Quel anti-inflammatoire est déconseillé en cas d'allergie aux sulfamides ?",
     "attendu": ["célécoxib"]},
    {"id": "S2", "type": "Extra — paraphrase",
     "texte": "Puis-je conduire une voiture si je prends un antidouleur ? Risque de m'endormir ?",
     "attendu": ["tramadol", "néfopam", "paracétamol + codéine"]},
    {"id": "S3", "type": "Extra — paraphrase",
     "texte": "Un antalgique opioïde faible peut-il créer une accoutumance chez le patient ?",
     "attendu": ["tramadol", "paracétamol + codéine"]},
    {"id": "S4", "type": "Extra — paraphrase",
     "texte": "Mon enfant a une infection de l'oreille, quel antibiotique de la famille des pénicillines est recommandé ?",
     "attendu": ["amoxicilline"]},
    {"id": "S5", "type": "Extra — paraphrase",
     "texte": "Mal de ventre et selles liquides après la prise de l'antibiotique, est-ce normal ?",
     "attendu": ["amoxicilline", "amoxicilline + acide clavulanique", "céfixime", "céfuroxime"]},
]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

STOPWORDS = set("""
a au aux avec ce ces dans de des du elle en et il ils je la le les leur lui ma mais me mes moi mon
ne nos notre nous on ou par pas pour qu que qui sa se ses si son sur ta te tes toi ton tu un une
vos votre vous est sont etre avoir faut peut peuvent puis dois doit quel quelle quels quelles
comment quand ou ce cette cet ete fait faire sans plus tout tous
""".split())


# ------------------------------------------------------------ recherche par mots-clés (BM25)
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
        q = tokens(question)
        scores = []
        if not self.docs or self.avg == 0:
            return []
        for i, c in enumerate(self.docs):
            s = 0.0
            for t in q:
                f = c.get(t, 0)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
            scores.append(s)
        ordre = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [(i, scores[i]) for i in ordre if scores[i] > 0]


# ------------------------------------------------------------ recherche sémantique
class RechercheSemantique:
    def __init__(self, chunks):
        import chromadb
        from sentence_transformers import SentenceTransformer
        self.index = {c["chunk_id"]: i for i, c in enumerate(chunks)}
        self.modele = SentenceTransformer(EMBEDDING_MODEL)
        self.collection = chromadb.PersistentClient(path=str(VECTOR_DB_DIR)).get_collection(COLLECTION_NAME)

    def search(self, question: str, k: int):
        emb = self.modele.encode([query_prefix() + question], normalize_embeddings=True)

        # ChromaDB peut contenir d'anciens chunks après une modification du corpus.
        # On récupère plus de candidats et on ignore les IDs absents du corpus actuel.
        total = self.collection.count()
        if total == 0:
            return []

        n_demande = min(total, max(k * 5, k))
        res = self.collection.query(query_embeddings=emb.tolist(), n_results=n_demande)

        ids = res.get("ids", [[]])[0]
        distances = res.get("distances", [[]])[0]

        resultats = []
        ids_inconnus = 0
        for cid, dist in zip(ids, distances):
            indice = self.index.get(cid)
            if indice is None:
                ids_inconnus += 1
                continue
            resultats.append((indice, 1 - dist))
            if len(resultats) >= k:
                break

        if ids_inconnus:
            print(
                f"\\n[AVERTISSEMENT] {ids_inconnus} ID(s) ChromaDB ne correspondent "
                "pas aux chunks actuels. Pour une comparaison complète, "
                "reconstruisez la base avec : python src/build_vector_db.py"
            )

        return resultats


# ------------------------------------------------------------ affichage / rapport
def extrait(chunk, n=130):
    return " ".join(chunk["text"].split())[:n].replace("|", "/")


def hit(resultats, chunks, attendu):
    if attendu is None:
        return None
    voulus = {normalize(a) for a in attendu}
    return any(normalize(chunks[i]["dci"]) in voulus for i, _ in resultats)


def symbole(h):
    return "—" if h is None else ("✅" if h else "❌")


def main():
    bm25_seulement = "--bm25-only" in sys.argv
    avec_extra = "--extra" in sys.argv
    try:
        questions = charger_questions(avec_extra=avec_extra)
    except (FileNotFoundError, OSError) as e:
        sys.exit(str(e))
    try:
        chunks = charger_chunks()
    except FileNotFoundError as e:
        sys.exit(str(e))

    mots = BM25([texte_indexe(c) for c in chunks])
    sem = None
    if not bm25_seulement:
        if not VECTOR_DB_DIR.exists():
            sys.exit("Base vectorielle introuvable : lancez d'abord  python src/build_vector_db.py")
        sem = RechercheSemantique(chunks)

    lignes_resume, details = [], []
    for q in questions:
        r_mots = mots.search(q["texte"], TOP_K)
        r_sem = sem.search(q["texte"], TOP_K) if sem else []
        h_mots, h_sem = hit(r_mots, chunks, q["attendu"]), hit(r_sem, chunks, q["attendu"])
        attendu = ", ".join(q["attendu"]) if q["attendu"] else "(absent du corpus)"
        top_mots = f"{r_mots[0][1]:.2f}" if r_mots else "—"
        top_sem = f"{r_sem[0][1]:.2f}" if r_sem else "—"
        lignes_resume.append(f"| {q['id']} | {q['type']} | {attendu} | {symbole(h_mots)} | "
                             f"{symbole(h_sem) if sem else 'n/a'} | {top_mots} | {top_sem if sem else 'n/a'} |")

        bloc = [f"### {q['id']} — {q['type']}", f"**Question :** {q['texte']}", f"**Attendu :** {attendu}", ""]
        for nom, res, score_nom in (("Mots-clés (BM25)", r_mots, "score BM25"),
                                    ("Sémantique (embeddings)", r_sem, "similarité cosinus")):
            if nom.startswith("Sémantique") and not sem:
                continue
            bloc += [f"**{nom}**", "", f"| # | {score_nom} | DCI | produit | doc | page | extrait |", "|---|---|---|---|---|---|---|"]
            if not res:
                bloc.append("| – | – | aucun résultat (aucun mot de la question dans les documents) | | | | |")
            for rang, (i, s) in enumerate(res, 1):
                c = chunks[i]
                bloc.append(f"| {rang} | {s:.3f} | {c['dci']} | {c['produit']} | {c['doc_type']} | {c['page']} | {extrait(c)} |")
            bloc.append("")
        details.append("\n".join(bloc))

        print(f"{q['id']:3s} [{q['type']:12s}] mots-clés {symbole(h_mots)}  sémantique {symbole(h_sem) if sem else 'n/a'}  | attendu : {attendu}")

    # synthèse chiffrée (uniquement les questions dont la réponse est dans le corpus)
    dans = [q for q in questions if q["attendu"]]
    def taux(methode):
        ok = sum(hit(methode(q["texte"], TOP_K), chunks, q["attendu"]) for q in dans)
        return f"{ok}/{len(dans)}"
    synth = [f"- hit@{TOP_K} mots-clés : **{taux(mots.search)}**"]
    if sem:
        synth.append(f"- hit@{TOP_K} sémantique : **{taux(sem.search)}**")
    print("\n" + "\n".join(synth).replace("**", ""))

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    sortie = EVAL_DIR / "comparaison_recherche.md"
    rapport = [
        "# Comparaison : recherche par mots-clés vs recherche sémantique", "",
        f"- Questions évaluées : {len(questions)}" + (" (avec questions extra)" if avec_extra else ""),
        f"- Chunks : {len(chunks)} (build_chunks.py : 120 mots max, chevauchement 20 mots)",
        f"- Mots-clés : BM25 (sans accents, sans mots vides) — Sémantique : `{EMBEDDING_MODEL}` + ChromaDB (cosinus)" if sem
        else "- Mots-clés : BM25 (sans accents, sans mots vides) — recherche sémantique non exécutée dans ce rapport",
        f"- Top-K = {TOP_K}. *hit@K* = au moins un des K résultats vient d'un dossier DCI attendu.", "",
        "## Synthèse", "", *synth, "",
        "| Question | Type | Attendu | Mots-clés | Sémantique | Score top-1 mots-clés | Score top-1 sémantique |",
        "|---|---|---|---|---|---|---|", *lignes_resume, "",
        "> Pour les questions « hors corpus », il n'y a pas de bonne réponse : on regarde si le score "
        "du meilleur résultat est faible (le système doit alors refuser plutôt qu'inventer).", "",
        "## Détail des résultats", "", *details,
    ]
    sortie.write_text("\n".join(rapport), encoding="utf-8")
    print(f"\nRapport écrit : {sortie.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
