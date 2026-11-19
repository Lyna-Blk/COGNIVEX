from pathlib import Path
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
import hashlib
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB_DIR = DATA / "vectorstore"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "pharmeazor_v1"

SOURCES = [
    DATA / "PHARMEAZOR_MY_8_DCI",
    DATA / "corpus",
    DATA / "fiches_dci",
]

DCIS = [
    "azithromycine", "ceftriaxone", "ciprofloxacine",
    "clarithromycine", "cotrimoxazole", "doxycycline",
    "levofloxacine", "metronidazole",
]

def normalize(value):
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(c for c in value if not unicodedata.combining(c))
    return value.casefold()

def identify_dci(path):
    parts = [normalize(p) for p in path.parts]
    for dci in DCIS:
        if any(dci in part for part in parts):
            return dci.upper()
    return "NON_SPECIFIE"

def identify_country(path):
    name = normalize(path.name + " " + str(path.parent))
    if "ansm" in name:
        return "France"
    if "emc" in name:
        return "United Kingdom"
    if "anpp" in name or "miph" in name:
        return "Algeria"
    return "Non identifie"

def read_file(path):
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        pages = []
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((number, text))
        return pages

    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    return [(None, text)]

def split_text(text, size=1100, overlap=160):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        piece = text[start:end].strip()
        if len(piece) >= 60:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks

def main():
    files = []
    for folder in SOURCES:
        if folder.exists():
            files.extend(
                p for p in folder.rglob("*")
                if p.is_file() and p.suffix.lower() in {".pdf", ".txt", ".md"}
            )

    seen_hashes = set()
    documents, metadatas, ids = [], [], []
    errors = []
    for path in sorted(files):
        try:
            file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if file_hash in seen_hashes:
                continue
            seen_hashes.add(file_hash)

            pages = read_file(path)
            for page_number, text in pages:
                for index, chunk in enumerate(split_text(text)):
                    doc_id = hashlib.sha256(
                        f"{file_hash}:{page_number}:{index}".encode()
                    ).hexdigest()
                    documents.append(chunk)
                    ids.append(doc_id)
                    metadatas.append({
                        "source": str(path.relative_to(ROOT)),
                        "file_name": path.name,
                        "file_type": path.suffix.lower(),
                        "dci": identify_dci(path),
                        "country": identify_country(path),
                        "page": str(page_number or "N/A"),
                    })
        except Exception as exc:
            errors.append(f"{path}: {exc}")

    if not documents:
        raise RuntimeError(
            "No readable documents found. Check the data folder paths."
        )

    print(f"Files discovered: {len(files)}")
    print(f"Unique files processed: {len(seen_hashes)}")
    print(f"Text chunks created: {len(documents)}")
    print(f"Files with errors: {len(errors)}")

    print("\nLoading multilingual embedding model...")
    model = SentenceTransformer(MODEL_NAME, device="cpu")

    print("Creating local embeddings...")
    embeddings = model.encode(
        documents,
        batch_size=16,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).tolist()

    client = chromadb.PersistentClient(path=str(DB_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    batch_size = 100
    for start in range(0, len(documents), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            embeddings=embeddings[start:end],
        )

    print("\nINDEXING COMPLETE")
    print("ChromaDB location:", DB_DIR)
    print("Indexed chunks:", collection.count())

    if errors:
        print("\nSome files could not be read:")
        for error in errors[:20]:
            print("-", error)

if __name__ == "__main__":
    main()
