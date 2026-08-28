# pharma-space

**A plain-language map of the pharmaceutical industry.** 22 major companies: the drugs they sell, how they got here over 30 years, what they're betting on next, and what they tried that failed. Built to be read, listened to, and queried by an agent.

Started August 2026. Written by a human learner working with two AI agents — one for research and structure, one for a daily news feed. Content is AI-researched from public reporting and machine-checked for internal consistency; it is not primary-source audited.

## Who it's for

Anyone who needs to get oriented in this industry quickly and doesn't have a database subscription: someone starting a job in pharma or biotech, a scientist moving from academia to industry, someone covering the sector, or anyone whose work keeps colliding with drug names they can't decode. It also works as a corpus for an AI agent to answer structural questions about the industry.

The premise is that pharma is hard to enter not because the facts are secret but because they're scattered — and because the vocabulary is designed to be looked up, not learned. So the naming primer comes first, and every company file follows the same shape so the second one is faster to read than the first.

## Who it's not for

- **Not investment advice or due-diligence material.** Figures are approximate, dated, and sometimes estimated. Do not trade on them.
- **Not medical or clinical guidance.** Nothing here informs treatment decisions. Drug indications are listed to explain markets, not to guide care.
- **Not a substitute for primary sources.** Company filings, FDA labels, ClinicalTrials.gov, and commercial databases (Citeline, Evaluate) are authoritative; this is orientation.
- **Not exhaustive.** 22 companies, not the whole industry. Roughly the top ten assets per company, not full portfolios. The failure registry is representative, not a census. Pipeline coverage is thin by design.
- **Not real-time.** Each file carries an `updated:` date in its frontmatter. Check it.

If a number matters to a decision you're making, verify it at the source.

## Four ways to use it

**1. Read it.** Start with [`reference/01_drug_naming_primer.md`](reference/01_drug_naming_primer.md), about 15 minutes and the highest-leverage thing here. Generic drug names are systematic: the suffix tells you what the molecule *is* (`-mab` = a legacy antibody stem, `-tinib` = kinase inhibitor, `-cel` = cell therapy, `-glutide` = GLP-1). Learn the main stems and unfamiliar names stop being noise. Then read the [`Core 22 coverage scope`](reference/00_company_list.md), any file in [`companies/`](companies), and one technology page in [`reference/modalities/`](reference/modalities).

**2. Listen to it.** [`audio/scripts/`](audio/scripts) holds source-current company narrations with tables converted to prose, abbreviations expanded, and numbers written as spoken ("about sixty-five billion dollars"). A script older than its company profile is withheld until regenerated. Pipe one into any text-to-speech tool for an 8–10 minute listen; [`audio/pronunciation.md`](audio/pronunciation.md) is a substitution table so drug names come out right (*ustekinumab* is not obvious on sight). Useful for commutes, and it turns out hearing a drug name is what makes it stick.

**3. Explore the graph.** Open the **[live explorer](https://yue-jiang.github.io/pharma-space-public/)** in a browser, or download [`graph/explorer.html`](graph/explorer.html) to use it offline. It is one self-contained file with no server. The Commercial layer shows marketed and legacy assets, with drug dot size driven by sales. The Bets layer opens with a portfolio-similarity map across twenty validated fields, then lets you drill into one field's active pipeline assets. Company dot size is driven by a validated commitment category. Selecting a company applies the same scale to its indication dots so its relative bets across fields are visible. Click any node for its evidence and context. Space expands the neighbourhood one hop, and shift+space retracts.

**4. Query it with an agent.** Clone the repo and point any coding agent at it: *"who are the main players in obesity?"*, *"which targets have the most failed programs?"*, *"what did Bristol Myers Squibb acquire and when?"*. The prose carries the reasoning; [`graph/nodes.jsonl`](graph/nodes.jsonl) and [`graph/edges.jsonl`](graph/edges.jsonl) carry the structure (one JSON object per line — a few lines of Python is enough to traverse it). Schema in [`graph/README.md`](graph/README.md).

## What's inside

| Path | Contents |
|---|---|
| [`companies/`](companies) | 22 deep dives: marketed assets, 1995–2025 history, current strategic bets, key risks |
| [`reference/`](reference) | Coverage scope · drug naming primer · drug index (758 entries) · target convergence · modality pages · graveyard (130 failure records) |
| [`reference/modalities/`](reference/modalities) | Technology pages: CAR-T, T-cell engagers, ADCs, radioligands, siRNA/ASO, gene therapy |
| [`players/`](players) | 10 one-page profiles of licensors and partners outside the core 22 |
| [`graph/`](graph) | Derived knowledge graph: 1,777 nodes (777 molecules, 423 targets, 353 deals) / 10,094 edges, plus the interactive explorer and a static overview figure |
| [`audio/`](audio) | Source-current narration scripts + pronunciation guide. Scripts older than their company profile are withheld until regenerated. |

Companies are tagged by how much coverage they actually have: **core** (full deep dive), **partner** (one-page profile), **cited** (named by a deal record only — no file, unverified). The explorer renders the three differently so a passing mention is never mistaken for research.

## Accuracy and corrections

Facts were researched from public reporting (company results, regulatory announcements, trade press) and cross-checked; load-bearing numbers — revenues, deal values, approval dates — were verified against multiple sources, while product-level sales are sometimes run-rate estimates and are marked `(est.)`. A validator (`graph/validate.py`) checks the graph for internal contradictions on every rebuild, and the honest gaps it finds are counted rather than hidden.

Expect errors anyway, particularly in product-level figures and patent-expiry years. This is a generated snapshot of a working repository; issues and pull requests here are not monitored. If something is wrong, the `updated:` date and the Sources section of each file tell you what to check.

## Reproducing the derived files

Two scripts ship and run against the published data with no extra inputs:

```bash
python3 graph/validate.py        # correctness checks over the graph
python3 graph/build_overview.py  # regenerate graph/overview.png (needs matplotlib)
```

The extraction pipeline that *builds* the graph from the prose is not included — it depends on cached model outputs that stay in the private working repo.

## License

Content: [CC BY 4.0](LICENSE) — use it, adapt it, attribute it. Sources are cited within each file.


---
*This is a generated public snapshot of a private working repository (content as of 2026-08-27). Issues/PRs here are not monitored by the maintenance pipeline.*
