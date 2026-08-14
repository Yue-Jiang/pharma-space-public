---
type: modality-page
updated: 2026-08-13
status: curated
---
# Modality pages

This tier organises the KB by **technology** rather than by company. It exists because a question the KB was asked on 2026-08-13 — "who plays in CAR-T?" — had no home: the answer was scattered across eight company files, the drug index, the target-convergence table and the graveyard, and no single file assembled it. These pages are that assembly point. Each covers one modality end to end: plain-language mechanism, the strategic and economic logic, marketed assets, the clinical-stage race, what failed and why, competitive dynamics, and a glossary for a newcomer.

**Derived view, not source of truth.** `companies/*.md` remain authoritative for revenue, history and strategy; `reference/02_drug_index.md` for drug identity and status; `reference/05_graveyard.md` for failures. Modality pages restate and cross-reference that material — where they disagree, the company file wins, and the modality page is the thing that needs fixing. Regenerate them when the underlying company files change materially (see AGENTS.md).

## The six pages

| Page | Modality |
|---|---|
| `car-t.md` | Engineered autologous T cells (CD19, BCMA) and the in-vivo pivot |
| `t-cell-engagers.md` | CD3-redirecting bispecific antibodies |
| `adc.md` | Antibody-drug conjugates (ADCs) |
| `radioligand.md` | Radioligand therapy (radiopharmaceuticals) |
| `sirna-antisense.md` | siRNA and antisense oligonucleotides (RNA silencing) |
| `gene-therapy.md` | Gene therapy and gene editing |

All six share the same seven sections (What it is / Why it matters / Marketed assets / The pipeline race / The graveyard / Competitive dynamics / Key terms), so an agent can query any modality with the same structural assumptions.
