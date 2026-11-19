import json
import re
from pathlib import Path
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent.parent

CORPUS_DIR = ROOT / "data" / "corpus"
OUTPUT_FILE = ROOT / "data" / "processed" / "chunks.jsonl"

MAX_WORDS = 120  
OVERLAP_WORDS = 20


def split_text(text):
    
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = min(start + MAX_WORDS, len(words))
        chunk_text = " ".join(words[start:end])

        if chunk_text.strip():
            chunks.append(chunk_text)

        if end == len(words):
            break

        start = end - OVERLAP_WORDS

    return chunks


def document_type(filename):
    name = filename.lower()

    if "rcp" in name:
        return "RCP"
    if "notice" in name:
        return "Notice"
    return "Autre document PDF"


def main():
    if not CORPUS_DIR.is_dir():
        raise FileNotFoundError(f"Dossier corpus introuvable : {CORPUS_DIR}")

    pdf_files = sorted(CORPUS_DIR.rglob("*.pdf"))

    if not pdf_files:
        print("Aucun fichier PDF trouvé dans data/corpus.")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    total_chunks = 0
    empty_pages = 0

    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        for pdf_path in pdf_files:
            relative_path = pdf_path.relative_to(ROOT).as_posix()
            relative_to_corpus = pdf_path.relative_to(CORPUS_DIR)

            # Structure attendue : DCI / nom_commercial / fichier.pdf
            parts = relative_to_corpus.parts
            dci = parts[0].upper() if len(parts) >= 1 else "À vérifier"
            brand = parts[1] if len(parts) >= 3 else "À vérifier"

            try:
                reader = PdfReader(str(pdf_path))
            except Exception as error:
                print(f"PDF non lisible : {relative_path} — {error}")
                continue

            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""

                if not text.strip():
                    empty_pages += 1
                    print(
                        f"Texte vide, OCR peut-être nécessaire : "
                        f"{relative_path}, page {page_number}"
                    )
                    continue

                page_chunks = split_text(text)

                for chunk_number, chunk_text in enumerate(page_chunks, start=1):
                    record = {
                        "chunk_id": (
                            f"{dci}_{brand}_{page_number}_{chunk_number}"
                        ),
                        "dci": dci,
                        "brand": brand,
                        "document_type": document_type(pdf_path.name),
                        "file_path": relative_path,
                        "page": page_number,
                        "text": chunk_text,
                    }

                    output.write(
                        json.dumps(record, ensure_ascii=False) + "\n"
                    )
                    total_chunks += 1

            print(f"Traité : {relative_path}")

    print(f"\nPDF trouvés : {len(pdf_files)}")
    print(f"Chunks créés : {total_chunks}")
    print(f"Pages sans texte extrait : {empty_pages}")
    print(f"Fichier créé : {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()