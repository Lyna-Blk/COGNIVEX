from pathlib import Path
import shutil

p = Path("process_my_dci.py")
backup = Path("process_my_dci.py.before_rag.bak")
if not backup.exists():
    shutil.copy2(p, backup)

code = p.read_text(encoding="utf-8-sig")
old = 'EXCEL = DATA / "Liste 40 medicaments.xlsx"'
new = 'EXCEL = DATA / "liste_40_medicament_complete.xlsx"'

if old in code:
    code = code.replace(old, new)
    p.write_text(code, encoding="utf-8")
    print("Excel path fixed.")
elif new in code:
    print("Excel path already fixed.")
else:
    print("WARNING: Excel path not found; no change made.")

requirements = """requests
pandas
openpyxl
pypdf
python-dotenv
langchain
langchain-community
langchain-groq
chromadb
sentence-transformers
"""
Path("requirements.txt").write_text(requirements, encoding="utf-8")
print("requirements.txt updated.")

print("\n=== GENERATOR REMAINING CODE ===")
g = Path("generate_corpus_metadata.py").read_text(encoding="utf-8-sig").splitlines()
for i, line in enumerate(g[100:], 101):
    print(f"{i}: {line}")
