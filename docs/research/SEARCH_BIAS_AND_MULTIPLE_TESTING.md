# Search bias and multiple testing

The number of expressions generated is part of the evidence.

- `tested_count` is written on the ledger row.
- Omitting the search-space size is `search_space_omission` FAIL.
- Hiding losers is `hidden_candidate` FAIL.
- Family p-values are corrected with the existing BH/Bonferroni/Holm engine. Discovery does not implement a second FDR.
- Null labels must not systematically manufacture a `RESEARCH_CANDIDATE` on synthetic data.
