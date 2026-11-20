from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
DB_DIR = ROOT / "data" / "vectorstore"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

model = SentenceTransformer(MODEL_NAME, device="cpu")
client = chromadb.PersistentClient(path=str(DB_DIR))
collection = client.get_collection("pharmeazor_v1")

questions = [
    ("What are the contraindications of azithromycin?", "AZITHROMYCINE"),
    ("What are the adverse effects of ceftriaxone?", "CEFTRIAXONE"),
]

for question, dci in questions:
    print("\n" + "=" * 70)
    print("QUESTION:", question)
    print("DCI FILTER:", dci)

    embedding = model.encode(
        [question],
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=embedding,
        n_results=5,
        where={"dci": dci}
    )

    for i, (document, metadata, distance) in enumerate(
        zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ),
        1
    ):
        print(f"\n--- Result {i} | Distance: {distance:.4f} ---")
        print("Source:", metadata.get("source"))
        print("DCI:", metadata.get("dci"))
        print("Page:", metadata.get("page"))
        print(document[:900])
