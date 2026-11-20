# BM25 Initial Test

Date: 2026-11-20

## Configuration
- Library: rank-bm25
- Documents/chunks indexed: 220
- Sources: TXT and Markdown files
- Chunk size: 1000 characters
- Overlap: 150 characters
- Language: English/French

## Test 1
Question: What are the contraindications of azithromycin?

Observation:
- Correct DCI filtering.
- Scientific article ranked first.
- Regulatory source (RCP) ranked second.
- The desired contraindication section was not retrieved directly.

## Test 2
Question: What are the adverse effects of ceftriaxone?

Observation:
- Correct DCI filtering.
- Scientific article ranked first.
- General information and fiche documents followed.
- The exact adverse-effects section was not retrieved.

## Conclusion
BM25 indexing and retrieval work technically.
However, retrieval relevance is not yet sufficient.
Section-aware chunking and source-type prioritization
should be evaluated before the final comparison with ChromaDB.
