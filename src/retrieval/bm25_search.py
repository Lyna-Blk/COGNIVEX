from pathlib import Path
import re
import unicodedata
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[2]

SOURCES = [
    ROOT / "data" / "PHARMEAZOR_MY_8_DCI",
    ROOT / "data" / "corpus",
    ROOT / "data" / "fiches_dci",
]

DCIS = {
    "azithromycin": "azithromycine",
    "azithromycine": "azithromycine",
    "ceftriaxone": "ceftriaxone",
    "ciprofloxacin": "ciprofloxacine",
    "ciprofloxacine": "ciprofloxacine",
    "clarithromycin": "clarithromycine",
    "clarithromycine": "clarithromycine",
    "cotrimoxazole": "cotrimoxazole",
    "doxycycline": "doxycycline",
    "levofloxacin": "levofloxacine",
    "levofloxacine": "levofloxacine",
    "metronidazole": "metronidazole",
}

TRANSLATIONS = {
    "contraindications": "contre indications",
    "adverse effects": "effets indesirables",
    "side effects": "effets indesirables",
    "precautions": "mises en garde precautions",
    "dosage": "posologie",
    "interactions": "interactions medicamenteuses",
}

def normalize(text):
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.findall(r"\b[\w-]+\b", text)

def prepare_query(query):
    expanded = query.lower()
    for english, french in TRANSLATIONS.items():
        if english in expanded:
            expanded += " " + french
    return expanded

def split_text(text, size=1000, overlap=150):
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()
        if len(chunk) >= 80:
            chunks.append(chunk)

        if end >= len(text):
            break
        start = end - overlap

    return chunks

def identify_dci(path):
    name = unicodedata.normalize(
        "NFKD", str(path).casefold()
    )
    name = "".join(c for c in name if not unicodedata.combining(c))

    for dci in set(DCIS.values()):
        if dci in name:
            return dci
    return None

def load_documents():
    documents = []

    for folder in SOURCES:
        if not folder.exists():
            continue

        for path in folder.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".txt", ".md"}:
                continue

            try:
                content = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                content = path.read_text(
                    encoding="cp1252", errors="replace"
                )

            dci = identify_dci(path)

            for number, chunk in enumerate(split_text(content)):
                documents.append({
                    "source": str(path.relative_to(ROOT)),
                    "dci": dci,
                    "chunk": number + 1,
                    "text": chunk,
                })

    return documents

def main():
    documents = load_documents()

    if not documents:
        raise RuntimeError("No documents found.")

    tokenized = [normalize(doc["text"]) for doc in documents]
    index = BM25Okapi(tokenized)

    print(f"BM25 READY | Chunks indexed: {len(documents)}")
    print("Enter a question (or type exit).")

    while True:
        query = input("\nQuestion: ").strip()

        if query.lower() in {"exit", "quit"}:
            break
        if not query:
            continue

        query_lower = query.casefold()
        target_dci = None

        for name, dci in DCIS.items():
            if re.search(r"\b" + re.escape(name) + r"\b", query_lower):
                target_dci = dci
                break

        prepared = prepare_query(query)
        scores = index.get_scores(normalize(prepared))

        ranked = sorted(
            enumerate(scores),
            key=lambda item: item[1],
            reverse=True
        )

        results = []
        for i, score in ranked:
            doc = documents[i]

            if target_dci and doc["dci"] != target_dci:
                continue

            if score > 0:
                results.append((doc, score))

            if len(results) == 5:
                break

        if not results:
            print("No relevant results found.")
            continue

        for rank, (doc, score) in enumerate(results, 1):
            print(f"\n--- Result {rank} | Score: {score:.4f} ---")
            print("DCI:", doc["dci"] or "Not identified")
            print("Source:", doc["source"])
            print("Chunk:", doc["chunk"])
            print(doc["text"][:900])

if __name__ == "__main__":
    main()