import json
import re
from pathlib import Path
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent.parent

CORPUS_DIR = ROOT / "data" / "corpus"
OCR_DIR = ROOT / "data" / "processed_corpus"
OUTPUT_FILE = ROOT / "data" / "processed" / "chunks.jsonl"

MAX_WORDS = 120
OVERLAP_WORDS = 20


def split_text(text):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + MAX_WORDS, len(words))
        morceau = " ".join(words[start:end])

        if morceau.strip():
            chunks.append(morceau)

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


def lire_ocr(pdf_path):
    chemin_relatif = pdf_path.relative_to(CORPUS_DIR)
    fichier_ocr = (OCR_DIR / chemin_relatif).with_suffix(".md")

    if fichier_ocr.is_file():
        return fichier_ocr.read_text(encoding="utf-8").strip()

    return ""


def main():
    if not CORPUS_DIR.is_dir():
        raise FileNotFoundError(f"Dossier corpus introuvable : {CORPUS_DIR}")

    pdf_files = sorted(CORPUS_DIR.rglob("*.pdf"))

    if not pdf_files:
        print("Aucun PDF trouvé dans data/corpus.")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    total_chunks = 0
    pages_vides = 0
    documents_ocr = 0
    documents_non_recuperes = 0

    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        for pdf_path in pdf_files:
            chemin_relatif = pdf_path.relative_to(ROOT).as_posix()
            chemin_corpus = pdf_path.relative_to(CORPUS_DIR)
            parties = chemin_corpus.parts

            dci = parties[0].upper() if parties else "A_VERIFIER"
            brand = parties[1] if len(parties) >= 3 else "A_VERIFIER"

            # ID du document basé sur son chemin complet : évite les collisions.
            document_id = re.sub(
                r"[^A-Za-z0-9]+",
                "_",
                chemin_corpus.with_suffix("").as_posix()
            ).strip("_")

            try:
                reader = PdfReader(str(pdf_path))
                pages = [
                    (numero, page.extract_text() or "")
                    for numero, page in enumerate(reader.pages, start=1)
                ]
            except Exception as erreur:
                print(f"PDF illisible : {chemin_relatif} — {erreur}")
                continue

            numeros_vides = [
                numero for numero, texte in pages if not texte.strip()
            ]
            pages_vides += len(numeros_vides)

            # Si des pages sont vides, on cherche le Markdown OCR du PDF.
            texte_ocr = lire_ocr(pdf_path) if numeros_vides else ""

            if texte_ocr:
                documents_ocr += 1
                blocs = [("OCR — pagination non précisée", texte_ocr)]

            else:
                if numeros_vides:
                    documents_non_recuperes += 1
                    print(
                        f"OCR introuvable : {chemin_relatif} "
                        f"(pages vides : {numeros_vides})"
                    )

                # On garde les pages dont le texte est lisible.
                blocs = [
                    (str(numero), texte)
                    for numero, texte in pages
                    if texte.strip()
                ]

            for page, texte in blocs:
                for numero_chunk, morceau in enumerate(split_text(texte), start=1):
                    record = {
                        "chunk_id": f"{document_id}_{page}_{numero_chunk}",
                        "dci": dci,
                        "brand": brand,
                        "document_type": document_type(pdf_path.name),
                        "file_path": chemin_relatif,
                        "page": page,
                        "text": morceau,
                    }

                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                    total_chunks += 1

            print(f"Traité : {chemin_relatif}")

    print(f"\nPDF trouvés : {len(pdf_files)}")
    print(f"Chunks créés : {total_chunks}")
    print(f"Pages sans texte extrait du PDF : {pages_vides}")
    print(f"Documents récupérés avec l'OCR : {documents_ocr}")
    print(f"Documents avec des pages non récupérées : {documents_non_recuperes}")
    print(f"Fichier créé : {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()