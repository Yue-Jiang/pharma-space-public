---
type: reference
updated: 2026-08-13
status: curated
---
# The graveyard — clinical-stage failures registry

*The survivorship correction for this knowledge base. Everything else in the KB describes winners; this file records the drugs that reached the clinic and died. A crowded target with many corpses (amyloid) teaches a different lesson than a crowded target with none (IL-23) — without this file, the two look identical in the convergence table.*

**Scope:** clinical-stage program deaths (Phase 1–3 or post-approval withdrawal) that are (a) on targets/mechanisms this KB tracks, (b) at our 22 covered companies, or (c) canonical industry lessons regardless of sponsor. Preclinical deaths are out of scope (unknowable, mostly). This registry is **representative, not exhaustive** — the complete attrition census exists only in commercial pipeline databases.

**Maintenance:** append-only, like `news/`. Rows enter via curation passes (see AGENTS.md event → scope table: trial failure/discontinuation events). Never delete a row; corrections edit in place with a note. Sort within each section by target, then year.

## Failure-mode vocabulary

| Code | Meaning | Example pattern |
|---|---|---|
| `efficacy` | Didn't work: missed primary endpoint(s) in adequately powered trial(s) | most Ph3 deaths |
| `safety` | Toxicity killed it (or the risk/benefit) | torcetrapib, fen-phen |
| `safety-class` | Toxicity inherent to mechanism, killing sibling programs too | BACE cognitive worsening |
| `strategic` | Sponsor deprioritized: portfolio shift, competitive landscape, cost | most quiet kills |
| `commercial` | Approved or approvable but market failed it | Aduhelm, Exubera |
| `manufacturing` | CMC/supply killed or crippled it | patritumab-DXd CRL |
| `unknown` | Sponsor never said; inference only | many CT.gov terminations |

## Reading notes (why this file exists)

1. **Survivorship denominators.** The target-convergence table (`03_target_convergence.md`) counts marketed assets per target. This file provides the denominator: marketed / (marketed + dead). A 4/4 target and a 4/24 target are different bets.
2. **Failure teaches at three levels.** A failed *target* (amyloid-for-cognition, IDO1) invalidates biology. A failed *molecule* on a target that later worked (early oral GLP-1s, first-gen anti-CD20s) teaches chemistry/format/PK. A failed *launch* (Aduhelm) teaches regulatory and payer dynamics. The `lesson` column tries to say which level.
3. **Absence of corpses is information too.** Targets where everyone who tried succeeded (IL-23p19, PCSK9) tend to be those validated by human genetics before the pile-on — the pattern behind the "what should target ID do" question this file exists to answer.

---

## Registry

*Seeded 2026-08-13: 128 entries from (a) the 22 company files' own failure mentions, (b) domain research (neuro, cardiometabolic, onco-immuno), (c) ClinicalTrials.gov termination mining across all 22 sponsors (see `graph/ctgov_failures.py`). Coverage is representative, not exhaustive.*

### Neuroscience (the amyloid wars and beyond)  (55 entries)

| Molecule | Target | Modality | Company | Phase | Died | Mode | What happened | Lesson |
|---|---|---|---|---|---|---|---|---|
| lorcaserin | 5-HT2C agonist | small molecule | Eisai (originator Arena) | approved-withdrawn | 2020 | safety | FDA-requested withdrawal Feb 2020 after CAMELLIA-TIMI 61 showed numerical cancer excess. | Selective receptor targeting fixed valvulopathy but new long-horizon risks emerged post-launch. |
| intepirdine (RVT-101) | 5-HT6 antagonist | small molecule | Axovant | Ph3 | 2017 | efficacy | MINDSET Ph3 (adjunct to donepezil, mild-moderate AD) missed both co-primaries Sept 2017; shelved Jan 2018 after DLB miss. | Asset flipped from GSK for $5M after Ph2 misses; discarded assets are usually discarded for reasons. |
| idalopirdine | 5-HT6 antagonist | small molecule | Lundbeck | Ph3 | 2017 | efficacy | Three STAR Ph3 trials (2,525 patients) showed no cognitive benefit as cholinesterase-inhibitor adjunct (2016-2017); dose lowered from Ph2. | Receptor-occupancy-based dose reduction between phases can quietly delete the effect; 5-HT6 class dead. |
| unnamed neurotrophic-factor programs | ALS | — | regeneron | — | — | efficacy | Neurotrophic-factor programs for ALS failed in the clinic during the 1988-2007 period. | — |
| verubecestat | BACE1 | small molecule | Merck | Ph3 | 2018 | safety-class | EPOCH stopped for futility 2017; APECS (prodromal AD) stopped 2018 with cognition worse than placebo. | On-target BACE inhibition worsens cognition; earlier treatment made it worse, not better. |
| lanabecestat | BACE1 | small molecule | AstraZeneca/Eli Lilly | Ph3 | 2018 | efficacy | AMARANTH and DAYBREAK-ALZ Ph3 trials stopped June 2018 on futility analyses; well tolerated. | Blocking Abeta production in symptomatic AD gives no benefit; damage already done. |
| atabecestat | BACE1 | small molecule | Janssen (J&J) | Ph3 | 2018 | safety | Ph2b/3 EARLY trial in preclinical AD stopped May 2018 for hepatotoxicity (elevated liver enzymes); cognition also worse. | Molecule-level liver toxicity can kill a program independent of class-level effects. |
| umibecestat | BACE1 | small molecule | Novartis/Amgen | Ph3 | 2019 | safety-class | Generation Ph2/3 prevention trials in ApoE4 carriers stopped July 2019: cognitive worsening, brain atrophy, weight loss. | Prevention trials amplify on-target harm; class signal reproduced in cognitively normal subjects. |
| elenbecestat | BACE1 | small molecule | Eisai/Biogen | Ph3 | 2019 | safety-class | MISSION AD1/2 stopped Sept 2019 by DSMB for unfavorable risk-benefit; last BACE inhibitor in Ph3. | Fifth Ph3 BACE death; on-target physiology (many BACE substrates) killed the whole class. |
| belantamab mafodotin | BCMA | ADC (MMAF, anti-BCMA) | GSK | approved-withdrawn | 2022 | efficacy | US authorization withdrawn Nov 22, 2022 at FDA request after confirmatory DREAMM-3 missed PFS (HR 1.03); ocular toxicity burden; DREAMM-7/8 later positive ex-US. | Accelerated approval is a loan: confirmatory miss forecloses the market even if later trials rehabilitate. |
| rimonabant | CB1 (inverse agonist) | small molecule | Sanofi-Aventis | approved-withdrawn | 2008 | safety | EU-approved 2006; never approved in US (suicidality); EU suspension and worldwide development halt 2008 for psychiatric events. | Central CB1 blockade carries mechanism-based depression/suicidality risk. |
| taranabant | CB1 (inverse agonist) | small molecule | Merck | Ph3 | 2008 | safety-class | Ph3 program stopped Oct 2008: dose-related psychiatric adverse events mirroring rimonabant; class abandoned (Pfizer CP-945,598 also killed). | A competitor's mechanism-based toxicity is predictive; class effects transfer across molecules. |
| soticlestat | CH24H | small molecule | Takeda | Ph3 | 2024 | efficacy | SKYLINE/SKYWAY narrow Ph3 misses in Dravet/LGS; 3 terminations | Near-miss p-values on rare-epilepsy endpoints: powering assumptions matter more than mechanism |
| Vioxx | COX-2 | small molecule | merck | approved-withdrawn | 2004 | safety | Voluntarily withdrawn worldwide September 2004 after trial data showed elevated heart-attack and stroke risk; $2.5B annual sales vaporized. | — |
| AMX0035 (Relyvrio) | ER stress/mitochondrial (PB+taurursodiol) | small molecule combination | Amylyx | approved-withdrawn | 2024 | efficacy | Approved for ALS 2022 on Ph2 CENTAUR; confirmatory Ph3 PHOENIX missed March 2024; voluntarily withdrawn from market April 2024. | Approval on a single Ph2 borrows against the confirmatory trial; withdrawal is the repayment. |
| asundexian | Factor XIa inhibitor | small molecule | Bayer | Ph3 | 2023 | efficacy | OCEANIC-AF stopped Nov 2023: stroke/systemic embolism 1.3% vs 0.4% on apixaban (HR 3.79); less bleeding. OCEANIC-STROKE continued. | Safety-first dosing (bleeding avoidance) can underdose efficacy against a strong active comparator. |
| lotiglipron (PF-07081532) | GLP-1R agonist (oral) | small molecule | Pfizer | Ph2 | 2023 | safety | Killed Jun 2023: elevated transaminases in Ph1 DDI and Ph2 studies; no symptomatic liver injury. | Liver enzyme signals in small-molecule GLP-1s are stop-signs before Ph3 investment. |
| iclepertin (BI 425809) | GlyT1 | small molecule | Boehringer Ingelheim | Ph3 | 2025 | efficacy | CONNEX 1-3 (1,840 patients, cognitive impairment in schizophrenia) missed all primary/secondary endpoints Jan 2025 despite breakthrough designation. | Ph2 cognition signals in schizophrenia rarely replicate; CIAS remains an endpoint graveyard. |
| epacadostat | IDO1 | small molecule | Incyte (partnered with Merck) | Ph3 | 2018 | efficacy | ECHO-301/KEYNOTE-252 stopped: PFS HR 1.00 vs pembrolizumab alone in melanoma; OS also futile; ~all IDO1 Ph3s pulled. | Single-arm response rates atop PD-1 are uninterpretable; demand monotherapy PD/proof-of-mechanism before Ph3. |
| ligelizumab | IgE | mAb | Novartis | Ph3 | 2021 | efficacy | Higher-affinity anti-IgE failed to beat omalizumab in PEARL CSU Ph3s; 4 terminations | Affinity is not efficacy; superiority-vs-own-incumbent trials are the hardest design |
| emraclidine (CVL-231) | M4 muscarinic (PAM) | small molecule | AbbVie (Cerevel) | Ph2 | 2024 | efficacy | Both EMPOWER Ph2 schizophrenia trials missed PANSS Nov 2024, centerpiece of $8.7B Cerevel buy; ~$3.5B impairment. | Single small Ph1b is thin support for multibillion M&A; same-pathway success (Cobenfy) doesn't transfer. |
| esreboxetine | NET (SNRI) | small molecule | Pfizer | Ph3 | 2009 | efficacy | 6 terminations: 'esreboxetine development program terminated' — fibromyalgia efficacy shortfall | Enantiomer respins of marginal drugs rarely rescue efficacy |
| fulranumab (JNJ-42160443) | NGF | mAb | Johnson & Johnson | Ph3 | 2016 | strategic | J&J returned rights to Amgen mid-Ph3 amid anti-NGF class safety holds; CT.gov whyStopped cites lack of efficacy in PAI2003 | Watch class-wide regulatory holds: they kill programs that never generated their own bad data |
| tanezumab | NGF | mAb | Pfizer/Eli Lilly | Ph3 | 2021 | safety | Anti-NGF for OA/chronic pain; rapidly progressive osteoarthritis signal, FDA AdCom 19-1 against; 14 terminated trials on CT.gov | Novel pain targets carry an asymmetric safety bar; a class-level AE (RPOA) killed three sponsors' programs at once |
| MK-0767 | PPARa/g dual | small molecule | Merck & Co (w/ Kyorin) | Ph3 | 2003 | safety | 10 terminated trials with blank whyStopped — a silent kill visible only as a cluster; preclinical carcinogenicity era of PPAR duals | Blank whyStopped clusters are where quiet kills hide; CT.gov cluster size substitutes for a press release |
| tesaglitazar | PPARa/g dual | small molecule | AstraZeneca | Ph3 | 2006 | safety | Galida; renal (creatinine) signal; 12 terminated trials, whyStopped: 'the development program has been terminated' | PPAR dual agonists died as a class (muraglitazar, MK-0767); mechanism-wide tox shows up late |
| acapatamab (AMG 160) | PSMA x CD3 | bispecific (HLE BiTE) | Amgen | Ph1 | 2022 | strategic | Deprioritized 2022 in favor of next-gen PSMA asset (AMG 340 in-license) amid CRS/tolerability management burden (est. mode). | Solid-tumor CD3 engagers face on-target CRS economics; companies iterate formats rather than push marginal first-gens. |
| mongersen (GED-0301) | SMAD7 | antisense oligo | Celgene/BMS | Ph3 | 2017 | efficacy | Ph3 Crohn's futility after $710M in-licensing; DMC-recommended stop; 4 terminations | Un-replicated single-country Ph2 data is the classic overpay setup |
| ulotaront (SEP-363856) | TAAR1/5-HT1A agonist | small molecule | Sumitomo Pharma/Otsuka | Ph3 | 2023 | efficacy | DIAMOND 1/2 in acute schizophrenia missed PANSS primary July 2023; large placebo response blamed; first TAAR1 agonist in Ph3. | Novel-mechanism antipsychotics die on placebo response; enrichment and site quality decide trials. |
| domvanalimab | TIGIT | mAb (Fc-silent) | Arcus Biosciences/Gilead | Ph3 | 2026 | efficacy | STAR-221 gastric futility (Dec 2025), STAR-121 NSCLC futility (Apr 2026), PACIFIC-8 dropped (Aug 2026); Gilead lapsed options. | Fc-silent differentiation thesis failed same as Fc-active rivals; mechanism, not format, was the problem. |
| Aduhelm | amyloid-beta | mAb | biogen | approved-withdrawn | 2024 | commercial | Commercial launch failed despite FDA accelerated approval; Medicare coverage restriction (April 2022) ended commercial viability; formally discontinued January 2024 with rights returned to Neurimmune. | — |
| AN-1792 | amyloid-beta (Abeta42 active immunization) | vaccine | Elan/Wyeth | Ph2 | 2002 | safety | Ph2a halted Jan 2002: aseptic meningoencephalitis in ~6% (18/298), T-cell (Th1) mediated; development terminated. | Active immunization against self-antigen risks T-cell autoimmunity; passive antibodies safer. |
| bapineuzumab | amyloid-beta (N-terminal, plaques) | mAb | Pfizer/Janssen (J&J) | Ph3 | 2012 | efficacy | Four Ph3 trials; Studies 301/302 missed cognitive/functional co-primaries in mild-moderate AD; IV program discontinued Aug 2012. | Plaque clearance in symptomatic AD too late; dose capped by ARIA in ApoE4 carriers. |
| gantenerumab | amyloid-beta (aggregated) | mAb | Roche | Ph3 | 2022 | efficacy | GRADUATE I/II missed primary Nov 2022; 6-8% slowing, n.s.; subcutaneous dosing removed less amyloid than expected. | Degree of amyloid removal predicts outcome; insufficient clearance = failed trial. |
| aducanumab | amyloid-beta (aggregated) | mAb | Biogen | approved-withdrawn | 2024 | commercial | Accelerated approval 2021 on contested data; CMS restricted coverage; Biogen discontinued sales and ENVISION trial Jan 2024. | Approval without clean efficacy data yields no payer coverage; launch dies commercially. |
| crenezumab | amyloid-beta (oligomers, IgG4) | mAb | Roche/Genentech (AC Immune) | Ph3 | 2022 | efficacy | CREAD 1/2 Ph3 stopped for futility Jan 2019; API Colombia autosomal-dominant prevention trial also negative June 2022. | IgG4 anti-oligomer design underdosed effector function; failed even in genetic prevention. |
| solanezumab | amyloid-beta (soluble monomer) | mAb | Eli Lilly | Ph3 | 2023 | efficacy | EXPEDITION 1-3 missed in mild AD (2012-2016); A4 preclinical-AD trial failed 2023 without even lowering plaque. | Binding soluble monomer doesn't clear plaque; target the aggregated species. |
| sitaxsentan | endothelin-A receptor | small molecule | Pfizer | Marketed (withdrawn) | 2010 | safety | Worldwide withdrawal for fatal idiosyncratic hepatotoxicity; trials terminated Dec 2010 | Post-marketing hepatotox can kill an approved asset faster than any Ph3 |
| NXY-059 (disufenton sodium) | free-radical trapping (neuroprotection) | small molecule | AstraZeneca/Renovis | Ph3 | 2006 | efficacy | SAINT II (3,306 acute stroke patients) neutral on all endpoints Oct 2006 after marginal SAINT I; development discontinued. | Preclinical stroke neuroprotection overestimated by biased animal studies; ~1,000 neuroprotectants failed. |
| semagacestat | gamma-secretase | small molecule | Eli Lilly | Ph3 | 2010 | safety | IDENTITY Ph3 trials halted Aug 2010: dose-dependent cognitive worsening plus excess skin cancers and infections. | Non-selective gamma-secretase inhibition hits Notch; substrate promiscuity is a target-level kill. |
| tominersen | huntingtin (HTT) | antisense oligonucleotide | roche | Ph3 | 2021 | efficacy | Huntington's disease program halted in 2021 due to lack of efficacy. | — |
| aticaprant | kappa opioid receptor antagonist | small molecule | Johnson & Johnson | Ph3 | 2025 | efficacy | Ph3 VENTURA program (adjunctive MDD, anhedonia-enriched) discontinued March 2025 for insufficient efficacy; safe and well tolerated. | KOR antagonism failed twice in 2025 (with navacaprant); anhedonia enrichment didn't rescue effect size. |
| navacaprant (NMRA-140) | kappa opioid receptor antagonist | small molecule | Neumora Therapeutics | Ph3 | 2025 | efficacy | KOASTAL-1 Ph3 in MDD missed MADRS primary and SHAPS secondary Jan 2025; sibling studies halted/paused. | Mechanism-level replication of failure across two sponsors is strong target invalidation. |
| latrepirdine (Dimebon) | mitochondrial/antihistamine (mechanism unclear) | small molecule | Pfizer/Medivation | Ph3 | 2010 | efficacy | Striking Russian Ph2 in AD; Ph3 CONNECTION missed all endpoints March 2010; Huntington's HORIZON also failed 2011; program abandoned 2012. | Single-country single-dose Ph2 results demand replication before global Ph3 investment. |
| fenfluramine/dexfenfluramine (fen-phen) | serotonin releaser (5-HT2B agonism) | small molecule | Wyeth (American Home Products) | approved-withdrawn | 1997 | safety | Withdrawn Sep 1997 after valvulopathy and pulmonary hypertension; >$13B legal damages. | 5-HT2B agonism causes valvulopathy; off-target receptor profiling is launch-critical. |
| sibutramine | serotonin-norepinephrine reuptake inhibitor | small molecule | Abbott | approved-withdrawn | 2010 | safety | Withdrawn Oct 2010 after SCOUT showed excess MI/stroke in CV-risk patients. | Sympathomimetic weight loss trades weight for cardiovascular events; post-marketing CVOTs can kill. |
| semorinemab | tau (N-terminal) | mAb | Genentech/Roche (AC Immune) | Ph2 | 2020 | efficacy | TAURIEL Ph2 (prodromal-mild AD) comprehensive miss reported Sept 2020; Lauriet (2021) hit ADAS-Cog only, not advanced. | Isolated single-endpoint signals in mixed Ph2s do not rescue a mechanism. |
| tilavonemab (ABBV-8E12) | tau (N-terminal) | mAb | AbbVie | Ph2 | 2021 | efficacy | No effect on progression in Ph2 early AD; also failed PSP (2019); AbbVie discontinued. | CSF target engagement did not translate; extracellular N-terminal tau likely wrong species. |
| gosuranemab (BIIB092) | tau (N-terminal) | mAb | Biogen | Ph2 | 2021 | efficacy | TANGO Ph2 in early AD missed June 2021 despite clearing CSF tau; had also failed PSP; some arms worsened on ADAS-Cog. | Peripheral/CSF tau clearance is not brain efficacy; intracellular tau unreachable by mAbs. |
| zagotenemab (LY3303560) | tau (aggregated, N-terminal epitope) | mAb | Eli Lilly | Ph2 | 2021 | efficacy | Ph2 miss in early symptomatic AD disclosed Oct 2021; fourth consecutive anti-tau antibody failure; Lilly discontinued. | Fourth same-epitope-family failure; N-terminal extracellular tau invalidated as antibody target. |
| LMTM (TRx0237) | tau aggregation | small molecule | TauRx | Ph3 | 2016 | efficacy | Ph3 read out 2016: no benefit as add-on to standard therapy; sponsor continued with contested monotherapy subgroup claims. | Post-hoc monotherapy subgroups are not evidence; methylene-blue derivative never showed clean effect. |

**Indication/launch-level failures of drugs that remain marketed** (not program deaths — the failed expansion carries the lesson):

| Molecule | Target | Modality | Company | Phase | Died | Mode | What happened | Lesson |
|---|---|---|---|---|---|---|---|---|
| Semaglutide (EVOKE program) | GLP-1R | small molecule | novo-nordisk | Ph3 | 2025 | efficacy | Failed in Alzheimer's disease (EVOKE, late 2025) and closed off the moonshot indication. Alzheimer's expansion failed; drug is a mega-blockbuster. | — |
| Cobenfy (KarXT) | M1/M4 muscarinic | small molecule | bristol-myers-squibb | Ph3 | 2025 | efficacy | ARISE adjunctive-schizophrenia trial missed primary endpoint in April 2025 despite September 2024 approval for monotherapy. | — |
| Zolgensma | SMN1 (spinal muscular atrophy) | gene therapy | novartis | marketed | 2019 | unknown | Approved 2019 at USD 2.1M/dose but quickly embroiled in data-manipulation scandal involving pre-submission animal data. data-manipulation scandal + safety warnings; drug remains marketed — NOT withdrawn. | — |
| Trodelvy | Trop-2 | ADC | gilead | approved-indication-withdrawn | 2024 | efficacy | Accelerated bladder-cancer approval withdrawn in 2024; lung-cancer trials disappointed. bladder AA withdrawn; drug marketed in breast. | — |

### Cardiometabolic (CETP, obesity's dark history, failed incretins)  (24 entries)

| Molecule | Target | Modality | Company | Phase | Died | Mode | What happened | Lesson |
|---|---|---|---|---|---|---|---|---|
| selonsertib | ASK1 inhibitor | small molecule | Gilead | Ph3 | 2019 | efficacy | STELLAR-4 (Feb 2019) and STELLAR-3 (Apr 2019) missed fibrosis endpoints; drug arms did not beat placebo. | Anti-fibrotic monotherapy downstream of metabolic drivers failed; MASH needed upstream metabolic mechanisms. |
| torcetrapib | CETP | small molecule | Pfizer | Ph3 | 2006 | safety | ILLUMINATE stopped Dec 2006: all-cause mortality HR 1.58 despite +72% HDL; off-target BP/aldosterone rise. | Molecule-level off-target toxicity can kill a program without invalidating the target. |
| dalcetrapib | CETP | small molecule | Roche | Ph3 | 2012 | efficacy | dal-OUTCOMES stopped May 2012 for futility; weak CETP inhibition raised HDL but no CV benefit. | Raising HDL-C per se does not reduce cardiovascular events. |
| evacetrapib | CETP | small molecule | Eli Lilly | Ph3 | 2015 | efficacy | ACCELERATE stopped Oct 2015 for futility despite potent HDL raising and LDL lowering. | Potent target engagement plus biomarker movement still failed outcomes; HDL hypothesis broken. |
| anacetrapib | CETP | small molecule | Merck | Ph3 | 2017 | strategic | REVEAL met endpoint (9% MACE reduction, LDL-driven) but Merck declined to file Oct 2017; adipose accumulation, 550-day half-life. | A statistically positive Ph3 can still be commercially unfilable if effect is marginal. |
| obeticholic acid (in NASH) | FXR agonist | small molecule | Intercept | Ph3 | 2023 | efficacy | REGENERATE hit fibrosis at highest dose only; FDA CRLs 2020 and 2023 on risk-benefit (pruritus, DILI concern); NASH program abandoned 2023. Remains approved in PBC. | Marginal efficacy plus tolerability liabilities fails regulatory risk-benefit even with a completed Ph3. |
| Exanta | Factor Xa | small molecule | astrazeneca | approved-withdrawn | — | safety | Anticoagulant withdrawn on liver safety grounds. | — |
| taspoglutide | GLP-1R agonist (once-weekly) | peptide | Roche (licensed from Ipsen) | Ph3 | 2010 | safety | Ph3 dosing stopped Sep 2010: hypersensitivity reactions, anti-drug antibodies (~50%), severe GI intolerance; returned to Ipsen 2011. | Peptide immunogenicity and formulation tolerability can kill despite validated mechanism. |
| danuglipron (PF-06882961) | GLP-1R agonist (oral) | small molecule | Pfizer | Ph2 | 2025 | safety | BID form dropped Dec 2023 (>50% discontinuation, GI); QD form killed Apr 2025 after one potential drug-induced liver injury case. | In a crowded class, tolerability parity is the bar; single safety cases kill laggards. |
| fasiglifam (TAK-875) | GPR40/FFAR1 | small molecule | Takeda | Ph3 | 2013 | safety | Hepatotoxicity signal across Ph3 diabetes program; 9 terminations incl. matched-placebo arms | First-in-class metabolic agonists need early hepatic safety depth; GPR40 field froze for a decade |
| Cerivastatin | HMG-CoA reductase (statin) | small molecule | bayer | approved-withdrawn | 2001 | safety | Lipobay/Baycol withdrawn worldwide August 2001 after reports of fatal rhabdomyolysis linked to ~100 deaths; >$1B in settlements. | — |
| darapladib | Lp-PLA2 inhibitor | small molecule | GlaxoSmithKline | Ph3 | 2014 | efficacy | STABILITY (2014) and SOLID-TIMI 52 both missed primary endpoints in ~29,000 patients. | Epidemiological biomarker association (Lp-PLA2) did not imply causality; genetics would have predicted failure. |
| ontamalimab (SHP647) | MAdCAM-1 | mAb | Takeda (ex-Shire, ex-Pfizer) | Ph3 | 2020 | strategic | Full IBD Ph3 program abandoned post-Shire-acquisition; 5 Ph3 terminations by sponsor decision | Acquired assets that duplicate an incumbent franchise (vedolizumab) die regardless of data |
| Avandia | PPAR-gamma (diabetes) | small molecule | gsk | approved-withdrawn | 2010 | safety | 2007 meta-analysis linked to cardiovascular risk; severe US restrictions imposed, EU market withdrawal 2010. | — |
| AVE5530 | cholesterol absorption | small molecule | Sanofi | Ph3 | 2009 | efficacy | 'Stopped due to insufficient efficacy' in hypercholesterolemia; 4 Ph3 terminations, minimal press | Fast-follower of ezetimibe with no differentiation — efficacy bar was the incumbent, not placebo |
| elafibranor (in NASH) | dual PPARalpha/delta agonist | small molecule | Genfit | Ph3 | 2020 | efficacy | RESOLVE-IT interim (May 2020) missed NASH resolution endpoint; high placebo response; trial terminated. Later approved for PBC (Iqirvo, 2024). | Indication-level death is not molecule death; biopsy endpoints with high placebo response are treacherous. |
| muraglitazar | dual PPARalpha/gamma agonist | small molecule | Bristol-Myers Squibb/Merck | Ph3 | 2006 | safety | AdCom-endorsed NDA derailed by Nissen JAMA analysis showing excess CV events, edema, heart failure; abandoned 2006. | Independent reanalysis of pooled safety data can reverse a near-approval. |
| aleglitazar | dual PPARalpha/gamma agonist | small molecule | Roche | Ph3 | 2013 | efficacy | AleCardio (7,228 post-ACS diabetics) halted Jul 2013 for futility plus PPAR class toxicity: fractures, heart failure, GI bleeding. | Re-entering a class after two safety failures needs a mechanistic fix, not just a new molecule. |
| inhaled insulin (Exubera) | insulin | inhaled protein | Pfizer/Nektar | Marketed (withdrawn) | 2007 | commercial | 'Marketing of this product will be discontinued' across 5 Ph3 terminations; ~$2.8B write-off | Device inconvenience + payer indifference kill even approved biologics; Novo's AERx followed in 2008 |
| Exubera (inhaled human insulin) | insulin receptor | inhaled protein | Pfizer (with Nektar) | approved-withdrawn | 2007 | commercial | Approved 2006; Pfizer pulled it Oct 2007 for commercial failure (~$2.8B charge); bulky device, spirometry burden, payer resistance. | Delivery convenience must beat incumbent workflow; device friction sank an approved drug. |
| Natrecor | natriuretic peptide receptor | protein | johnson-and-johnson | approved-withdrawn | — | safety | Partial failure after safety questions crushed sales following 2003 Scios acquisition. | — |
| Axokine | neurotrophy/obesity | protein | regeneron | — | 2003 | efficacy | Neurotrophic-factor obesity program collapsed in clinical development in 2003. | — |
| VX-264 | type 1 diabetes (encapsulated islet) | cell therapy | vertex | — | 2025 | strategic | Encapsulated-islet program discontinued in 2025. | — |

**Indication/launch-level failures of drugs that remain marketed** (not program deaths — the failed expansion carries the lesson):

| Molecule | Target | Modality | Company | Phase | Died | Mode | What happened | Lesson |
|---|---|---|---|---|---|---|---|---|
| Camzyos (mavacamten) | Cardiac myosin | small molecule | bristol-myers-squibb | Ph3 | 2025 | efficacy | ODYSSEY-HCM expansion trial in non-obstructive HCM failed in 2025; limits label expansion from obstructive HCM indication. drug remains marketed for oHCM. | — |

### Oncology (IDO1, TIGIT, failed ADCs and engagers)  (25 entries)

| Molecule | Target | Modality | Company | Phase | Died | Mode | What happened | Lesson |
|---|---|---|---|---|---|---|---|---|
| pacanalotamab (AMG 420) | BCMA x CD3 | bispecific (canonical BiTE, continuous IV) | Amgen | Ph1 | 2021 | strategic | 70% ORR at MTD in RRMM but required continuous IV infusion; shelved for half-life-extended AMG 701 (est. year). | Delivery burden can kill an efficacious molecule; PK/format is a launch-level variable. |
| pavurutamab (AMG 701) | BCMA x CD3 | bispecific (HLE BiTE) | Amgen | Ph1 | 2022 | strategic | Discontinued Aug 2022 after 2021 CRS-driven FDA enrollment pause; >50% CRS; crowded BCMA field (CAR-T, teclistamab) erased window. | Being third-to-market on a validated target with a slower asset is a kill criterion, not a milestone. |
| magrolimab | CD47 | mAb | Gilead | Ph3 | 2024 | safety | ENHANCE futility + excess deaths; FDA holds; 10 terminations | 'Don't-eat-me' hematology combos: on-target anemia + infection risk sank the lead of the class |
| rovalpituzumab tesirine (Rova-T) | DLL3 | ADC (PBD dimer payload) | AbbVie (Stemcentrx) | Ph3 | 2019 | efficacy | TAHOE: OS 6.3 vs 8.6 mo, worse than topotecan (2018); MERU maintenance no benefit; PBD toxicity (effusions, edema); $5.8B write-off. | Right target, wrong modality: DLL3 later validated by tarlatamab T-cell engager; PBD warhead therapeutic index too narrow. |
| Iressa | EGFR | small molecule | astrazeneca | approved-withdrawn | 2004 | efficacy | Stumbled in unselected lung cancer patients 2002–2004 before EGFR-targeted rationale was understood. | — |
| Exkivity (mobocertinib) | EGFR exon 20 insertion, lung cancer | small molecule | takeda | approved-withdrawn | 2023 | efficacy | Withdrawn after failed confirmatory trial in 2023. | — |
| amcenestrant | ER (oral SERD) | small molecule | Sanofi | Ph3 | 2022 | efficacy | AMEERA-3/-5 misses in HR+ breast cancer; 4 terminations | Oral SERD class: PK/potency differences made elacestrant work where amcenestrant failed |
| Patritumab deruxtecan | HER3 | ADC | daiichi-sankyo | Ph3 | 2025 | efficacy | US application withdrawn May 2025 after HERTHENA-Lung02 trial missed overall survival significance; manufacturing CRL June 2024. | — |
| navoximod (NLG919/GDC-0919) | IDO1 | small molecule | NewLink Genetics (Genentech-partnered) | Ph1 | 2018 | strategic | Genentech returned rights after unremarkable Ph1 combo data and the ECHO-301 IDO1 class collapse (est.). | Class-anchor trial failure (epacadostat) triggers portfolio contagion; me-too assets die without their own readout. |
| linrodostat (BMS-986205) | IDO1 | small molecule | Bristol-Myers Squibb | Ph3 | 2019 | efficacy | Wound down after epacadostat's ECHO-301 collapse; 4 Ph2/3 terminations citing SOC change/business | Class-lead readouts reprice every follower overnight; BMS cut before its own Ph3 read out |
| favezelimab | LAG-3 | mAb (pembrolizumab coformulation) | Merck & Co. | Ph3 | 2024 | efficacy | KEYFORM program (incl. KEYFORM-008 lymphoma) discontinued Dec 2024 alongside vibostolimab after data review. | LAG-3 value proved setting-specific (relatlimab melanoma); expansion beyond validated niche quietly died. |
| Cell-therapy platform | — | cell therapy | takeda | — | 2025 | strategic | Platform wound down in 2025 as part of restructuring. | — |
| MYSTIC | PD-L1 | mAb | astrazeneca | Ph3 | 2017 | efficacy | High-profile failure of MYSTIC trial in 2017 in lung cancer. | — |
| tiragolumab | TIGIT | mAb | Roche | Ph3 | 2024 | efficacy | SKYSCRAPER-01/-06 misses; 10 direct terminations plus the 28-trial atezolizumab combo cluster | Combo-partner deaths surface in the backbone drug's trial cluster — read clusters jointly |
| vibostolimab (MK-7684) | TIGIT | mAb (pembrolizumab coformulation) | Merck & Co. | Ph3 | 2024 | efficacy | Four Ph3s hit futility (KeyVibe-003/-007/-008/-010); KeyVibe-008 OS HR 1.26 with excess irAEs; program discontinued Dec 2024. | Adding a second checkpoint can subtract: added toxicity drove adjuvant discontinuations, worsening efficacy. |
| ociperlimab (BGB-A1217) | TIGIT | mAb | BeiGene | Ph3 | 2025 | efficacy | AdvanTIG-302 terminated at OS futility interim (Apr 2025); whole program killed; Novartis had earlier walked from option. | Partner walk-aways (Novartis 2023) are leading indicators of class-level futility. |
| Belrestotug | TIGIT (oncology) | mAb | gsk | — | 2025 | unknown | Program terminated 2025 with £471M impairment. | — |
| sabatolimab (MBG453) | TIM-3 | mAb | Novartis | Ph3 | 2023 | efficacy | STIMULUS-MDS2 miss ended the TIM-3 MDS/AML program; 9 terminations across both names | Second-wave checkpoint targets (TIM-3, TIGIT, LAG-3 beyond melanoma) mostly failed to repeat PD-1 |
| Zaltrap | VEGF | mAb | regeneron | approved-withdrawn | 2012 | commercial | Ziv-aflibercept approved in 2012 for colorectal cancer but flopped amid pricing controversy. | — |
| Lartruvo | VEGF-A | mAb | eli-lilly | approved-withdrawn | 2019 | efficacy | Withdrawn in 2019 after the ANNOUNCE Phase 3 trial failed. | — |
| giredestrant | estrogen receptor (SERD) | small molecule | roche | Ph3 | — | efficacy | Failed in first-line metastatic breast cancer; repositioned to adjuvant setting with Priority Review. | — |
| sigvotatug vedotin | integrin beta-6 ADC | ADC | pfizer | Ph3 | 2026 | efficacy | Phase 3 SigVie-002 second-line NSCLC trial missed overall survival in June 2026. | — |

**Indication/launch-level failures of drugs that remain marketed** (not program deaths — the failed expansion carries the lesson):

| Molecule | Target | Modality | Company | Phase | Died | Mode | What happened | Lesson |
|---|---|---|---|---|---|---|---|---|
| Kymriah (tisagenlecleucel) — 2L LBCL | CD19 | CAR-T | novartis | Ph3 | 2021 | efficacy | BELINDA missed in second-line large B-cell lymphoma (Aug 2021) where Yescarta (ZUMA-7) and Breyanzi succeeded on the same target. | Same target, different construct/logistics: CD19 was not the variable. |
| Blenrep | BCMA (multiple myeloma) | ADC | gsk | approved-withdrawn-relaunched | 2022 | efficacy | Won accelerated US approval 2020 but withdrawn from US market late 2022 after confirmatory DREAMM-3 trial failed. US withdrawal 2022 after DREAMM-3; relaunched 2025-26 on DREAMM-7/8. | — |
| Opdivo (nivolumab) | PD-1 | mAb | bristol-myers-squibb | Ph3 | 2016 | efficacy | CheckMate-026 trial failed in August 2016: Opdivo monotherapy did not beat chemotherapy in first-line NSCLC with broad PD-L1 cutoff, ceding market leadership to Keytruda. | — |
| Opdualag (nivolumab + ipilimumab) | PD-1 + CTLA-4 | mAb | bristol-myers-squibb | Ph3 | 2025 | efficacy | Adjuvant melanoma trial missed in 2025; limits expansion of combination checkpoint inhibitor franchise. | — |

### Immunology & inflammation  (10 entries)

| Molecule | Target | Modality | Company | Phase | Died | Mode | What happened | Lesson |
|---|---|---|---|---|---|---|---|---|
| tabalumab (LY2127399) | BAFF | mAb | Eli Lilly | Ph3 | 2015 | efficacy | Insufficient efficacy in lupus (ILLUMINATE) and MM; 9 terminations across drug+device clusters | Belimumab worked on the same target — dose, population and endpoint choice decide BAFF outcomes |
| tolebrutinib | BTK (brain-penetrant) | small molecule | sanofi | Ph3 | 2025 | efficacy | Failed primary progressive MS trial; despite positive HERCULES data in non-relapsing secondary progressive MS and breakthrough designation, FDA issued complete response letter in December 2025. | — |
| Alofisel | Cell therapy, Crohn's disease | cell therapy | takeda | Ph3 | 2023 | efficacy | Failed Phase 3 trial in 2023. | — |
| efavaleukin alfa | IL-2 mutein (Treg-biased) | fusion protein | Amgen | Ph2b | 2023 | efficacy | Lupus futility ended program; 5 linked terminations | Treg-expansion biomarkers did not translate to clinical endpoints in lupus |
| rocatinlimab | IL-4 receptor alpha | mAb | amgen | Ph2 | 2026 | strategic | Collaboration with Kyowa Kirin terminated in early 2026; portfolio deprioritization in favor of higher-conviction assets. | — |
| filgotinib (US) | JAK1 | small molecule | Gilead/Galapagos | approved-withdrawn | 2020 | safety-class | FDA CRL (Aug 2020) over testicular toxicity and 200-mg benefit/risk; Gilead abandoned US RA path Dec 2020; EU/Japan approved (Jyseleca). | Regulatory geography splits a launch: class-level safety scrutiny (JAK) can kill one market while another approves. |
| Camlipixant | P2X3 (chronic cough) | small molecule | gsk | Ph3 | 2026 | efficacy | Discontinued July 2026 for refractory chronic cough after mixed CALM-1/CALM-2 phase III results. | — |
| lampalizumab | complement factor D | Fab | Roche | Ph3 | 2017 | efficacy | SPECTRI/CHROMA geographic-atrophy misses; 4 terminations | GA endpoints later worked for pegcetacoplan — target choice within complement mattered |
| BI 3720931 | cystic fibrosis gene therapy | gene therapy | boehringer-ingelheim | — | 2026 | strategic | Inhaled cystic fibrosis gene therapy program halted in 2026 as part of portfolio pruning. | — |
| vilaprisan | progesterone receptor (SPRM) | small molecule | Bayer | Ph3 | 2020 | safety | Uterine fibroids; program stopped on long-term rodent tox findings after ulipristal's hepatotox scare; 7 terminations | Preclinical tox re-reads can kill a Ph3 asset when a sister drug poisons the class's risk-benefit |

### Infectious disease & vaccines  (7 entries)

| Molecule | Target | Modality | Company | Phase | Died | Mode | What happened | Lesson |
|---|---|---|---|---|---|---|---|---|
| mRNA-1647 | Cytomegalovirus (CMV) | mRNA vaccine | moderna | Ph3 | 2025 | efficacy | Failed Phase 3 CMVictory trial in October 2025 with 6–23% efficacy; discontinued for congenital CMV indication. | — |
| GS-1720/GS-4182 | HIV capsid/integrase | small molecule | gilead | Ph2 | 2026 | regulatory | Weekly oral lenacapavir combination hit FDA clinical hold in early 2026. | — |
| BMS-986094 | Hepatitis C NS5B polymerase | small molecule | bristol-myers-squibb | Ph2 | 2012 | safety | Nucleotide polymerase inhibitor halted after patient death in clinical trial; triggered $1.8B writedown from Inhibitex acquisition. | — |
| COVID-19 vaccine (J&J) | SARS-CoV-2 | viral vector | johnson-and-johnson | approved-withdrawn | 2023 | safety | Discontinued in 2023 after rare thrombosis with thrombocytopenia (TTS) events triggered April 2021 pause. | — |
| Dengvaxia | dengue | vaccine | sanofi | approved-withdrawn | 2017 | safety | Philippine school program suspended in 2017 after Sanofi disclosed increased risk in previously uninfected children; became reputational crisis. | — |

**Indication/launch-level failures of drugs that remain marketed** (not program deaths — the failed expansion carries the lesson):

| Molecule | Target | Modality | Company | Phase | Died | Mode | What happened | Lesson |
|---|---|---|---|---|---|---|---|---|
| Qdenga (dengue vaccine) | Dengue virus vaccine | — | takeda | approved-exUS | 2023 | strategic | US application withdrawn in 2023. US filing withdrawn; marketed ex-US. | — |
| mRESVIA | Respiratory Syncytial Virus (RSV) | mRNA vaccine | moderna | marketed | 2025 | commercial | FDA approved May 2024 but commercially failed; booked only $25M in 2024 and $8M in 2025 due to late market entry behind GSK Arexvy and Pfizer Abrysvo. approved and marketed; commercial failure only. | — |

### Rare disease  (2 entries)

| Molecule | Target | Modality | Company | Phase | Died | Mode | What happened | Lesson |
|---|---|---|---|---|---|---|---|---|
| VX-814 | alpha-1 antitrypsin deficiency corrector | small molecule | vertex | — | 2020 | unknown | Alpha-1 antitrypsin deficiency corrector failed in 2020, knocking the stock. | — |
| VX-864 | alpha-1 antitrypsin deficiency corrector | small molecule | vertex | — | 2021 | unknown | Alpha-1 antitrypsin deficiency corrector failed in 2021, knocking the stock. | — |

### Post-market safety withdrawals (pre-2010 era lessons)  (5 entries)

| Molecule | Target | Modality | Company | Phase | Died | Mode | What happened | Lesson |
|---|---|---|---|---|---|---|---|---|
| Bextra | COX-2 | small molecule | pfizer | approved-withdrawn | 2005 | safety | COX-2 inhibitor withdrawn in 2005 on safety grounds. | — |
| ranitidine (Zantac) | H2 receptor antagonist | small molecule | sanofi | approved-withdrawn | 2019 | manufacturing | Pulled from market in 2019 over NDMA contamination; spawned mass litigation and ~$300-350M in settlements by 2024-2026. | — |
| Propulsid | gastric motility | small molecule | johnson-and-johnson | approved-withdrawn | 2000 | safety | Withdrawn from US market in 2000 after fatal arrhythmias. | — |
| Xigris | sepsis | small molecule | eli-lilly | approved-withdrawn | 2011 | efficacy | Sepsis drug withdrawn in 2011 after a failed confirmatory trial. | — |
| Oxbryta | soluble guanylate cyclase activator | small molecule | pfizer | approved-withdrawn | 2024 | strategic | Sickle-cell drug (voxelotor, core of GBT acquisition) withdrawn worldwide in 2024. | — |

---

## Source & coverage notes

- **CT.gov mining** (2,608 terminated/withdrawn/suspended Ph2-3 trials across 22 sponsor groups, clustered to ~3,000 interventions) contributed ~23 verified rows including silent kills with no press release (MK-0767's 10 blank-whyStopped terminations, esreboxetine, AVE5530). Terminated ≠ failed: most entries required news verification; most Ph3 efficacy failures never show as "terminated" at all.
- **Known bias**: entries skew toward (1) failures big enough to make news, (2) our 22 covered companies, (3) post-2005 (CT.gov coverage). The pre-2000 graveyard and dead-biotech graveyard are underrepresented — that data substantially exists only in commercial pipeline databases.
- **Update path**: OpenClaw's daily feed flags trial failures/discontinuations → curation pass appends rows here + updates `graph/cache/graveyard.json` (see AGENTS.md).
