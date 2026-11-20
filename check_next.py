from pathlib import Path
import json, importlib.util

root = Path(".")
print("=== INSTALLATION ===")
for m in ["pandas", "openpyxl", "pypdf", "dotenv", "langchain",
          "langchain_community", "langchain_groq", "chromadb",
          "sentence_transformers", "groq"]:
    print(f"{m}: {'OK' if importlib.util.find_spec(m) else 'MISSING'}")

print("\n=== METADATA VS FICHES ===")
mp = root / "data/processed/corpus_metadata.json"
records = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else []
fiche_dir = root / "data/fiches_dci"
fiches = {p.stem.casefold() for p in fiche_dir.glob("*.md")}
print("Metadata records:", len(records))
print("Markdown fiches:", len(fiches))
for r in records:
    dci = str(r.get("dci", ""))
    fiche = str(r.get("markdown_file", ""))
    exists = (root / fiche).exists() if fiche else False
    print(f"{dci}: fiche_path_exists={exists}; fiche_name_match={dci.casefold() in fiches}")

print("\n=== REFERENCED PDF PATHS ===")
total = missing = 0
for r in records:
    for prod in r.get("produits", []):
        for path in prod.get("file_paths", []):
            total += 1
            if not (root / path).exists():
                missing += 1
                print("MISSING:", path)
print(f"Referenced PDF paths: {total}; missing: {missing}")

print("\n=== CORPUS FOLDERS ===")
for p in sorted((root / "data/corpus").iterdir()) if (root / "data/corpus").exists() else []:
    if p.is_dir():
        print(p.name, "PDFs:", len(list(p.rglob("*.pdf"))))

print("\n=== PROCESS SCRIPT SAFETY CHECK ===")
code = (root / "process_my_dci.py").read_text(encoding="utf-8-sig")
for i, line in enumerate(code.splitlines(), 1):
    if "rmtree" in line or "generate_corpus_metadata" in line or "EXCEL =" in line:
        print(f"{i}: {line.strip()}")
