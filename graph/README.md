# graph/ — the knowledge graph

A structured index over the prose knowledge base, derived from `companies/*.md` and `reference/*.md`. **The prose is the source of truth**; if graph and prose disagree, the prose wins. Nothing here is hand-edited.

## Files

| File | What it is |
|---|---|
| `nodes.jsonl` | one JSON object per line, one line per node |
| `edges.jsonl` | one JSON object per line, one line per edge |
| `explorer.html` | self-contained interactive view — open in any browser, works offline |
| `overview.png` | static figure: companies against the most crowded targets |
| `validate.py` | correctness checks (`--json`, `--strict`) |
| `build_overview.py` | regenerates `overview.png` from the jsonl (needs matplotlib) |

## Node kinds

| kind | key fields |
|---|---|
| `company` | `tier` — `core` (deep dive in `companies/`), `partner` (profile in `players/`), `cited` (named by a deal record only; no file, unverified) |
| `molecule` | `brands`, `class`, `modality`, `sales_2025_usd_bn`, `loe_year` (patent expiry), `phase` (`failed` for graveyard entries) |
| `target` | the molecular target; id is a canonical symbol |
| `indication` | disease treated |
| `disease_area` | coarse grouping of indications |
| `modality` | drug format (`mab`, `adc`, `small-molecule`, `cell-therapy`, …) |
| `deal` | `type`, `year`, `value_usd_bn`, `counterparty`, `assets` |

## Edge relations

| rel | meaning |
|---|---|
| `owns` | company → molecule it markets |
| `acts_on` | molecule → target (`action`: inhibitor, agonist, …) |
| `treats` | molecule → indication |
| `failed_on` | dead molecule → target it failed against (`year`, `mode`) |
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
owns = defaultdict(list)
for e in edges:
    if e["rel"] == "owns":
        owns[e["dst"]].append(e["src"])
for e in edges:
    if e["rel"] == "acts_on" and e["dst"] == "GLP-1R":
        print(e["src"], "->", owns.get(e["src"]))
```

`competes_with` dominates the edge count (~2,100 of 4,795) because it is combinatorial within an indication; filter it out for most traversals.

## Caveats

- **Marketed-asset bias.** The graph covers what companies sell today plus the failure registry. Pipeline assets named in prose mostly have no nodes yet.
- **Sales figures** are approximate, sometimes run-rate estimates, and FX-converted for non-USD reporters.
- **Coverage tiers matter.** A `cited` company node carries no verified information beyond its name.
- Run `python3 graph/validate.py` to see the current gap counts — molecules without a target, indications that fell into the `other` bucket, and so on. They are counted rather than papered over.
