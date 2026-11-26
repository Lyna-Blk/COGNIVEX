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
    passage_prefix,
    texte_indexe,
)

print("Chargement des chunks nettoyés...", flush=True)
chunks = charger_chunks()

def calculer_embeddings():
    from sentence_transformers import SentenceTransformer
    print(f"Calcul des embeddings avec {EMBEDDING_MODEL} (plusieurs minutes sur CPU)...", flush=True)
    modele = SentenceTransformer(EMBEDDING_MODEL)
    textes = [passage_prefix() + texte_indexe(chunk) for chunk in chunks]
    vecteurs = modele.encode(textes, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
    EMBEDDINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_FILE, vecteurs)
    return vecteurs


if "--recalculer" in sys.argv or not EMBEDDINGS_FILE.is_file():
    embeddings = calculer_embeddings()
else:
    print("Chargement des embeddings...", flush=True)
    embeddings = np.load(EMBEDDINGS_FILE)
    if len(embeddings) != len(chunks):
        print(f"{len(embeddings)} embeddings pour {len(chunks)} chunks : ils sont périmés.", flush=True)
        embeddings = calculer_embeddings()

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

try:
    client.delete_collection(COLLECTION_NAME)
except Exception:
    pass

collection = client.create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine", "embedding_model": EMBEDDING_MODEL},
)

for debut in range(0, len(chunks), 100):
    lot = chunks[debut:debut + 100]
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
