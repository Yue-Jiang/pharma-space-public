---
type: reference
updated: 2026-08-13
status: curated
---
# players/ — supporting-cast profiles

This tier holds one-page profiles of companies that are **not** among the KB's 22 covered companies (see `reference/00_company_list.md`) but appear repeatedly in their deals, pipelines and product economics. They are deliberately short: no History section, no era narrative, no audio script.

The tier exists so that partner and licensor entities in `graph/nodes.jsonl` and `graph/cache/deals.json` resolve to something readable instead of an anonymous stub. If an agent traversing the graph lands on "Hansoh Pharma" or "Kelun-Biotech", there should be a page.

**Criteria for adding a profile** — any one is sufficient:

1. The company appears as a counterparty in **two or more** deals involving the covered 22.
2. It **co-owns a marketed asset** with one of the covered 22 (shared economics, not just supply).
3. It is the **origin of a major in-licensed asset** in a covered company's pipeline.

Format: `players/<slug>.md`, frontmatter `type: player-profile`, 250-400 words, fixed section order. Acquired players stay in the tier with a status noting the acquirer.
