import sys
from pathlib import Path

import numpy as np
import chromadb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from rag_config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    VECTOR_DB_DIR,
    EMBEDDINGS_FILE,
    charger_chunks,
)

print("Chargement des chunks nettoyés...", flush=True)
chunks = charger_chunks()

print("Chargement des embeddings...", flush=True)
embeddings = np.load(EMBEDDINGS_FILE)

assert len(chunks) == len(embeddings), (
    f"{len(chunks)} chunks mais {len(embeddings)} embeddings. "
    "Vérifie qu'ils viennent de la même expérience."
)
assert len({chunk["chunk_id"] for chunk in chunks}) == len(chunks), (
    "Des identifiants de chunks sont répétés."
)

print(f"{len(chunks)} chunks prêts.", flush=True)
print(f"Dossier de la base : {VECTOR_DB_DIR}", flush=True)

VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))

# Recréer la collection pour éviter de garder d'anciens chunks
try:
    client.delete_collection(COLLECTION_NAME)
except Exception:
    pass

collection = client.create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine", "embedding_model": EMBEDDING_MODEL},
)

for debut in range(0, len(chunks), 25):
    lot = chunks[debut:debut + 25]
    print(f"Ajout du lot {debut + 1} à {debut + len(lot)}...", flush=True)

    collection.add(
        ids=[chunk["chunk_id"] for chunk in lot],
        embeddings=embeddings[debut:debut + len(lot)].tolist(),
        documents=[chunk["text"] for chunk in lot],
        metadatas=[
            {
                "dci": chunk["dci"],
                "produit": chunk["produit"],
                "doc_type": chunk["doc_type"],
                "fichier": chunk["fichier"],
                "page": str(chunk["page"]),
                "section": chunk["section"],
            }
            for chunk in lot
        ],
    )

print(f"Base prête : {collection.count()} vecteurs.", flush=True)
print(f"Base enregistrée dans : {VECTOR_DB_DIR}", flush=True)