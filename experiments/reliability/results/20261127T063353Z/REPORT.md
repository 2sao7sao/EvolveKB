# pass@1 and pass@k

samples per question: 5, temperature: 0.8

| system | pass@1 | pass@2 | pass@3 | pass@5 | pass^1 | pass^3 | pass^5 | mean score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_rag | 0.28 | 0.38 | 0.44 | 0.5 | 0.28 | 0.14 | 0.1 | 1.2 |
| kb_evidence | 0.16 | 0.23 | 0.26 | 0.3 | 0.16 | 0.05 | 0.0 | 0.96 |

pass@k = chance at least one of k samples is fully correct; pass^k = chance all k are.
Per-question passes are in summary.json.
