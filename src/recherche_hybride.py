from rag_config import POOL_HYBRIDE, RRF_K


def fusion_rrf(listes: list[list[tuple[int, float]]], poids: list[float] | None = None,
               k_rrf: int = RRF_K, top_k: int = 5) -> list[tuple[int, float]]:
    """Fusionne plusieurs classements [(indice, score), ...] triés du meilleur au moins bon."""
    poids = poids or [1.0] * len(listes)
    scores: dict[int, float] = {}
    for liste, p in zip(listes, poids):
        for rang, (indice, _) in enumerate(liste, start=1):
            scores[indice] = scores.get(indice, 0.0) + p / (k_rrf + rang)
    ordre = sorted(scores, key=lambda i: (-scores[i], i))[:top_k]
    return [(i, scores[i]) for i in ordre]


class RechercheHybride:
    """Même interface que BM25 et RechercheSemantique : search(question, k)."""

    def __init__(self, bm25, semantique, pool: int = POOL_HYBRIDE, k_rrf: int = RRF_K,
                 poids_bm25: float = 1.0, poids_sem: float = 1.0):
        self.bm25, self.semantique = bm25, semantique
        self.pool, self.k_rrf = pool, k_rrf
        self.poids = [poids_bm25, poids_sem]

    def search(self, question: str, k: int, question_sem: str | None = None):
        """question_sem : texte envoyé à la recherche sémantique (par défaut la même question)."""
        r_mots = self.bm25.search(question, self.pool)
        r_sem = self.semantique.search(question_sem or question, self.pool)
        return fusion_rrf([r_mots, r_sem], self.poids, self.k_rrf, k)

    def rangs(self, question: str, indices: list[int], question_sem: str | None = None):
        """Rang de chaque passage dans chaque méthode (pour comprendre une fusion)."""
        r_mots = {i: r for r, (i, _) in enumerate(self.bm25.search(question, self.pool), 1)}
        r_sem = {i: r for r, (i, _) in enumerate(self.semantique.search(question_sem or question, self.pool), 1)}
        return {i: (r_mots.get(i), r_sem.get(i)) for i in indices}
