import json
import re
from pathlib import Path
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "data" / "corpus"
PROCESSED_CORPUS_DIR = ROOT / "data" / "processed_corpus"
OUTPUT_FILE = ROOT / "data" / "processed" / "chunks.jsonl"

MAX_WORDS = 120
OVERLAP_WORDS = 20


def split_text(text):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + MAX_WORDS, len(words))
        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)

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


def read_markdown_pages(markdown_path):
    text = markdown_path.read_text(encoding="utf-8")

    # نبحث عن عناوين الصفحات التي ينشئها ocr_pipeline.py
    page_pattern = re.compile(
        r"^##\s+Page\s+(\d+)\s*$",
        flags=re.IGNORECASE | re.MULTILINE,
    )
    matches = list(page_pattern.finditer(text))

    if not matches:
        return [(1, text.strip())]

    pages = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        page_text = text[start:end].strip()
        pages.append((int(match.group(1)), page_text))

    return pages


def main():
    pdf_files = sorted(CORPUS_DIR.rglob("*.pdf"))

    if not pdf_files:
        print("Aucun fichier PDF trouvé dans data/corpus.")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    total_chunks = 0
    empty_pages = 0

    # نفتح الملف للكتابة من جديد: النتيجة القديمة تتعوض بالنتيجة الجديدة.
    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        for pdf_path in pdf_files:
            relative_path = pdf_path.relative_to(CORPUS_DIR)
            source_pdf_path = pdf_path.relative_to(ROOT).as_posix()

            # نفس المسار داخل processed_corpus، مع تبديل .pdf إلى .md
            markdown_path = (PROCESSED_CORPUS_DIR / relative_path).with_suffix(".md")

            parts = relative_path.parts
            dci = parts[0].upper() if parts else "À vérifier"
            brand = parts[1] if len(parts) >= 3 else "À vérifier"

            pages = []
            text_source = "PDF original"

            # نستعمل Markdown إذا كان موجودًا وفيه نص، وإلا نقرأ PDF.
            if markdown_path.is_file():
                markdown_pages = read_markdown_pages(markdown_path)
                if any(page_text.strip() for _, page_text in markdown_pages):
                    pages = markdown_pages
                    text_source = "processed_corpus"

            if not pages:
                try:
                    reader = PdfReader(str(pdf_path))
                    pages = [
                        (page_number, page.extract_text() or "")
                        for page_number, page in enumerate(reader.pages, start=1)
                    ]
                except Exception as error:
                    print(f"PDF non lisible : {source_pdf_path} — {error}")
                    continue

            for page_number, text in pages:
                if not text.strip():
                    empty_pages += 1
                    print(
                        f"Texte vide : {source_pdf_path}, page {page_number}"
                    )
                    continue

                for chunk_number, chunk_text in enumerate(split_text(text), start=1):
                    chunk_id = (
                        f"{relative_path.with_suffix('').as_posix()}"
                        f"_p{page_number}_c{chunk_number}"
                    ).replace("/", "_").replace("\\", "_")

                    record = {
                        "chunk_id": chunk_id,
                        "dci": dci,
                        "brand": brand,
                        "document_type": document_type(pdf_path.name),
                        "file_path": source_pdf_path,
                        "text_source": text_source,
                        "page": page_number,
                        "text": chunk_text,
                    }

                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                    total_chunks += 1

            print(f"Traité : {source_pdf_path} — texte depuis {text_source}")

    print(f"\nPDF trouvés : {len(pdf_files)}")
    print(f"Chunks créés : {total_chunks}")
    print(f"Pages sans texte extrait : {empty_pages}")
    print(f"Fichier créé : {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()