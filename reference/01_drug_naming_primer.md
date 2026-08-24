---
type: reference
updated: 2026-08-23
status: curated
---
# Drug Naming Primer — how to decode pharma drug names

*Learner reference for this knowledge base. Read this once and most drug names become decodable rather than memorizable.*

## Every drug has three names

| Name type | Who assigns it | Example (same molecule!) | When you'll see it |
|---|---|---|---|
| **Code name** | The company, during R&D | LY3298176 | Pipeline discussions, clinical trial press releases, before approval |
| **Generic name (INN)** | WHO (global standard) | tirzepatide | Scientific literature, regulatory filings — never changes, works worldwide |
| **Brand name(s)** | The company's marketers, per market/indication | Mounjaro (diabetes), Zepbound (obesity) | Earnings reports, advertising, prescriptions |

**Key trap: one molecule can carry multiple brand names.** Companies re-brand the same molecule for different indications (separate pricing, marketing, and reimbursement). Sales are reported per brand, so a molecule's true size = sum of its brands.

### Same-molecule, multiple-brands examples (from this KB)

| Generic (the real identity) | Brand #1 | Brand #2 | Why split |
|---|---|---|---|
| tirzepatide (Lilly) | Mounjaro — type 2 diabetes | Zepbound — obesity | Different indications and commercial reporting |
| semaglutide (Novo) | Ozempic — T2D injection | Wegovy — obesity; Rybelsus — oral T2D | Indication + formulation |
| denosumab (Amgen) | Prolia — osteoporosis | Xgeva — cancer bone metastases | Different dose & indication |
| nivolumab (BMS) | Opdivo — IV | Opdivo Qvantig — subcutaneous | Formulation (lifecycle management vs. patent cliff) |
| daratumumab (J&J) | Darzalex — IV | Darzalex Faspro — subcutaneous | Formulation |
| paliperidone (J&J) | Invega Sustenna / Trinza / Hafyera | — | Injection interval (1/3/6 months) |

## The cheat code: generic-name stems

The **suffix (stem) of a generic name tells you the drug's mechanism**. Learn ~20 stems and unfamiliar names parse themselves.

### Biologics & modern modalities

| Stem | Meaning | Examples in this KB |
|---|---|---|
| **-mab** | Monoclonal antibody under the legacy INN scheme; still common among marketed drugs | daratumumab (J&J), denosumab (Amgen), ixekizumab (Lilly) |
| -ximab / -zumab / -umab | Legacy antibody source infixes: chimeric / humanized / fully human | ustekinumab, evolocumab |
| **-tug** | Monospecific, full-length immunoglobulin with an unmodified constant region | New WHO antibody scheme |
| **-bart** | Monospecific, full-length immunoglobulin with an engineered constant region | New WHO antibody scheme |
| **-mig** | Bi- or multispecific immunoglobulin | New WHO antibody scheme |
| **-ment** | Monospecific immunoglobulin-derived fragment or domain | New WHO antibody scheme |
| *two-word names: "mab + -tecan/-tansine"* | **Antibody-drug conjugate (ADC)** — antibody with chemo payload | trastuzumab **deruxtecan** (Enhertu), datopotamab deruxtecan |
| **-cel** | Cell therapy (CAR-T etc.) | lisocabtagene maraleucel = "liso-cel" (Breyanzi, BMS), ciltacabtagene autoleucel = "cilta-cel" (Carvykti, J&J) |
| **-gene … -vec** | Gene therapy (gene + vector) | onasemnogene abeparvovec (Zolgensma, Novartis) |
| **-siran** | siRNA (gene silencing) | inclisiran (Leqvio, Novartis) |
| **-rsen** | Antisense oligonucleotide | nusinersen (Spinraza, Biogen) |
| **-tide** | Peptide | tirzepatide, dulaglutide; **-glutide** = GLP-1 agonist specifically |

### Small molecules — oncology

| Stem | Meaning | Examples |
|---|---|---|
| **-tinib** | Tyrosine kinase inhibitor | ibrutinib (Imbruvica), pirtobrutinib (Jaypirca), lazertinib |
| **-ciclib** | CDK4/6 inhibitor | abemaciclib (Verzenio, Lilly), palbociclib (Ibrance, Pfizer) |
| **-parib** | PARP inhibitor | olaparib (Lynparza, AZ) |
| **-zomib** | Proteasome inhibitor | carfilzomib (Kyprolis, Amgen), bortezomib (Velcade) |
| **-lutamide** | Androgen receptor blocker (prostate) | apalutamide (Erleada, J&J), enzalutamide (Xtandi) |
| **-lidomide** | Immunomodulatory imide (myeloma) | lenalidomide (Revlimid), pomalidomide (Pomalyst) — both BMS |
| **-rafenib / -metinib** | BRAF / MEK inhibitors (melanoma) | dabrafenib / trametinib (Novartis) |

### Small molecules — general medicine

| Stem | Meaning | Examples |
|---|---|---|
| **-citinib** | JAK-family inhibitor (immunology) | baricitinib (Olumiant, Lilly), deucravacitinib (Sotyktu, BMS — technically TYK2) |
| **-gliflozin** | SGLT2 inhibitor (diabetes/heart/kidney) | empagliflozin (Jardiance) |
| **-gliptin** | DPP-4 inhibitor (diabetes) | sitagliptin (Januvia, Merck) |
| **-statin** | Cholesterol (HMG-CoA reductase) | atorvastatin (Lipitor) |
| **-sartan** | Blood pressure (ARB) | valsartan (in Entresto, Novartis) |
| **-prazole** | Acid reflux (PPI) | omeprazole (Prilosec) |
| **-vir** | Antiviral | lenacapavir (Gilead), nirmatrelvir (Paxlovid, Pfizer) |
| **-xaban** | Factor Xa anticoagulant | apixaban (Eliquis, BMS/Pfizer), rivaroxaban (Xarelto, J&J/Bayer) |

## Practical reading rules

1. **Anchor on the generic name; treat brands as aliases.** The KB's drug index (`02_drug_index.md`) maps every brand back to its generic.
2. **Parse the stem first.** "datopotamab deruxtecan" → two words, mab + tecan → an ADC. You now know its modality without ever having seen it.
3. **In earnings reports, expect brands; in trial readouts, expect generics or code names.** MK-3475 = pembrolizumab = Keytruda are the same drug at three life stages.
4. **Biosimilars carry a random 4-letter suffix in the US** (adalimumab-atto, trastuzumab-anns) — the suffix carries no meaning; it just distinguishes copies.
5. **Formulation suffixes** (Faspro, Qvantig, Hytrulo) usually mean "subcutaneous version of an IV drug" — a common patent-cliff defense strategy.

WHO replaced the `-mab` stem for newly named antibodies in 2021. Older `-mab` names will remain dominant in marketed portfolios for years, so both systems matter. Source: [WHO, New INN monoclonal antibody nomenclature scheme](https://www.who.int/publications/i/item/inn-21-531).

---
*Created 2026-08-12 for the pharma-space knowledge base.*
