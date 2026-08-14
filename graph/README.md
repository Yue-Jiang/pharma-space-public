---
type: reference
updated: 2026-08-12
status: generated
---
# graph/ — derived knowledge graph

A structured index over the prose knowledge base. **Derived, never hand-edited**: regenerated from `companies/*.md` + `reference/02_drug_index.md` after curation passes. The prose is the source of truth; if graph and prose disagree, the prose wins and the graph needs regenerating.

## Why it exists (division of labor)

- Prose answers: "tell me about X", "why did X do Y" — narrative, judgment.
- Graph answers: reverse lookups ("everything targeting obesity"), completeness-guaranteed enumerations ("ALL ADCs"), multi-hop chains ("cliffs 2027-2030 with no in-house successor"), aggregations, and **consistency linting** (partnership edges must be derivable from both partners' files; every asset must have index + pronunciation rows).

## Files

| File | One JSON object per line |
|---|---|
| `nodes.jsonl` | `{id, kind, ...}` — kinds: `company`, `molecule`, `target`, `disease_area`, `indication`, `modality`, `deal` |
| `edges.jsonl` | `{src, rel, dst, ...}` — see vocabulary below |

## Node conventions

- `molecule` nodes are canonical (generic/INN name as id, e.g. `tirzepatide`). Brands are a `brands` list attribute — never separate nodes. Attributes: `modality`, `sales_2025_usd_bn` (approx, nullable), `loe_year` (nullable), `phase` (marketed | ph3 | ph2 | ...).
- `company` ids are repo slugs (`eli-lilly`). `indication` ids are lowercase (`obesity`, `nsclc`), each linked to one of ~8 `disease_area` nodes (oncology, immunology, cardiometabolic, neuroscience, vaccines-id, rare, respiratory, other).
- `target` nodes: gene/protein symbol as id (`PD-1`, `GLP-1R`, `KRAS-G12C`); murky MoA -> no edge rather than fake precision.
- `deal` nodes: `{id, kind:"deal", type: acquisition|license|divestiture|partnership, year, value_usd_bn (nullable), notes}`.

## Edge vocabulary

| rel | src → dst | Notes |
|---|---|---|
| `owns` | company → molecule | `from`/`to` years when known; current owner has no `to` |
| `originated` | company → molecule | who discovered/first developed |
| `licensed_to` / `co_develops` / `co_markets` | company → company | `asset:` attribute names the molecule; `geography:` when split (e.g. Xarelto US vs ex-US) |
| `royalty_on` | company → molecule | economic interest without control |
| `treats` | molecule → indication | one edge per indication |
| `in_area` | indication → disease_area | the 2-level hierarchy |
| `has_modality` | molecule → modality | flat controlled vocabulary |
| `acts_on` | molecule → target | `action: agonist\|inhibitor\|...`; ADCs use the antibody antigen; bispecifics get one edge per arm |
| `acquired_via` / `divested_via` | molecule → deal | connects assets to transactions |
| `party_to` | company → deal | acquirer/acquiree/licensor/licensee in `role:` |
| `competes_with` | molecule → molecule | **derived**, same-indication only; `basis: shared_indication` |
| `pressure_on` | any → any | **thesis-type** edges: payer crowding, capacity constraints. MUST carry `source:` and `as_of:` |

**fact vs thesis:** every edge has `etype: fact | derived | thesis`. Agents answering questions should state which tier they used. Thesis edges expire: ignore if `as_of` older than ~6 months.

## Regeneration

`python graph/extract.py` (run from repo root; part of the curation-pass checklist, step 5). Extraction is LLM-assisted for History/Current-bets sections and mechanical for the drug-index table; a run prints a lint report (asymmetric partnerships, index/pronunciation gaps, molecules with no indication).

## Current coverage

16 / 22 companies (batches 1-3). Rebuilt: 2026-08-12.

## Company coverage tiers

Company nodes carry a `tier` field stating how much the KB actually knows about them — so a licensor that appears once is never mistaken for a fully-researched company:

| tier | meaning | source of truth | explorer rendering |
|---|---|---|---|
| `core` | one of the Core 22, full deep dive | `companies/<slug>.md` | large solid blue |
| `partner` | recurring licensor/partner/co-owner with a one-page profile | `players/<slug>.md` | medium light blue |
| `cited` | named only by a deal record or an asset row; **no KB file, details unverified** | none | small hollow outline |

`tier` is derived at rebuild time from which files exist — promoting a company is just adding its file and re-running `extract.py`. A `cited` company accumulating several deal edges is the signal that it deserves a `players/` profile (the lint prints the current list).

## Validation

`python3 graph/validate.py` (`--json`, `--strict`). Checks structural invariants, semantic plausibility (name-stem vs modality, biologic-vs-small-molecule, status-vs-graph-membership, failed-with-sales, ownerless molecules, un-merged target aliases) and reports the size of every catch-all bucket. Catch-alls are treated as first-class findings, not footnotes: the KB's worst failures have all been plausible-looking defaults rather than visible gaps. See AGENTS.md for the level semantics and the curation-pass step.

## Reproducing the visualisations (no LLM)

| file | built by | inputs |
|---|---|---|
| `explorer.html` | `python3 graph/build_explorer.py` | `nodes.jsonl`, `edges.jsonl`, `reference/02_drug_index.md`, `reference/00_company_list.md`, `players/*.md`, `cache/graveyard.json`, `cache/layout.json`, `explorer_template.html` |
| `overview.png` | `python3 graph/build_overview.py` | `nodes.jsonl`, `edges.jsonl` |

Both are **fully deterministic — they make no model calls** and produce byte-identical output on repeated runs. All LLM-derived facts are frozen in `graph/cache/*.json` by `extract.py`; the builders only read them. So the pipeline after any KB edit is:

```
python3 graph/extract.py          # re-derive graph (LLM only if cache misses -> writes cache/TODO.md)
python3 graph/validate.py         # correctness checks; --strict for CI
python3 graph/build_explorer.py   # interactive view
python3 graph/build_overview.py   # static figure
```

**Layout stability:** node positions live in `cache/layout.json` so the picture doesn't reshuffle when the graph grows — new nodes are placed at the centroid of their placed neighbours with a name-hash jitter (deterministic). `build_explorer.py --relayout` recomputes everything with networkx; it moves every node, so use it rarely.

The UI itself (CSS + JS) is `explorer_template.html`, with `__NODES__`/`__EDGES__` placeholders. Edit the template to change interaction or styling; edit `build_explorer.py` to change what data reaches the panels.
