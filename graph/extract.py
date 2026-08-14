#!/usr/bin/env python3
"""pharma-space graph extraction — regenerates graph/ from the prose KB.

Usage (from repo root):  python3 graph/extract.py

Design: INCREMENTAL. Mechanical parsing (drug index, assets tables) runs fresh
every time; LLM-derived facts (targets, deals) come from graph/cache/*.json.
When new molecules or updated company files need LLM extraction, this script
does NOT call an LLM itself — it writes graph/cache/TODO.md containing
ready-to-use prompts. The maintaining agent (Claude Science, OpenClaw, ...)
fulfills those prompts with its own LLM, merges the JSON answers into the
cache files, and re-runs this script. Everything else is deterministic.

Outputs: graph/nodes.jsonl, graph/edges.jsonl, reference/03_target_convergence.md,
and a lint report on stdout. Stdlib only. Do not hand-edit outputs.
"""
import json, re, os, glob, sys, datetime
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "graph", "cache")
today = datetime.date.today().isoformat()

# ---------------- controlled vocabularies ----------------
COMPANY_SLUG = {
    "amgen":"amgen","bms":"bristol-myers-squibb","lilly":"eli-lilly","j&j":"johnson-and-johnson",
    "pfizer":"pfizer","merck":"merck","roche":"roche","novartis":"novartis","az":"astrazeneca",
    "novo":"novo-nordisk","abbvie":"abbvie","sanofi":"sanofi","gsk":"gsk","takeda":"takeda",
    "gilead":"gilead","boehringer":"boehringer-ingelheim","boehringer ingelheim":"boehringer-ingelheim",
    "bayer":"bayer","daiichi":"daiichi-sankyo","daiichi sankyo":"daiichi-sankyo","vertex":"vertex",
    "regeneron":"regeneron","biogen":"biogen","moderna":"moderna","eisai":"eisai","legend":"legend",
    "crispr":"crispr-therapeutics","crispr therapeutics":"crispr-therapeutics",
}
FX = {"DKK":0.149,"CHF":1.12,"EUR":1.09,"JPY":0.0067,"GBP":1.28,"SEK":0.096}

MODALITY_RULES = [

    ("car-t","cell-therapy"),("cell therapy","cell-therapy"),("adc","adc"),("deruxtecan","adc"),
    ("vedotin","adc"),("govitecan","adc"),("antibody-drug","adc"),("drug conjugate","adc"),
    ("soravtansine","adc"),("emtansine","adc"),("mafodotin","adc"),("tirumotecan","adc"),
    ("bispecific","bispecific-ab"),("bite","bispecific-ab"),
    ("antibody","mab"),("mab","mab"),("sirna","sirna"),("antisense","aso"),("oligonucleotide","aso"),
    ("gene therapy","gene-therapy"),("gene-edit","gene-editing"),("crispr","gene-editing"),
    ("mrna","mrna"),("peptide","peptide"),("glp-1","peptide"),("insulin","peptide"),
    ("fusion protein","fusion-protein"),("peptibody","fusion-protein"),("enzyme","enzyme"),
    ("erythropoietin","biologic-other"),("maturation agent","biologic-other"),("vaccine","vaccine"),
    ("radioligand","radioligand"),("radioconjugate","radioligand"),
    # --- added 2026-08-14 (found by clicking Cuvitru: immunoglobulin was silently defaulting to small-molecule) ---
    ("immunoglobulin","immunoglobulin"),("immune globulin","immunoglobulin"),("globulin","immunoglobulin"),
    ("plasma-derived","plasma-derived"),("albumin","plasma-derived"),
    ("factor viii","clotting-factor"),("factor viia","clotting-factor"),("factor ix","clotting-factor"),
    ("factor x","clotting-factor"),("coagulation","clotting-factor"),("antihemophilic","clotting-factor"),
    ("interferon","cytokine"),("interleukin","cytokine"),("colony-stimulating","cytokine"),
    ("thrombopoietin","cytokine"),("g-csf","cytokine"),("epoetin","cytokine"),
    ("growth hormone","hormone"),("somatropin","hormone"),("parathyroid hormone","hormone"),
    ("hormone analog","hormone"),("gonadotropin","hormone"),
    ("neurotoxin","toxin"),("botulinum","toxin"),
    ("costimulation blocker","fusion-protein"),("receptor fusion","fusion-protein"),("-cept","fusion-protein"),
    ("biosimilar","biosimilar"),("polysaccharide","vaccine"),("antigen","vaccine"),
    ("liposomal","formulation-smallmolecule"),("nanoparticle","formulation-smallmolecule"),
    ("recombinant","recombinant-protein"),  # catch-all AFTER the specific recombinant classes above
    ("tpa","recombinant-protein"),("enzyme replacement","enzyme"),
]
SMALL_MOL_HINTS = ("inhibitor", "agonist", "antagonist", "modulator", "blocker", "small molecule",
                   "kinase", "oral", "statin", "-tinib", "-prazole", "-sartan", "-vir", "degrader")
MODALITY_OVERRIDES = {}
_mo = os.path.join(CACHE, "modality_overrides.json")
if os.path.exists(_mo):
    MODALITY_OVERRIDES = json.load(open(_mo))

def modality_of(cls):
    """Map a class description to a modality.

    NOTE: never silently default to small-molecule — that is how Cuvitru (an
    immunoglobulin) was once labelled a small molecule. An unmatched class with no
    small-molecule hint returns "unclassified" so the lint surfaces it.
    """
    c = cls.lower()
    for pat, m in MODALITY_RULES:
        if pat in c: return m
    if any(h in c for h in SMALL_MOL_HINTS): return "small-molecule"
    return "unclassified"

STEM_RULES = [
    # generic-name stems are STRONGER evidence than class prose: a "-mab" is an antibody
    # even when the class cell only says "PD-1 checkpoint inhibitor". (Found 2026-08-14:
    # nivolumab/pembrolizumab/ipilimumab were all labelled small-molecule for this reason.)
    (r"\w+(zumab|ximab|umab|omab|imab)\b", "mab"),
    (r"\w+(vedotin|deruxtecan|govitecan|emtansine|mafodotin|soravtansine|tesirine|tirumotecan)\b", "adc"),
    (r"\w+(leucel|cabtagene)\b", "cell-therapy"),
    (r"\w+cept\b", "fusion-protein"),
    (r"\w+(glutide|tide|relin|actide)\b", "peptide"),
    (r"\w+(sen|rsen|mersen)\b", "aso"),
    (r"\w+siran\b", "sirna"),
    (r"\w+(gene|parvovec|vec)\b", "gene-therapy"),
    (r"\w+(tinib|ciclib|parib|rafenib|degib|lisib|metinib)\b", "small-molecule"),
]
def mod_of(generic, cls):
    """Modality for a molecule.

    Precedence: curated override > generic-name stem > class-text rules.
    The stem outranks the class because class cells describe MECHANISM
    ("PD-1 inhibitor"), which says nothing about molecular format.
    Bispecific/ADC class text still wins over a plain -mab stem via the
    explicit check below.
    """
    g = generic.lower().strip()
    if g in MODALITY_OVERRIDES: return MODALITY_OVERRIDES[g]
    c = cls.lower()
    # class text that is MORE specific than the stem
    for pat, m in (("bispecific","bispecific-ab"), ("bite","bispecific-ab"), ("t-cell engager","bispecific-ab"),
                   ("antibody-drug","adc"), ("drug conjugate","adc"), ("adc","adc"),
                   ("biosimilar","biosimilar"), ("radioligand","radioligand"), ("radioconjugate","radioligand")):
        if pat in c: return m
    for pat, m in STEM_RULES:
        if re.search(pat, g): return m
    return modality_of(cls)

IND_RULES = {
    # --- added 2026-08-14: gaps found by clicking through the explorer (Gleevec -> "other") ---
    "chronic myeloid leukemia": "cml", "cml": "cml",
    "gastrointestinal stromal": "gist", "gist": "gist",
    "acute lymphoblastic": "all-leukemia", "acute myeloid": "aml", "aml": "aml",
    "myeloproliferative": "mpn", "polycythemia": "mpn",
    "acne": "dermatology-other", "eczema": "atopic dermatitis",
    "erectile": "urology-other", "benign prostatic": "urology-other", "overactive bladder": "urology-other",
    "contracept": "womens-health", "endometriosis": "womens-health", "menopaus": "womens-health", "fibroid": "womens-health",
    "glaucoma": "eye", "allerg": "allergy", "rhinitis": "allergy", "urticaria": "allergy",
    "insomnia": "sleep", "narcolepsy": "sleep", "adhd": "neuro-other", "smoking": "addiction", "opioid": "addiction",
    "nausea": "supportive-care", "neutropenia": "supportive-care", "mucositis": "supportive-care",
    "thyroid cancer": "thyroid-cancer", "head and neck": "head-neck-cancer", "esophageal": "gi-cancer",
    "pancrea": "gi-cancer", "cholangio": "gi-cancer", "sarcoma": "sarcoma", "myelodysplastic": "mds",
    "immunoglobulin": "immunology-other", "immune deficiency": "immunology-other",
    "constipation": "gi-other", "reflux": "gi-other", "ulcer": "gi-other", "irritable bowel": "gi-other",
    "osteoarthritis": "musculoskeletal", "fibromyalgia": "pain", "anesthes": "anesthesia",
    "contrast": "imaging", "radiolog": "imaging", "diagnostic": "imaging",
    "bacterial": "infection-other", "antibiotic": "infection-other", "fungal": "infection-other",
    "tuberculosis": "infection-other", "vaccine": "vaccines-other",  # substring -> indication id
    "obesity":"obesity","type 2 diabetes":"type-2-diabetes","t2d":"type-2-diabetes","diabetes":"type-2-diabetes",
    "type 1 diabetes":"type-1-diabetes","heart failure":"heart-failure","stroke prevention":"anticoagulation",
    "anticoagul":"anticoagulation","cholesterol":"dyslipidemia","ldl":"dyslipidemia","lipid":"dyslipidemia",
    "cardiovascular":"dyslipidemia","hypertrophic cardiomyopathy":"cardiomyopathy",
    "pulmonary arterial hypertension":"pulmonary-arterial-hypertension","pah":"pulmonary-arterial-hypertension",
    "myeloma":"multiple-myeloma","lymphoma":"lymphoma","leukemia":"leukemia","cll":"leukemia","mds":"mds",
    "myelofibrosis":"myelofibrosis","breast cancer":"breast-cancer","lung cancer":"lung-cancer","nsclc":"lung-cancer",
    "sclc":"lung-cancer","prostate":"prostate-cancer","colorectal":"colorectal-cancer","melanoma":"melanoma",
    "bladder":"bladder-cancer","gastric":"gastric-cancer","ovarian":"ovarian-cancer","renal":"kidney-cancer",
    "rcc":"kidney-cancer","hepatocellular":"liver-cancer","many cancers":"pan-tumor","multiple cancers":"pan-tumor",
    "various cancers":"pan-tumor","solid tumors":"pan-tumor","neuroendocrine":"pan-tumor","bone metastases":"pan-tumor",
    "psoriasis":"psoriasis","psoriatic":"psoriasis","rheumatoid":"rheumatoid-arthritis","atopic dermatitis":"atopic-dermatitis",
    "crohn":"ibd","ulcerative colitis":"ibd","ibd":"ibd","asthma":"asthma","copd":"copd","lupus":"lupus",
    "spondylo":"axial-spondyloarthritis","multiple sclerosis":"multiple-sclerosis","alzheimer":"alzheimers",
    "migraine":"migraine","schizophrenia":"schizophrenia","depression":"depression","bipolar":"depression",
    "epilep":"epilepsy","parkinson":"parkinsons","spinal muscular":"sma","friedreich":"rare-other",
    "osteoporosis":"osteoporosis","gout":"gout","thyroid eye":"thyroid-eye-disease","anemia":"anemia","itp":"itp",
    "hemophilia":"hemophilia","hiv":"hiv","hepatitis":"hepatitis","covid":"covid","rsv":"rsv","flu":"influenza",
    "pneumo":"pneumococcal","shingles":"shingles","hpv":"hpv","menin":"meningococcal","malaria":"malaria",
    "cystic fibrosis":"cystic-fibrosis","sickle":"sickle-cell","thalassemia":"sickle-cell","amyloid":"attr-amyloidosis",
    "fabry":"rare-other","gaucher":"rare-other","pnh":"pnh","hae":"rare-other","myasthenia":"gmg",
    "eye":"retinal-disease","macular":"retinal-disease","retina":"retinal-disease","dme":"retinal-disease",
    "sleep apnea":"obesity","weight":"obesity","ckd":"chronic-kidney-disease","kidney disease":"chronic-kidney-disease",
    "growth":"rare-endocrine","transplant":"transplant","pulmonary fibrosis":"ipf","ipf":"ipf","pain":"pain",
}
AREA = {}
for _ind, _area in {
    "addiction":"neuroscience",
    "all-leukemia":"oncology",
    "allergy":"immunology",
    "aml":"oncology",
    "anesthesia":"neuroscience",
    "cml":"oncology",
    "dermatology-other":"immunology",
    "eye":"other",
    "gi-cancer":"oncology",
    "gi-other":"other",
    "gist":"oncology",
    "head-neck-cancer":"oncology",
    "imaging":"other",
    "immunology-other":"immunology",
    "infection-other":"infectious-disease",
    "mpn":"oncology",
    "musculoskeletal":"other",
    "neuro-other":"neuroscience",
    "pain":"neuroscience",
    "sarcoma":"oncology",
    "sleep":"neuroscience",
    "supportive-care":"oncology",
    "thyroid-cancer":"oncology",
    "urology-other":"other",
    "vaccines-other":"infectious-disease",
    "womens-health":"other",
    "obesity":"cardiometabolic","type-2-diabetes":"cardiometabolic","type-1-diabetes":"cardiometabolic",
    "heart-failure":"cardiometabolic","anticoagulation":"cardiometabolic","dyslipidemia":"cardiometabolic",
    "cardiomyopathy":"cardiometabolic","chronic-kidney-disease":"cardiometabolic","pulmonary-arterial-hypertension":"cardiometabolic",
    "multiple-myeloma":"oncology","lymphoma":"oncology","leukemia":"oncology","mds":"oncology","myelofibrosis":"oncology",
    "breast-cancer":"oncology","lung-cancer":"oncology","prostate-cancer":"oncology","colorectal-cancer":"oncology",
    "melanoma":"oncology","bladder-cancer":"oncology","gastric-cancer":"oncology","ovarian-cancer":"oncology",
    "kidney-cancer":"oncology","liver-cancer":"oncology","pan-tumor":"oncology",
    "psoriasis":"immunology","rheumatoid-arthritis":"immunology","atopic-dermatitis":"immunology","ibd":"immunology",
    "asthma":"immunology","copd":"immunology","lupus":"immunology","axial-spondyloarthritis":"immunology","gout":"immunology",
    "thyroid-eye-disease":"immunology","transplant":"immunology",
    "multiple-sclerosis":"neuroscience","alzheimers":"neuroscience","migraine":"neuroscience","schizophrenia":"neuroscience",
    "depression":"neuroscience","epilepsy":"neuroscience","parkinsons":"neuroscience","sma":"neuroscience","gmg":"neuroscience","pain":"neuroscience",
    "hiv":"vaccines-id","hepatitis":"vaccines-id","covid":"vaccines-id","rsv":"vaccines-id","influenza":"vaccines-id",
    "pneumococcal":"vaccines-id","shingles":"vaccines-id","hpv":"vaccines-id","meningococcal":"vaccines-id","malaria":"vaccines-id",
    "cystic-fibrosis":"rare","sickle-cell":"rare","attr-amyloidosis":"rare","rare-other":"rare","pnh":"rare",
    "hemophilia":"rare","rare-endocrine":"rare",
    "osteoporosis":"other","anemia":"other","itp":"other","retinal-disease":"other","ipf":"respiratory","other":"other",
}.items(): AREA[_ind] = _area

TARGET_CANON = {
    # --- alias-audit merges (2026-08-14, LLM sweep + manual canonical direction) ---
    "AGTR1": "AT1R",
    "ATP4A": "H+/K+-ATPase",
    "BLYS": "BAFF",
    "CEREBLON": "CRBN",
    "CGRP-R": "CGRP receptor",
    "COX-2": "COX2",
    "CYP3A": "CYP3A4",
    "D2": "DRD2",
    "F10": "Factor-Xa",
    "F2": "Factor IIa",
    "F8": "Factor-VIII",
    "FOLH1": "PSMA",
    "FACTOR VIIIA": "Factor-VIII",
    "GABRA": "GABA-A receptor",
    "GUCY1A3": "soluble guanylate cyclase",
    "HT2A": "5-HT2A",
    "HEPATITIS C NS5B POLYMERASE": "HCV NS5B",
    "IFNAR": "IFNAR1",
    "IL-4R-ALPHA": "IL-4 receptor alpha",
    "IL-6R": "IL6R",
    "IN": "HIV integrase",
    "KLKB1": "plasma kallikrein",
    "M1": "CHRM1",
    "M3 MUSCARINIC RECEPTOR": "CHRM3",
    "M4": "M4 muscarinic",
    "MPL": "TPOR",
    "MYH7": "cardiac myosin",
    "NPRA": "natriuretic peptide receptor",
    "NR3C1": "GR",
    "NR3C4": "AR",
    "NS5A": "HCV NS5A",
    "NS5B": "HCV NS5B",
    "PGR": "progesterone receptor",
    "PPAR-GAMMA": "PPARG",
    "PPARA/G": "PPARalpha/gamma",
    "PSMB5": "proteasome",
    "PTGS2": "COX2",
    "RSV-F": "RSV F",
    "RT": "HIV reverse transcriptase",
    "S. PNEUMONIAE POLYSACCHARIDE": "pneumococcal polysaccharide antigens",
    "SARS-COV-2 SPIKE": "SARS-CoV-2 spike protein",
    "SARS-COV-2 SPIKE": "SARS-CoV-2 spike protein",
    "SLC6A2": "NET",
    "VEGFR-1": "VEGFR1",
    "VEGFR-2": "VEGFR2",
    "VEGFR-3": "VEGFR3",
    "BETA-2 ADRENERGIC RECEPTOR": "ADRB2",
    "C-MET": "MET",
    "CARDIAC MYOFILAMENT": "cardiac myosin",
    "DENGUE": "dengue virus",
    "ENDOTHELIN-A RECEPTOR": "EDNRA",
    "FACTOR X": "Factor-Xa",
    "GLUCOCORTICOID RECEPTOR": "GR",
    "NOREPINEPHRINE TRANSPORTER": "NET",
    "SOLUBLE GUANYLATE CYCLASE ACTIVATOR": "soluble guanylate cyclase",
    "TAU AGGREGATION": "tau",
    "THROMBIN": "Factor IIa",
    "PD1":"PD-1","PDCD1":"PD-1","PDL1":"PD-L1","GLP1R":"GLP-1R","GLP-1":"GLP-1R","GIP":"GIPR",
    "IL23":"IL-23p19","IL-23":"IL-23p19","IL-23P19":"IL-23p19","IL-12/23":"IL-12/23-p40","IL17":"IL-17A",
    "IL-17":"IL-17A","IL13":"IL-13","IL4R":"IL-4Ra","IL-4RA":"IL-4Ra","IL-4R":"IL-4Ra","IL5":"IL-5","IL6":"IL-6",
    "TNF":"TNF-alpha","TNF-A":"TNF-alpha","TNF-ALPHA":"TNF-alpha","ERBB2":"HER2","VEGF":"VEGF-A","VEGFA":"VEGF-A",
    "FACTOR XA":"Factor-Xa","FXA":"Factor-Xa","KRAS G12C":"KRAS-G12C","KRASG12C":"KRAS-G12C","TROP-2":"TROP2",
    "DPP4":"DPP-4","CDK4":"CDK4/6","CDK6":"CDK4/6","PARP1":"PARP","CTLA4":"CTLA-4","LAG3":"LAG-3",
    "S1P":"S1PR","S1P1":"S1PR","S1PR1":"S1PR","AMYLIN":"AMYR","AMYLIN RECEPTOR":"AMYR","INSULIN RECEPTOR":"INSR","IR":"INSR",
}
def canon_target(sym):
    s = sym.strip().upper().replace("\u03b1","A")
    return TARGET_CANON.get(s, TARGET_CANON.get(s.replace(" ",""), sym.strip()))

# ---------------- parsing helpers ----------------
def parse_sales_bn(s):
    s2 = s.replace(",", "").replace("\u00a5", "JPY ").replace("\u20ac", "EUR ")
    m = re.search(r"\(\s*~?\$\s*([\d.]+)\s*B\s*\)", s2, re.I)
    if m: return float(m.group(1))
    m = re.search(r"(DKK|CHF|EUR|JPY|GBP|SEK)\s*~?\s*([\d.]+)\s*B", s2, re.I)
    if m: return round(float(m.group(2)) * FX[m.group(1).upper()], 2)
    if not re.search(r"DKK|CHF|EUR|JPY|GBP|SEK", s2, re.I):
        m = re.search(r"\$?\s*~?\s*([\d.]+)\s*B", s2, re.I)
        if m: return float(m.group(1))
        m = re.search(r"\$?~?\s*([\d.]+)\s*M\b", s2, re.I)
        if m: return round(float(m.group(1))/1000, 3)
    return None

def parse_loe(s):
    m = re.search(r"(20\d\d)", s)
    return int(m.group(1)) if m else None

def company_slugs(cell):
    main = cell.split("(")[0].strip().lower()
    partners = re.findall(r"w/\s*([A-Za-z&\- ]+?)(?:[,)]|$)", cell)
    # "Kelun-Biotech / Merck" style co-ownership -> two companies, not one phantom slug
    mains = [m.strip() for m in re.split(r"\s+/\s+", main) if m.strip()]
    out = [COMPANY_SLUG.get(m, m.replace(" ", "-")) for m in mains]
    for p in partners:
        p = p.strip().lower()
        out.append(COMPANY_SLUG.get(p, p.replace(" ", "-")))
    return out

def indications_of(used):
    u = used.lower()
    found = {ind for pat, ind in IND_RULES.items() if pat in u}
    return found or {"other"}

def table_rows(text_lines, ncols):
    rows = []
    for line in text_lines:
        line = line.strip()
        if not line.startswith("|"): continue
        body = line.replace("|", "").strip()
        if set(body) <= {"-", " ", ":"}: continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == ncols: rows.append(cells)
    return rows

# ---------------- 1. drug index (mechanical) ----------------
idx_path = os.path.join(ROOT, "reference", "02_drug_index.md")
# 7 columns since 2026-08-13: Brand | Generic | Company | Class | Used for | Status | Same molecule as
# (6-column form still parsed so older snapshots of the file don't silently yield an empty graph)
idx_lines = open(idx_path).read().splitlines()
idx_rows = [r for r in table_rows(idx_lines, 7) if r[0].lower() != "brand"]
NCOLS = 7
if not idx_rows:
    idx_rows = [r for r in table_rows(idx_lines, 6) if r[0].lower() != "brand"]
    NCOLS = 6
assert idx_rows, "drug index parsed to zero rows — column count changed again? check reference/02_drug_index.md header"

# only these statuses represent assets a company currently sells; the rest are historical/pipeline
LIVE_STATUS = {"marketed", "legacy"}
mols = {}
for r in idx_rows:
    if NCOLS == 7:
        brand, generic, company, cls, used_for, status, same_as = r
    else:
        brand, generic, company, cls, used_for, same_as = r
        status = "marketed"
    if status.strip().lower() not in LIVE_STATUS:
        continue  # withdrawn/historical/failed/pipeline drugs live in the index + graveyard, not the marketed graph
    gen = re.sub(r"\s*\(.*?\)", "", generic.lower()).strip()
    if gen in ("—", "-", ""): continue
    m = mols.setdefault(gen, {"brands": [], "companies": set(), "cls": cls, "indications": set()})
    m["brands"].append(brand)
    for s in company_slugs(company): m["companies"].add(s)
    m["indications"] |= indications_of(used_for)

brand_to_gen = {}
for gen, m in mols.items():
    for b in m["brands"]:
        brand_to_gen[re.sub(r"\s*\(.*?\)", "", b.lower()).strip()] = gen

# ---------------- 2. sales/LOE from assets tables (mechanical) ----------------
sales_loe = {}
for path in sorted(glob.glob(os.path.join(ROOT, "companies", "*.md"))):
    txt = open(path).read()
    sec = re.search(r"## Major marketed assets(.*?)## History", txt, re.S)
    if not sec: continue
    for line in sec.group(1).splitlines():
        if not line.strip().startswith("|"): continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0].lower().startswith("drug") or set("".join(cells[:2])) <= {"-",":"," "}: continue
        bm = re.match(r"([^(]+)", cells[0])
        if bm:
            sales_loe[bm.group(1).strip().strip("*").lower()] = {"sales": cells[3], "loe": cells[4]}
for gen, m in mols.items():
    best, loe = None, None
    for b in m["brands"]:
        for key in (b.lower(), b.lower().split(" / ")[0], b.split("/")[0].strip().lower()):
            if key in sales_loe:
                v = parse_sales_bn(sales_loe[key]["sales"])
                if v: best = (best or 0) + v
                loe = loe or parse_loe(sales_loe[key]["loe"])
                break
    m["sales_2025_usd_bn"] = round(best, 2) if best else None
    m["loe_year"] = loe

# ---------------- 3. cached LLM facts + TODO generation ----------------
os.makedirs(CACHE, exist_ok=True)
tpath, dpath = os.path.join(CACHE, "targets.json"), os.path.join(CACHE, "deals.json")
targets = json.load(open(tpath)) if os.path.exists(tpath) else {}
deals_by_co = json.load(open(dpath)) if os.path.exists(dpath) else {}

todo = []
missing_targets = sorted(set(mols) - set(targets))
if missing_targets:
    listing = "\n".join(f'- {g} | class: "{mols[g]["cls"]}" | used for: {", ".join(sorted(mols[g]["indications"]))}' for g in missing_targets)
    todo.append(("targets", f"""Merge the answer into graph/cache/targets.json (mapping generic -> array).
PROMPT: For each drug below, give molecular target(s) and action. Return ONLY a JSON object mapping generic name -> array of {{"target":"<canonical symbol (PD-1, GLP-1R, HER2 style)>","action":"agonist|antagonist|inhibitor|blocker|degrader|silencer|engager|binder|substitution"}}. ADCs: use antibody antigen. Bispecifics: both targets. Unclear: "unknown". No prose.
DRUGS:
{listing}"""))
covered_files = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ROOT, "companies", "*.md"))}

# --- coverage tiers: how much the KB actually knows about a company ---
#   core    = has a companies/<slug>.md deep dive (the Core 22)
#   partner = has a players/<slug>.md profile (recurring licensor/partner, one-pager)
#   cited   = appears only because a deal or an asset row names it; no KB file
_player_files = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ROOT, "players", "*.md"))} - {"README"}
def company_tier(slug):
    if slug in covered_files: return "core"
    if slug in _player_files or f"{slug}-biotech" in _player_files: return "partner"
    return "cited"

missing_deals = sorted(covered_files - set(deals_by_co))
for slug in missing_deals:
    todo.append(("deals:"+slug, f"""Merge the answer (JSON array) into graph/cache/deals.json under key "{slug}".
PROMPT: From the History+Current-bets sections of companies/{slug}.md, extract every M&A/licensing/divestiture/partnership deal. JSON array of {{"type":"acquisition|license|divestiture|partnership|spinoff","year":int|null,"counterparty":str,"value_usd_bn":float|null,"assets":[...],"role":"acquirer|seller|licensor|licensee|partner"}} from {slug}'s perspective. Only deals explicitly in text. JSON only."""))

todo_path = os.path.join(CACHE, "TODO.md")
if todo:
    with open(todo_path, "w") as f:
        f.write(f"# Extraction TODO — generated {today}\n\nFulfill each prompt with an LLM, merge JSON into the named cache file, re-run graph/extract.py, then delete this file.\n\n")
        for name, body in todo:
            f.write(f"## {name}\n\n```\n{body}\n```\n\n")
elif os.path.exists(todo_path):
    os.remove(todo_path)

# ---------------- 4. build graph ----------------
nodes, edges = [], []
all_cos = set()
for m in mols.values(): all_cos |= m["companies"]
for c in sorted(all_cos):
    nodes.append({"id": c, "kind": "company", "covered": c in covered_files,
                  "tier": company_tier(c)})
for a in sorted(set(AREA.values())): nodes.append({"id": ("other-area" if a == "other" else a), "kind": "disease_area"})
all_inds = set()
for m in mols.values(): all_inds |= m["indications"]
for ind in sorted(all_inds):
    nodes.append({"id": ind, "kind": "indication"})
    edges.append({"src": ind, "rel": "in_area", "dst": (lambda a: "other-area" if a == "other" else a)(AREA.get(ind, "other")), "etype": "fact"})
for md in sorted({mod_of(g, m["cls"]) for g, m in mols.items()}): nodes.append({"id": md, "kind": "modality"})

acts_on = []
for gen, tlist in targets.items():
    if gen not in mols: continue
    seen = set()
    for t in tlist:
        sym = canon_target(t["target"])
        if sym.lower() == "unknown" or sym in seen: continue
        seen.add(sym)
        acts_on.append((gen, sym, t.get("action", "binder")))
tgt_cos, tgt_mols = defaultdict(set), defaultdict(set)
for gen, sym, act in acts_on:
    tgt_cos[sym] |= mols[gen]["companies"]; tgt_mols[sym].add(gen)
for sym in sorted(tgt_mols): nodes.append({"id": sym, "kind": "target"})

for gen, m in sorted(mols.items()):
    nodes.append({"id": gen, "kind": "molecule", "brands": m["brands"], "class": m["cls"],
                  "modality": mod_of(gen, m["cls"]), "sales_2025_usd_bn": m["sales_2025_usd_bn"],
                  "loe_year": m["loe_year"], "phase": "marketed"})
    edges.append({"src": gen, "rel": "has_modality", "dst": mod_of(gen, m["cls"]), "etype": "fact"})
    for c in sorted(m["companies"]):
        edges.append({"src": c, "rel": "owns", "dst": gen, "etype": "fact",
                      "note": "co-owned/partnered" if len(m["companies"]) > 1 else None})
    for ind in sorted(m["indications"]):
        edges.append({"src": gen, "rel": "treats", "dst": ind, "etype": "fact"})
for gen, sym, act in acts_on:
    edges.append({"src": gen, "rel": "acts_on", "dst": sym, "action": act, "etype": "fact"})

i = 0
for slug, dlist in sorted(deals_by_co.items()):
    for d in dlist:
        did = f"deal-{slug}-{d.get('year') or 'na'}-{i}"; i += 1
        nodes.append({"id": did, "kind": "deal", "type": d["type"], "year": d.get("year"),
                      "value_usd_bn": d.get("value_usd_bn"), "counterparty": d.get("counterparty"),
                      "assets": (d.get("assets") or None), "role": d.get("role")})
        edges.append({"src": slug, "rel": "party_to", "dst": did, "role": d.get("role"), "etype": "fact"})
        for a in d.get("assets") or []:
            a_low = str(a).lower().strip()
            # match strategies: exact generic; parenthetical generic "Brand (generic)"; brand name
            gen = None
            if a_low in mols:
                gen = a_low
            else:
                pm = re.search(r"\(([^)]+)\)", a_low)
                if pm and pm.group(1).strip() in mols:
                    gen = pm.group(1).strip()
                else:
                    bare = re.sub(r"\s*\(.*?\)", "", a_low).strip()
                    gen = brand_to_gen.get(bare) or (bare if bare in mols else None)
            if gen:
                edges.append({"src": gen, "rel": "acquired_via" if d["type"] == "acquisition" else "via",
                              "dst": did, "etype": "fact"})

by_ind = defaultdict(list)
for gen, m in mols.items():
    for ind in m["indications"]:
        if ind != "other": by_ind[ind].append(gen)
for ind, gens in by_ind.items():
    for x in range(len(gens)):
        for y in range(x + 1, len(gens)):
            a, b = sorted([gens[x], gens[y]])
            if mols[a]["companies"] != mols[b]["companies"]:
                edges.append({"src": a, "rel": "competes_with", "dst": b,
                              "basis": f"shared_indication:{ind}", "etype": "derived"})

# ---------------- 4b. graveyard: failed assets as nodes + failed_on edges ----------------
gy_path = os.path.join(ROOT, "graph", "cache", "graveyard.json")
gy_failed_on = defaultdict(set)   # target -> set(dead molecules), for convergence denominators
if os.path.exists(gy_path):
    gy = json.load(open(gy_path))
    tgt_node_ids = {n["id"] for n in nodes if n["kind"] == "target"}
    for key, g in sorted(gy.items()):
        if g.get("scope") != "program-death":
            continue  # indication-level failures of marketed drugs stay registry-only
        if key in mols:
            continue  # safety net: never mark a marketed molecule dead
        # graveyard records carry free-text modality ("bispecific (HLE BiTE)", "mAb") —
        # map it through the same vocabulary so dead assets are comparable to live ones
        nodes.append({"id": key, "kind": "molecule", "phase": "failed",
                      "modality": mod_of(key, g.get("modality") or ""),
                      "modality_note": g.get("modality"), "year_died": g.get("year_died"),
                      "failure_mode": g.get("failure_mode")})
        _md = mod_of(key, g.get("modality") or "")
        if _md != "unclassified":
            if not any(n["id"] == _md and n["kind"] == "modality" for n in nodes):
                nodes.append({"id": _md, "kind": "modality"})
            edges.append({"src": key, "rel": "has_modality", "dst": _md, "etype": "fact"})
        tgt = (g.get("target") or "").strip()
        if tgt and tgt.lower() not in ("unknown", "none", "", "—", "null"):
            # strip action words so "GLP-1R agonist" lands on the marketed GLP-1R node
            t = re.sub(r"\s*\(.*?\)", "", tgt)
            t = re.sub(r"\b(agonist|antagonist|inhibitor|blocker|antibody|receptor antagonist|dual|selective|oral)\b",
                       "", t, flags=re.I).strip(" -/")
            # bispecific engager deaths: attribute to the tumor-antigen arm, not CD3
            t = re.sub(r"\s*x\s*CD3$", "", t, flags=re.I).strip()
            sym = canon_target(t if t else tgt.split("(")[0].strip())
            if sym not in tgt_node_ids:
                nodes.append({"id": sym, "kind": "target"}); tgt_node_ids.add(sym)
            edges.append({"src": key, "dst": sym, "rel": "failed_on", "etype": "fact",
                          "year": g.get("year_died"), "mode": g.get("failure_mode")})
            gy_failed_on[sym].add(key)

with open(os.path.join(ROOT, "graph", "nodes.jsonl"), "w") as f:
    for n in nodes: f.write(json.dumps({k: v for k, v in n.items() if v is not None}) + "\n")
with open(os.path.join(ROOT, "graph", "edges.jsonl"), "w") as f:
    for e in edges: f.write(json.dumps({k: v for k, v in e.items() if v is not None}) + "\n")

# ---------------- 5. target convergence reference ----------------
conv_path = os.path.join(ROOT, "reference", "03_target_convergence.md")
top = sorted(tgt_cos.items(), key=lambda kv: (-len(kv[1]), -len(tgt_mols[kv[0]])))
out = [f"""---
type: reference
updated: {today}
status: generated
---
# Target convergence — where the industry piles up

**Generated by `graph/extract.py` from marketed assets of the {len(covered_files)} covered companies. Do not hand-edit; regenerate after curation passes.** A target with many companies on it = a validated mechanism that attracted me-too competition; crowded node = competition on molecule properties, not biology. "First-in-class" = alone on a node.

**Dead column = survivorship denominator** (clinical-stage program deaths on this target, from `reference/05_graveyard.md`). A 4-marketed/0-dead target (validated cheaply, e.g. by human genetics) is a different bet than 2-marketed/20-dead (amyloid). Registry is representative, not exhaustive — treat counts as floors.

| Target | Companies | Assets (generic names) | Dead | Notes |
|---|---|---|---|---|"""]
for sym, cos in top:
    if len(cos) < 2 and len(tgt_mols[sym]) < 2: continue
    ndead = len(gy_failed_on.get(sym, ()))
    out.append(f"| {sym} | {len(cos)}: {', '.join(sorted(cos))} | {', '.join(sorted(tgt_mols[sym]))} | {ndead or ''} |  |")

# graveyard-only targets with 2+ corpses deserve a row too (the anti-convergence list)
dead_only = sorted(((s, ms) for s, ms in gy_failed_on.items() if s not in tgt_mols and len(ms) >= 2),
                   key=lambda kv: -len(kv[1]))
if dead_only:
    out.append("\n**Graveyard-only targets (2+ program deaths, zero marketed assets among covered companies)** — mechanisms the industry tried and abandoned:\n")
    out.append("| Target | Dead | Failed molecules |")
    out.append("|---|---|---|")
    for sym, ms in dead_only:
        out.append(f"| {sym} | {len(ms)} | {', '.join(sorted(ms))} |")
out.append(f"""
*Marketed assets only — pipeline extraction pending. Molecules: {len(mols)} | targets: {len(tgt_mols)} | deals: {sum(len(v) for v in deals_by_co.values())} | rebuilt {today}.*""")
open(conv_path, "w").write("\n".join(out))

# ---------------- 6. lint report ----------------
print(f"graph rebuilt {today}: {len(nodes)} nodes {dict(Counter(n['kind'] for n in nodes))}")
print(f"                {len(edges)} edges")
print("\nLINT")
if todo: print(f"  [ACTION] {len(todo)} LLM extraction task(s) pending -> graph/cache/TODO.md")
unmapped = [g for g, m in mols.items() if m["indications"] == {"other"}]
print(f"  molecules with unmapped indication ({len(unmapped)}): {unmapped[:8]}")
no_sales = [g for g, m in mols.items() if m["sales_2025_usd_bn"] is None]
print(f"  molecules with no sales figure: {len(no_sales)}")
no_tgt = sorted(set(mols) - {g for g, _, _ in acts_on})
print(f"  molecules with no target edge ({len(no_tgt)}): {no_tgt[:8]}")
player_files = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ROOT, "players", "*.md"))} - {"README"}
def has_profile(c):
    # "genmab-/-pfizer" style composites count as covered if any component has a file
    parts = [p for p in re.split(r"-/-|/", c) if p]
    return all(p in covered_files or p in player_files for p in parts)
uncovered = sorted(c for c in all_cos if c not in covered_files and not has_profile(c))
print(f"  partner companies with neither deep-dive nor players/ profile: {uncovered}")
# staleness: company files not updated in >180 days
stale = []
for path in glob.glob(os.path.join(ROOT, "companies", "*.md")):
    fm = re.search(r"updated:\s*(\d{4}-\d{2}-\d{2})", open(path).read())
    if fm:
        age = (datetime.date.today() - datetime.date.fromisoformat(fm.group(1))).days
        if age > 180: stale.append((os.path.basename(path), age))
print(f"  stale company files (>180d): {stale or 'none'}")
# pronunciation coverage
pron = open(os.path.join(ROOT, "audio", "pronunciation.md")).read().lower()
missing_pron = [g for g in mols if len(g) > 9 and g.split()[0] not in pron][:10]
print(f"  long generics possibly missing pronunciation: {missing_pron or 'none'}")
