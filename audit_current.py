from pathlib import Path
import json, re, hashlib, subprocess

root = Path(".")
data = root / "data"
base = data / "PHARMEAZOR_MY_8_DCI"
out = data / "audit_current_state.txt"
lines = []

def add(x=""):
    lines.append(str(x))

add("COGNIVEX - CURRENT STATE AUDIT")
add("=" * 55)

# Git
try:
    r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
    add("\nGIT STATUS")
    add(r.stdout.strip() or "Clean working tree")
except Exception as e:
    add(f"Git error: {e}")

# Metadata
add("\nMETADATA")
p = data / "processed" / "corpus_metadata.json"
if p.exists():
    try:
        obj = json.loads(p.read_text(encoding="utf-8-sig"))
        add(f"Records: {len(obj) if isinstance(obj, list) else 'not a list'}")
        if isinstance(obj, list):
            add("DCIs: " + ", ".join(str(x.get("dci", x.get("DCI", "?"))) for x in obj))
    except Exception as e:
        add(f"JSON ERROR: {e}")
else:
    add("MISSING")

# Articles
add("\nARTICLES")
hashes = {}
if base.exists():
    for d in sorted(x for x in base.iterdir() if x.is_dir()):
        files = list((d / "ARTICLE").glob("*.txt")) if (d / "ARTICLE").exists() else []
        if not files:
            add(f"MISSING ARTICLE: {d.name}")
            continue
        f = files[0]
        raw = f.read_bytes()
        text = raw.decode("utf-8-sig", errors="replace")
        digest = hashlib.sha256(raw).hexdigest()
        duplicate = hashes.get(digest)
        hashes[digest] = d.name
        question_lines = [
            i for i, line in enumerate(text.splitlines(), 1)
            if re.search(r"[A-Za-zÀ-ÿ]\?[A-Za-zÀ-ÿ]", line)
        ]
        add(f"\n{d.name}: {len(raw)} bytes")
        add(f"  First line: {text.splitlines()[0][:150] if text.splitlines() else 'EMPTY'}")
        add(f"  Replacement characters: {text.count(chr(65533))}")
        add(f"  Suspicious question-mark lines: {len(question_lines)}")
        add(f"  Duplicate article: {duplicate or 'No'}")
        add(f"  Sections: {sum(1 for x in text.splitlines() if x.strip().startswith('#'))}")
        add(f"  Read error markers: {text.count(chr(65533))}")

# Script configuration
add("\nPROCESS SCRIPT")
p = root / "process_my_dci.py"
if p.exists():
    t = p.read_text(encoding="utf-8-sig", errors="replace")
    for i, line in enumerate(t.splitlines(), 1):
        if "EXCEL" in line or "Liste 40 medicaments" in line or "liste_40_medicament" in line:
            add(f"Line {i}: {line.strip()}")

add("\nREQUIREMENTS")
p = root / "requirements.txt"
add(p.read_text(encoding="utf-8-sig", errors="replace") if p.exists() else "MISSING")

# Products, PDFs and source files
add("\nFILE COUNTS")
for folder in sorted(x for x in base.iterdir() if x.is_dir()) if base.exists() else []:
    add(
        f"{folder.name}: "
        f"products={len(list((folder/'Produit').glob('*.txt'))) if (folder/'Produit').exists() else 0}, "
        f"PDFs={len(list((folder/'RCP_et_notice').glob('*.pdf'))) if (folder/'RCP_et_notice').exists() else 0}, "
        f"SOURCE={'yes' if (folder/'SOURCE.txt').exists() and (folder/'SOURCE.txt').stat().st_size else 'missing/empty'}"
    )

out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
print(f"\nREPORT SAVED: {out}")
