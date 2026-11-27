"""
Découpe le corpus nettoyé, calcule les embeddings et enregistre la base vectorielle.

Sources indexées :
- data/processed_corpus/**/*.md
- data/fiches_dci/*.md

Sortie : data/processed/vector_store/

Lancer depuis la racine du projet :
    .\\.venv\\Scripts\\python.exe src\\build_vector_store.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from retrieval import build_chunks, fit_embeddings, save_store, STORE_DIR


def main() -> None:
    chunks = build_chunks()
    if not chunks:
        raise SystemExit("Aucun document .md à indexer.")
    print(f"{len(chunks)} passages. Calcul des embeddings...")
    model = fit_embeddings([chunk["text"] for chunk in chunks])
    save_store(chunks, model)
    print(
        f"Base vectorielle écrite dans {STORE_DIR} "
        f"({len(chunks)} passages, dimension {model['dimension']}, "
        f"{len(model['vocabulary'])} termes)."
    )


if __name__ == "__main__":
    main()
