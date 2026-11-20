from pathlib import Path
import os, importlib.util, shutil

p = Path("process_my_dci.py")
lines = p.read_text(encoding="utf-8-sig").splitlines()

print("=== PROCESS SCRIPT: REMAINING CODE ===")
for i, line in enumerate(lines[100:], 101):
    print(f"{i}: {line}")

print("\n=== PDF CORPUS ===")
for d in sorted(Path("data/corpus").iterdir()):
    if d.is_dir():
        pdfs = list(d.glob("*.pdf"))
        print(f"{d.name}: {len(pdfs)} PDFs")
        for f in pdfs:
            print(" ", f.name, f.stat().st_size, "bytes")

print("\n=== POPPLER ===")
print("pdftotext:", shutil.which("pdftotext"))
print("pdfinfo:", shutil.which("pdfinfo"))

print("\n=== GROQ KEY ===")
print("GROQ_API_KEY configured:", bool(os.environ.get("GROQ_API_KEY")))

print("\n=== PYTHON PACKAGES ===")
for name in ["pandas", "requests", "chromadb", "sentence_transformers",
             "langchain", "langchain_community", "langchain_groq"]:
    print(name, bool(importlib.util.find_spec(name)))
