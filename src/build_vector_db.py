"""
ÉTAPE 2 — Calculer les embeddings et monter la base vectorielle (ChromaDB).

Entrée  : data/processed/chunks.jsonl   (produit par build_chunks.py)
Sortie  : data/vectordb/                (base ChromaDB persistante, collection "cognivex_chunks")

Lancer depuis la racine du projet :
    python src/build_vector_db.py

Remarque : la 1re exécution télécharge le modèle d'embeddings (~470 Mo) depuis Hugging Face
(internet nécessaire), ensuite il est gardé en cache. La base est reconstruite à chaque
exécution (on supprime l'ancienne collection) => pas de doublons.
"""
import sys
import time

import chromadb
from sentence_transformers import SentenceTransformer

from rag_config import (COLLECTION_NAME, EMBEDDING_MODEL, ROOT, VECTOR_DB_DIR,
                        charger_chunks, passage_prefix, texte_indexe)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BATCH = 64


def main():
    try:
        chunks = charger_chunks()
    except FileNotFoundError as e:
        sys.exit(str(e))
    print(f"{len(chunks)} chunks chargés")

    print(f"Chargement du modèle : {EMBEDDING_MODEL}")
    modele = SentenceTransformer(EMBEDDING_MODEL)

    textes = [passage_prefix() + texte_indexe(c) for c in chunks]
    t0 = time.time()
    # normalize_embeddings=True : vecteurs de norme 1 => distance cosinus correcte
    embeddings = modele.encode(textes, batch_size=BATCH, show_progress_bar=True,
                               normalize_embeddings=True)
    print(f"Embeddings calculés en {time.time() - t0:.0f} s — dimension {embeddings.shape[1]}")

    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # la collection n'existait pas encore
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "embedding_model": EMBEDDING_MODEL},
    )

    for i in range(0, len(chunks), 500):
        lot = chunks[i:i + 500]
        collection.add(
            ids=[c["chunk_id"] for c in lot],
            embeddings=embeddings[i:i + 500].tolist(),
            documents=[c["text"] for c in lot],  # texte brut (pour l'affichage / les citations)
            metadatas=[{
                "dci": c["dci"], "produit": c["produit"], "doc_type": c["doc_type"],
                "fichier": c["fichier"], "page": c["page"], "section": c["section"],
            } for c in lot],
        )

    print(f"\nBase vectorielle prête : {VECTOR_DB_DIR.relative_to(ROOT)}  ({collection.count()} vecteurs)")


if __name__ == "__main__":
    main()
