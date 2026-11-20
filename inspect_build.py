from pathlib import Path
import json, ast, importlib.util

root = Path(".")
print("=== PYTHON FILES ===")
for p in sorted(root.rglob("*.py")):
    if any(x in p.parts for x in ["venv", ".git", "__pycache__"]):
        continue
    print("\n---", p, "---")
    try:
        lines = p.read_text(encoding="utf-8-sig").splitlines()
        for i, line in enumerate(lines[:100], 1):
            print(f"{i}: {line}")
    except Exception as e:
        print("READ ERROR:", e)

print("\n=== METADATA STRUCTURE ===")
p = root / "data/processed/corpus_metadata.json"
try:
    obj = json.loads(p.read_text(encoding="utf-8-sig"))
    print("Type:", type(obj).__name__)
    if isinstance(obj, list) and obj:
        print("First record:", json.dumps(obj[0], ensure_ascii=False, indent=2)[:5000])
    elif isinstance(obj, dict):
        print("Keys:", list(obj.keys()))
        print("Sample:", json.dumps(obj, ensure_ascii=False, indent=2)[:5000])
except Exception as e:
    print("ERROR:", e)

print("\n=== INSTALLED PACKAGES ===")
for name in ["pandas", "openpyxl", "pypdf", "langchain", "langchain_community",
             "langchain_groq", "chromadb", "sentence_transformers", "groq",
             "requests", "python_dotenv"]:
    print(name, bool(importlib.util.find_spec(name)))

print("\n=== SOURCE / DATA FILES ===")
for folder in ["src", "data/processed", "data/fiches_dci", "data/corpus"]:
    p = root / folder
    print("\n", folder)
    if p.exists():
        for f in sorted(p.iterdir()):
            if f.is_file():
                print(f.name, f.stat().st_size, "bytes")
            elif f.is_dir():
                print("[DIR]", f.name)
