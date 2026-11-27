"""
build_knowledge_graph.py
------------------------
Step 2 of Week 3: Build the medication knowledge graph.

Reads  : data/knowledge_graph/dci_dict.json
Writes : data/knowledge_graph/graph.json      (NetworkX node-link format)
         data/knowledge_graph/graph.graphml   (for Gephi/Cytoscape visualisation)
         data/knowledge_graph/graph_summary.md (human-readable report)

Ontology
--------
Node types:
  - DCI             : active substance (e.g. paracétamol)
  - Medicament      : brand product with dosage/form (e.g. DOLIPRANE 500mg cp)
  - ClasseThera     : therapeutic class (e.g. Antalgiques et anti-inflammatoires)
  - CodeATC         : ATC code node (e.g. N02BE01)

Edge types (relation):
  - EST_GENERIQUE_DE   : Medicament → DCI
  - APPARTIENT_A       : DCI → ClasseThera
  - A_CODE_ATC         : DCI → CodeATC
  - MEME_CLASSE_QUE    : DCI → DCI (same therapeutic class)
  - EQUIVALENT_A       : Medicament → Medicament (same DCI + dosage + form)
"""

import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
DICT_PATH = ROOT / "data" / "knowledge_graph" / "dci_dict.json"
OUT_DIR   = ROOT / "data" / "knowledge_graph"
OUT_JSON  = OUT_DIR / "graph.json"
OUT_GML   = OUT_DIR / "graph.graphml"
OUT_MD    = OUT_DIR / "graph_summary.md"


def main():
    # ── Load dict ─────────────────────────────────────────────────────────────
    if not DICT_PATH.exists():
        raise FileNotFoundError("Run src/build_dci_dict.py first!")
    with open(DICT_PATH, encoding="utf-8") as f:
        dci_dict = json.load(f)

    print(f"[build_graph] Building knowledge graph from {len(dci_dict)} DCI entries...")

    try:
        import networkx as nx
    except ImportError:
        raise SystemExit("NetworkX not installed. Run: pip install networkx")

    G = nx.DiGraph()

    # ── Track classes and ATC for MEME_CLASSE_QUE ──────────────────────────
    classe_to_dcis: dict[str, list[str]] = defaultdict(list)
    atc_prefix_to_dcis: dict[str, list[str]] = defaultdict(list)

    # ── Pass 1: add DCI, ClasseThera, CodeATC nodes + their edges ───────────
    for dci_key, entry in dci_dict.items():
        dci_id    = f"DCI::{dci_key}"
        classe    = entry.get("classe", "")
        atc       = entry.get("atc", "")
        num       = entry.get("numero", 0)

        # --- DCI node ---
        G.add_node(dci_id,
                   type="DCI",
                   label=dci_key,
                   dci_normalized=entry.get("dci_normalized", ""),
                   atc=atc,
                   classe=classe,
                   numero=num,
                   dans_nomenclature=entry.get("dans_nomenclature_algerienne", False),
                   source="Liste_MIPH_2026")

        # --- ClasseThera node + edge ---
        if classe:
            classe_id = f"CLASSE::{classe}"
            if not G.has_node(classe_id):
                G.add_node(classe_id, type="ClasseThera", label=classe)
            G.add_edge(dci_id, classe_id,
                       relation="APPARTIENT_A",
                       source="Liste_MIPH_2026")
            classe_to_dcis[classe].append(dci_id)

        # --- CodeATC node + edge ---
        if atc:
            atc_id = f"ATC::{atc}"
            if not G.has_node(atc_id):
                G.add_node(atc_id, type="CodeATC", label=atc,
                           # ATC hierarchy prefix (first 4 chars = subgroup)
                           prefix_4=atc[:4] if len(atc) >= 4 else atc)
            G.add_edge(dci_id, atc_id,
                       relation="A_CODE_ATC",
                       source="Liste_MIPH_2026")
            # Group by 4-char ATC prefix for MEME_CLASSE_QUE
            if len(atc) >= 4:
                atc_prefix_to_dcis[atc[:4]].append(dci_id)

        # --- Medicament nodes + EST_GENERIQUE_DE edges ---
        seen_meds = {}  # (nom_normalized, forme, dosage) -> med_id
        for gen in entry.get("generiques", []):
            nc    = gen.get("nom_commercial", "").strip()
            forme = gen.get("forme", "").strip()
            dos   = gen.get("dosage", "").strip()
            nc_norm = gen.get("nom_normalized", "")

            if not nc:
                continue

            # Create a unique but stable ID for this brand+form+dosage
            med_key = (nc_norm, forme.lower(), dos.lower())
            if med_key not in seen_meds:
                med_id = f"MED::{nc_norm}::{forme.lower()[:6]}::{dos.lower()[:8]}"
                # Sanitize for graphml
                med_id = med_id.replace(" ", "_").replace("/", "_")
                seen_meds[med_key] = med_id
                G.add_node(med_id,
                           type="Medicament",
                           label=nc,
                           nom_commercial=nc,
                           nom_normalized=nc_norm,
                           forme=forme,
                           dosage=dos,
                           dci=dci_key,
                           dans_nomenclature=gen.get("dans_nomenclature", False),
                           source=gen.get("sources", "Liste_MIPH_2026"))
            else:
                med_id = seen_meds[med_key]

            # Edge: Medicament → DCI
            if not G.has_edge(med_id, dci_id):
                G.add_edge(med_id, dci_id,
                           relation="EST_GENERIQUE_DE",
                           source="Liste_MIPH_2026")

        # --- EQUIVALENT_A: same DCI, same dosage, same form ---
        # Group medicines by (forme, dosage) → they are equivalents
        by_form_dos: dict[tuple, list[str]] = defaultdict(list)
        for key, mid in seen_meds.items():
            _, forme, dos = key
            by_form_dos[(forme, dos)].append(mid)

        for group_meds in by_form_dos.values():
            if len(group_meds) > 1:
                for i, m1 in enumerate(group_meds):
                    for m2 in group_meds[i+1:]:
                        if not G.has_edge(m1, m2):
                            G.add_edge(m1, m2,
                                       relation="EQUIVALENT_A",
                                       source="Liste_MIPH_2026")
                        if not G.has_edge(m2, m1):
                            G.add_edge(m2, m1,
                                       relation="EQUIVALENT_A",
                                       source="Liste_MIPH_2026")

    # ── Pass 2: MEME_CLASSE_QUE edges (DCI in same class) ───────────────────
    for classe, dci_ids in classe_to_dcis.items():
        if len(dci_ids) > 1:
            for i, d1 in enumerate(dci_ids):
                for d2 in dci_ids[i+1:]:
                    if not G.has_edge(d1, d2):
                        G.add_edge(d1, d2,
                                   relation="MEME_CLASSE_QUE",
                                   classe=classe,
                                   source="Liste_MIPH_2026")
                    if not G.has_edge(d2, d1):
                        G.add_edge(d2, d1,
                                   relation="MEME_CLASSE_QUE",
                                   classe=classe,
                                   source="Liste_MIPH_2026")

    # ── Save graph.json ───────────────────────────────────────────────────────
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = nx.node_link_data(G)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[build_graph] ✓ graph.json saved  ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

    # ── Save graph.graphml (for Gephi) ────────────────────────────────────────
    # graphml requires all attribute values to be string/int/float/bool
    H = nx.DiGraph()
    for node_id, attrs in G.nodes(data=True):
        safe = {k: (str(v) if not isinstance(v, (int, float, bool)) else v)
                for k, v in attrs.items()}
        H.add_node(str(node_id), **safe)
    for u, v, attrs in G.edges(data=True):
        safe = {k: (str(v2) if not isinstance(v2, (int, float, bool)) else v2)
                for k, v2 in attrs.items()}
        H.add_edge(str(u), str(v), **safe)
    nx.write_graphml(H, str(OUT_GML))
    print(f"[build_graph] ✓ graph.graphml saved (for Gephi/Cytoscape)")

    # ── Write human-readable summary ──────────────────────────────────────────
    # Count by type
    type_counts = {}
    for _, d in G.nodes(data=True):
        t = d.get("type", "?")
        type_counts[t] = type_counts.get(t, 0) + 1

    rel_counts = {}
    for _, _, d in G.edges(data=True):
        r = d.get("relation", "?")
        rel_counts[r] = rel_counts.get(r, 0) + 1

    # Top DCI by nb generics
    dci_gen_counts = []
    for dci_key, entry in dci_dict.items():
        dci_id = f"DCI::{dci_key}"
        nb = sum(1 for _, _, d in G.in_edges(dci_id, data=True)
                 if d.get("relation") == "EST_GENERIQUE_DE")
        dci_gen_counts.append((dci_key, nb))
    dci_gen_counts.sort(key=lambda x: -x[1])

    md = ["# Knowledge Graph — Summary\n",
          f"**Total nodes**: {G.number_of_nodes()}  |  **Total edges**: {G.number_of_edges()}\n",
          "\n## Node types\n",
          "| Type | Count |",
          "|---|---|"]
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        md.append(f"| {t} | {c} |")

    md += ["\n## Edge types (relations)\n",
           "| Relation | Count |",
           "|---|---|"]
    for r, c in sorted(rel_counts.items(), key=lambda x: -x[1]):
        md.append(f"| {r} | {c} |")

    md += ["\n## Top 10 DCI by number of brand names\n",
           "| DCI | Brand names (generics) |",
           "|---|---|"]
    for dci, nb in dci_gen_counts[:10]:
        md.append(f"| {dci} | {nb} |")

    md += ["\n## Ontology\n",
           "```",
           "NODES:",
           "  DCI          → active substance (paracétamol, amoxicilline...)",
           "  Medicament   → brand product (DOLIPRANE 500mg comprimé)",
           "  ClasseThera  → therapeutic class (Antalgiques, Antibiotiques...)",
           "  CodeATC      → ATC classification code (N02BE01)",
           "",
           "EDGES:",
           "  EST_GENERIQUE_DE  Medicament → DCI",
           "  APPARTIENT_A      DCI        → ClasseThera",
           "  A_CODE_ATC        DCI        → CodeATC",
           "  MEME_CLASSE_QUE   DCI        ↔ DCI  (same class)",
           "  EQUIVALENT_A      Medicament ↔ Medicament  (same DCI+form+dosage)",
           "```"]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"[build_graph] ✓ graph_summary.md saved")
    print(f"\n{'─'*60}")
    print(f"  Nodes  : {G.number_of_nodes()}")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    {t:<15} : {c}")
    print(f"  Edges  : {G.number_of_edges()}")
    for r, c in sorted(rel_counts.items(), key=lambda x: -x[1]):
        print(f"    {r:<25} : {c}")


if __name__ == "__main__":
    main()
