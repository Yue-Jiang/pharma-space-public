---
type: modality-page
updated: 2026-08-13
status: curated
---
# Gene therapy and gene editing

## What it is
Gene therapy treats a disease by changing the genetic instructions inside a patient's cells rather than by dosing a drug repeatedly. There are two delivery routes and they behave like different industries. **In vivo** therapy infuses a modified virus — almost always an **adeno-associated virus (AAV)**, chosen because it is not very pathogenic and different variants (*serotypes*, e.g. AAV9, AAV5, AAVrh74) prefer different tissues — which carries a working copy of a gene into the patient's own cells. **Ex vivo** therapy removes the patient's cells (usually blood stem cells), modifies them in a factory, and gives them back after chemotherapy has cleared space in the bone marrow. Separately, **gene editing** does not add a gene but rewrites the existing one: CRISPR/Cas9 acts as programmable molecular scissors that cut a chosen DNA sequence, and the cell's own repair machinery disables or alters it. Casgevy is ex vivo editing — the "drug" is a batch of the patient's own gene-edited stem cells, manufactured much like a CAR-T product (see the CAR-T modality page), which is why gene editing and cell therapy share supply chains, treatment centres, and conditioning regimens.

## Why it matters
The pitch is a **one-time cure** for a monogenic disease: one infusion, a lifetime of benefit, replacing decades of chronic therapy. That is genuine medicine — five-year HOPE-B data show 94% of Hemgenix patients (51 of 54) still free of routine factor IX prophylaxis with mean factor IX activity of 36.1% — and it is also a commercial structure the pharmaceutical industry is not built for. Revenue arrives as a single **$2–3.5M** payment per patient in a population of a few hundred to a few thousand, from payers who suspect the patient will change insurer long before the savings arrive. Every launch economics problem in this modality follows from that shape: no recurring revenue, tiny patient counts, enormous per-unit price, complex site requirements, and a durability claim that cannot be proven at launch. **The industry's 2024–26 verdict has been to retreat**: multiple approved gene therapies were pulled from the market for commercial reasons, not safety or efficacy.

## Marketed assets
| Asset (generic) | Company | Vector / approach | Indication | Price / sales |
|---|---|---|---|---|
| Zolgensma / Itvisma (onasemnogene abeparvovec) | Novartis | AAV9, in vivo (Itvisma = same vector, intrathecal formulation) | Spinal muscular atrophy | ~$1.2B FY2025 (est.; Q4 $307M). Launched 2019 at ~$2.1M/dose |
| Casgevy (exagamglogene autotemcel, exa-cel) | Vertex w/ CRISPR Therapeutics | Ex vivo CRISPR/Cas9 gene editing | Severe sickle cell disease; transfusion-dependent beta thalassemia | **$2.2M US list**; **$116M FY2025** (60/40 profit share with CRISPR Therapeutics); 301 patient initiations. FDA label extended to ages 2+ |
| Hemgenix (etranacogene dezaparvovec) | CSL Behring (not a covered-22 company) | AAV5, in vivo | Haemophilia B | **$3.5M US list**; >75 individuals treated across eight countries in real-world settings as of Dec 2025 |
| Luxturna (voretigene neparvovec) | Novartis ex-US / Spark (Roche) | AAV2, subretinal | RPE65-mediated inherited retinal dystrophy | The 2017 first-mover; commercially negligible |
| Elevidys (delandistrogene moxeparvovec) | Sarepta (not a covered-22 company) | AAVrh74, in vivo | Duchenne muscular dystrophy | Largest-selling AAV therapy, now carrying a boxed warning (see graveyard) |

**Why the two flagships behave so differently.** Zolgensma works because spinal muscular atrophy is diagnosed in newborns through screening programmes, is otherwise fatal, and has a defined patient flow into specialist centres — a one-time infusion fits that clinical pathway naturally. Casgevy faces the opposite: sickle cell disease is chronic, patients are adults with existing (if imperfect) options, and the treatment requires apheresis, myeloablative chemotherapy, and roughly a **12-month patient journey** from cell collection to engraftment. That is why 301 initiations is genuine progress and $116M is a small number for a "cure" — the bottleneck is the clinical process, not demand or price.

## The pipeline race
| Programme | Company | Approach | Status |
|---|---|---|---|
| Casgevy paediatric expansion | Vertex / CRISPR Therapeutics | Ex vivo CRISPR | FDA label extended to ages 2+ following filings from H1 2026 (priority voucher used) |
| Verve programmes | Eli Lilly (Verve acquisition) | **In vivo** base editing, liver (PCSK9 and related) | Early clinical — the attempt to make editing a one-shot injection instead of a manufacturing process |
| Prevail programmes | Eli Lilly | AAV, neurology | Clinical |
| Kate Therapeutics assets | Novartis (~$1.1B, 2024) | AAV capsid engineering, muscle/CNS delivery | Preclinical — buying vector design, not a drug |
| In vivo CAR-T (Orbital RNA platform) | Bristol Myers Squibb | In vivo cell engineering | Early — see the CAR-T page; the same "skip the factory" logic |
| Poseida assets | Roche | Non-viral / allogeneic cell engineering | Acquired 2025 |
| Salanersen, next-gen SMA | Biogen / Ionis | ASO (not gene therapy) | Included here because it competes directly with Zolgensma for the same patients |

The strategic direction across all of these is the same: **get out of the ex vivo factory and out of the AAV capsid.** Ex vivo therapy is expensive because every dose is a bespoke manufacturing run; AAV is limiting because of immunogenicity (below). Lilly's Verve deal (in vivo base editing of liver genes) and BMS's in vivo CAR-T work are two versions of the same escape.

## The graveyard
**Target-level lessons are almost absent here, which is the point.** The genetics are usually correct — replace SMN1, supply factor IX, disable BCL11A to restore fetal haemoglobin. Nearly every failure in this modality is about **delivery, durability, or commerce**, and that makes it the cleanest illustration in the KB of a modality whose science outran its business model.

**Commercial deaths (approved drugs pulled for lack of demand):**
| Asset | Company | What happened |
|---|---|---|
| Beqvez (fidanacogene elaparvovec) | Pfizer | Stopped selling worldwide, citing weak demand — Pfizer exited haemophilia gene therapy entirely, leaving its gene-therapy cupboard bare |
| Roctavian (valoctocogene roxaparvovec) | BioMarin | Withdrawn from the US market despite approval |
| Zynteglo / Skysona | bluebird bio | The template case: approved therapies commercially unsustainable at gene-therapy prices in small populations; bluebird exited European markets over pricing (est. — not re-verified this session) |

The pattern: haemophilia proved a bad fit because effective prophylactic factor products and non-factor antibodies already exist. A one-time cure competing against a chronic therapy that *works* gives patients and haematologists little reason to accept an irreversible procedure with an unknown durability tail. Contrast Zolgensma, where the alternative was death.

**Safety deaths (the AAV dose problem):**
- **Elevidys (Sarepta)** is the modality's most serious ongoing safety story. Following patient deaths from **acute liver failure**, the FDA investigated its AAVrh74 gene therapies, distribution was halted, and the agency required a **boxed warning for acute serious liver injury and acute liver failure**; an updated prescribing information was subsequently approved. High systemic AAV doses — needed to reach muscle throughout the body — put a very large viral load through the liver.
- **BI 3720931 (Boehringer Ingelheim)**, an inhaled cystic fibrosis gene therapy, was halted in 2026 as part of portfolio pruning — a `strategic` death, and a reminder that large-cap sponsors exit this modality quietly as well as loudly.
- **Zolgensma** itself has a governance scar rather than an efficacy one: a 2019 data-manipulation episode involving pre-submission animal data, plus hepatotoxicity warnings. The drug remains marketed and is **not** withdrawn — a distinction the graveyard registry preserves deliberately.

**The structural constraints behind all of it:**
1. **AAV immunogenicity and no redosing.** Most adults already carry neutralising antibodies to common AAV serotypes from past natural infection, which excludes them from treatment — Hemgenix eligibility requires anti-AAV5 antibody testing, and in HOPE-B 21 of 54 patients (38.9%) had detectable titres before infusion. Worse, the therapy itself provokes an immune response, so **you get one shot**: if expression fades, there is no second dose. Every durability question is therefore permanent.
2. **Ex vivo requires conditioning chemotherapy.** Casgevy and its peers need myeloablation to make room for the edited cells, carrying infertility and secondary-malignancy risk. That is a heavy price for a non-fatal chronic disease and it narrows who consents.
3. **Durability cannot be priced at launch.** Payers are asked for $2–3.5M against a benefit measured in decades, on four- or five-year data. Hemgenix's five-year NEJM publication is exactly the evidence the modality needs, and it arrived three years *after* approval.

## Competitive dynamics
No one leads this modality the way Daiichi Sankyo leads ADCs or Novartis leads radioligands, because no one has found the business model. **Novartis** is the closest to a franchise owner: Zolgensma is the only in vivo gene therapy at blockbuster scale, and the company keeps investing in delivery (Kate Therapeutics for capsid engineering) rather than in more disease programmes — an implicit judgement that the vector, not the gene, is the bottleneck. Its own competition is instructive: Zolgensma's rivals are not other gene therapies but Biogen's ASO Spinraza and Roche's oral risdiplam, both of which are chronic therapies that patients can start, stop, and combine.

**Vertex** is the most credible attacker, and it attacked from an unusual angle — buying nothing, and instead running a decade-long collaboration with CRISPR Therapeutics from 2015 that produced the world's first approved CRISPR medicine (UK authorisation November 2023, US shortly after). Casgevy's slow ramp is a manufacturing-and-pathway problem rather than a scientific one, and the paediatric expansion to ages 2+ addresses the population where the lifetime benefit is largest and the alternative options are worst. The economics are shared 60/40 with CRISPR Therapeutics, so Vertex's upside is capped in the same way Daiichi's ADC upside is.

**Everyone else has been retrenching or rerouting.** Pfizer left haemophilia gene therapy; BioMarin pulled Roctavian in the US; Boehringer Ingelheim killed its inhaled CF programme; Roche's Spark-derived franchise never scaled. The money that used to fund AAV programmes is now funding two adjacent ideas. The first is **in vivo editing** — Lilly's Verve platform aiming to edit liver genes with a single injection and no cell manufacturing, which would collapse both the factory cost and the ex vivo conditioning requirement. The second is **in vivo cell engineering** — BMS's Orbital RNA platform and similar efforts to make CAR-T inside the patient (covered on the CAR-T page), which is the same wager that the industry's real problem was never the genetic payload but the bespoke manufacturing run around it.

Summary for a newcomer: gene therapy has produced several of the most impressive clinical results in modern medicine and one durable commercial success. Every strategic move in the modality since 2024 is an attempt to keep the first fact while fixing the second.

## Key terms
| Term | Meaning |
|---|---|
| AAV (adeno-associated virus) | The standard in vivo delivery vehicle. Not very pathogenic, doesn't usually integrate into the genome, but limited in cargo size and provokes immunity. |
| Serotype / capsid | The AAV variant's protein shell, which determines which tissues it enters. AAV9 → CNS/motor neurons (Zolgensma); AAV5 → liver (Hemgenix); AAVrh74 → muscle (Elevidys). |
| In vivo vs ex vivo | Modify cells inside the body (an infusion) vs remove, modify in a factory, and return them (a manufactured cell product). |
| CRISPR/Cas9 | Programmable DNA-cutting system: a guide RNA specifies the sequence, the Cas9 enzyme cuts, and the cell's repair machinery disables or alters the gene. |
| Base editing | A refinement that chemically converts one DNA letter to another without cutting both strands — the approach in Lilly's Verve programmes. |
| Neutralising antibodies (nAbs) | Pre-existing immunity to a viral vector from past natural infection. Excludes a large fraction of adults from AAV therapy and is why redosing is not possible. |
| Conditioning / myeloablation | Chemotherapy that clears the bone marrow before edited stem cells are returned. Necessary for ex vivo therapy; carries infertility and malignancy risk. |
| Durability | How long the effect lasts. The central unpriced risk: paid for once, delivered over decades, measurable only in retrospect. |
| Outcomes-based agreement | Payment contract in which the manufacturer refunds part of the price if the therapy stops working — the industry's partial answer to durability risk. |
| Monogenic disease | Caused by a defect in a single gene. The only category gene therapy currently addresses well, and the reason patient populations are small. |
