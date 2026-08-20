# graph/ — the knowledge graph

A structured index over the prose knowledge base, derived from `companies/*.md` and `reference/*.md`. **The prose is the source of truth**; if graph and prose disagree, the prose wins. Nothing here is hand-edited.

## Files

| File | What it is |
|---|---|
| `nodes.jsonl` | one JSON object per line, one line per node |
| `edges.jsonl` | one JSON object per line, one line per edge |
| `claims.jsonl` | source-backed structured claims for factual treatment and prevention edges |
| `schema/indications.json` | exact indication concepts, aliases, parents, and disease areas |
| `explorer.html` | self-contained interactive view — open in any browser, works offline |
| `overview.png` | static figure: companies against the most crowded targets |
| `validate.py` | standalone correctness checks over the published artifacts (`--json`, `--strict`) |
| `build_overview.py` | regenerates `overview.png` from the jsonl (needs matplotlib) |

## Node kinds

| kind | key fields |
|---|---|
| `company` | `tier` — `core` (deep dive in `companies/`), `partner` (profile in `players/`), `cited` (named by a deal record only; no file, unverified) |
| `molecule` | `brands`, `class`, `modality`, `sales_2025_usd_bn`, `loe_year` (patent expiry), `phase` (`marketed | legacy | pipeline | failed`) |
| `target` | the molecular target; id is a canonical symbol |
| `indication` | disease treated |
| `disease_area` | coarse grouping of indications |
| `modality` | drug format (`mab`, `adc`, `small-molecule`, `cell-therapy`, …) |
| `deal` | `type`, `year` (announcement year), `announced_year`, `closed_year`, `announcement_source`, `value_usd_bn`, `counterparty`, `assets` |

Modality records what the medicine is, not the protein or pathway it targets. The private build pipeline checks explicit source format independently from classifier output before these generated files are published.

## Edge relations

| rel | meaning |
|---|---|
| `portfolio_includes` | company → molecule associated with its portfolio; not a legal-ownership claim |
| `acquired_asset` / `divested_asset` | company → molecule, backed by a linked deal |
| `inherited_asset` | successor company → molecule inherited through a merger |
| `licensed_asset` / `licensed_out` / `partnered_on` | company → molecule, backed by a linked deal |
| `failed_on` | molecule → target, qualified as program death, indication/regional failure, trial setback, or launch failure; target checked against curated mechanism edges when available |
| `acts_on` | molecule → target (`action`: inhibitor, agonist, …) |
| `treats` | molecule → exact indication (`claim_id` links to source evidence) |
| `prevents` | molecule → indication prevented or prophylactically covered |
| `studied_for` | pipeline molecule → indication under investigation (`intended_use` preserves treatment/prevention intent) |
| `subtype_of` | specific indication → broader indication |
| `failed_on` | molecule → target with a failed program (`scope`, `failed_indication`, `year`, `mode`) |
| `has_modality` | molecule → modality |
| `in_area` | indication → disease area |
| `party_to` | company → deal (`role`) |
| `acquired_via` / `via` | molecule → the deal that moved it |
| `competes_with` | molecule ↔ molecule, derived from a shared indication (`basis`) — the only inferred relation; `etype` is `derived`, everything else is `fact` |

## Querying it

```python
import json
from collections import defaultdict

nodes = {n["id"]: n for n in map(json.loads, open("graph/nodes.jsonl"))}
edges = [json.loads(l) for l in open("graph/edges.jsonl")]

# who has marketed assets against GLP-1R?
portfolio = defaultdict(list)
for e in edges:
    if e["rel"] == "portfolio_includes":
        portfolio[e["dst"]].append(e["src"])
for e in edges:
    if e["rel"] == "acts_on" and e["dst"] == "GLP-1R":
        print(e["src"], "->", portfolio.get(e["src"]))
```

`competes_with` dominates the edge count (5,862 of 10,094) because it is combinatorial within an indication; filter it out for most traversals.

## Explorer layers

The explorer opens in **Commercial**, a less crowded company and product view containing only marketed and legacy assets. Drug dot size reflects approximate 2025 sales.

Switch to **Bets** to start with an all-fields portfolio overview, then select one field to see its active pipeline assets. In the overview, proximity reflects weighted overlap across company portfolios and the companies backing each field. Company dot size is categorical: leader, challenger, material, or exploratory, using the strongest visible commitment when multiple fields are shown. Companies in the same category have exactly the same size because the public evidence supports broad tiers, not a precise rank within a tier. Click a company to inspect the active assets, registered work, graph coverage, and separately disclosed capital context behind its category.

Targets, modalities, indications, and disease areas use the same underlying graph. They can be added with the node controls without changing the asset layer.

Commercial and single-field Bets views use one blended relationship layout. Each selected type adds its own relationship forces, so company, modality, indication, and target structure can influence the graph together. The all-fields Bets overview instead uses weighted portfolio similarity across companies and fields. Degree normalization prevents highly connected hubs from pulling everything into one cluster. Fixed starting geometry and cached filter combinations keep the result stable between visits. An optional advanced spacing control adjusts density without changing the underlying evidence.

## Caveats

- **Pipeline coverage is substantial but incomplete.** Pipeline nodes use `studied_for`, never an established treatment claim. Run validation to see assets still present in prose but absent from the graph.
- **Sales figures** are approximate, sometimes run-rate estimates, and FX-converted for non-USD reporters.
- **Coverage tiers matter.** A `cited` company node carries no verified information beyond its name.
- **Indication rollups.** Exact concepts are matched before generic patterns. Broad concepts such as IBD are available through `subtype_of`, not substituted for ulcerative colitis or Crohn disease.
- Run `python3 graph/validate.py` to see the current gap counts, including molecules without a target and indications that fell into the `other` bucket. They are counted rather than papered over. Private builds additionally compare published assertions with source-extraction caches; those caches are intentionally absent from this mirror.
