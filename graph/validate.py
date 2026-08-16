#!/usr/bin/env python3
"""validate.py — correctness checks over the derived graph.

Usage (from repo root):
    python3 graph/validate.py            # human-readable report
    python3 graph/validate.py --json     # machine-readable, for agents
    python3 graph/validate.py --strict   # exit 1 if any ERROR-level check fails

Philosophy: the dangerous failure mode in this KB is not a missing fact, it is a
WRONG fact that looks like a fact. Catch-all buckets ("other", "unknown",
"unclassified", silent defaults) are where wrong facts hide, because a default
value is indistinguishable from a researched one downstream. So:

  ERROR    — an assertion the graph makes that is probably false, or a broken
             invariant (dangling edge, contradictory status). Fix before trusting.
  WARN     — an honest gap (unclassified/other) that should shrink over time.
             Never silently upgraded to a guess.
  INFO     — coverage statistics, no action implied.

Every check names the offending ids so a curation pass can act without re-deriving.
"""
import json, os, re, sys, glob
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, "graph")
nodes = [json.loads(l) for l in open(os.path.join(G, "nodes.jsonl"))]
edges = [json.loads(l) for l in open(os.path.join(G, "edges.jsonl"))]
by_id = {n["id"]: n for n in nodes}
mol = {n["id"]: n for n in nodes if n["kind"] == "molecule"}

override_path = os.path.join(G, "cache", "modality_overrides.json")
modality_overrides = json.load(open(override_path)) if os.path.exists(override_path) else {}
graveyard_path = os.path.join(G, "cache", "graveyard.json")
graveyard = json.load(open(graveyard_path)) if os.path.exists(graveyard_path) else {}

findings = []  # (level, check, message, ids)
def add(level, check, msg, ids=()):
    findings.append({"level": level, "check": check, "message": msg,
                     "ids": sorted(ids)[:40], "n": len(ids) if ids else 0})

# ---------------------------------------------------------------- structural
dangling = {e["src"] for e in edges if e["src"] not in by_id} | {e["dst"] for e in edges if e["dst"] not in by_id}
if dangling:
    add("ERROR", "dangling-edges", "edges reference node ids that do not exist", dangling)

dupe_ids = [i for i, c in Counter(n["id"] for n in nodes).items() if c > 1]
if dupe_ids:
    add("ERROR", "duplicate-node-ids", "same id appears as multiple nodes", dupe_ids)

self_loops = {e["src"] for e in edges if e["src"] == e["dst"]}
if self_loops:
    add("ERROR", "self-loops", "node related to itself", self_loops)

# ---------------------------------------------------------------- catch-all buckets (the point of this script)
unclassified_mod = {g for g, n in mol.items() if n.get("modality") in (None, "unclassified")}
if unclassified_mod:
    add("WARN", "modality-unclassified",
        "molecules whose modality could not be determined from their class text — "
        "resolve in graph/cache/modality_overrides.json (NEVER let these default to small-molecule)",
        unclassified_mod)

modality_edges = defaultdict(set)
invalid_modality_endpoints = set()
for e in edges:
    if e["rel"] != "has_modality":
        continue
    modality_edges[e["src"]].add(e["dst"])
    if e["src"] not in mol or by_id.get(e["dst"], {}).get("kind") != "modality":
        invalid_modality_endpoints.add(f"{e['src']} -> {e['dst']}")
if invalid_modality_endpoints:
    add("ERROR", "modality-edge-invalid-endpoints",
        "has_modality edges must connect a molecule to a modality node",
        invalid_modality_endpoints)

modality_edge_mismatch = set()
for g, n in mol.items():
    expected = n.get("modality")
    observed = modality_edges.get(g, set())
    # Failed graveyard entries with unknown format intentionally omit the edge.
    if expected == "unclassified" and not observed:
        continue
    if observed != {expected}:
        modality_edge_mismatch.add(
            f"{g} [node={expected}; edges={','.join(sorted(observed)) or 'none'}]"
        )
if modality_edge_mismatch:
    add("ERROR", "modality-node-edge-mismatch",
        "molecule modality field and has_modality edge disagree",
        modality_edge_mismatch)

# Overrides are exceptional assertions, not an unreviewed second classifier.
# Require an inspectable source for every one, and make sure non-molecule
# graveyard entities can never leak into the molecule graph.
bad_override_schema = set()
orphan_overrides = set()
missing_override_sources = set()
for generic, record in modality_overrides.items():
    if (not isinstance(record, dict) or not record.get("modality")
            or not record.get("source") or not record.get("evidence")):
        bad_override_schema.add(generic)
    if generic not in mol:
        orphan_overrides.add(generic)
    if isinstance(record, dict):
        source = record.get("source", "")
        if source and not source.startswith(("http://", "https://")) and not os.path.exists(os.path.join(ROOT, source)):
            missing_override_sources.add(f"{generic} [{source}]")
if bad_override_schema:
    add("ERROR", "modality-override-missing-provenance",
        "every modality override must contain modality, source, and evidence", bad_override_schema)
if orphan_overrides:
    add("ERROR", "modality-override-orphan",
        "modality override does not correspond to a molecule node", orphan_overrides)
if missing_override_sources:
    add("ERROR", "modality-override-source-missing",
        "modality override cites a repository source path that does not exist",
        missing_override_sources)

non_molecule_graveyard_nodes = {
    generic for generic, record in graveyard.items()
    if record.get("entity_type", "molecule") != "molecule" and generic in mol
}
if non_molecule_graveyard_nodes:
    add("ERROR", "non-molecule-modeled-as-molecule",
        "trial, platform, or programme-family graveyard entry became a molecule node",
        non_molecule_graveyard_nodes)

treats = defaultdict(set)
for e in edges:
    if e["rel"] == "treats": treats[e["src"]].add(e["dst"])
only_other = {g for g in mol if treats.get(g) == {"other"}}
no_ind = {g for g in mol if g not in treats}
if only_other:
    add("WARN", "indication-other-only",
        "molecules whose ONLY indication is the catch-all 'other' — add an IND_RULES pattern "
        "or fix the drug-index 'Used for' cell", only_other)
if no_ind:
    add("WARN", "indication-missing", "molecules with no indication at all", no_ind)

acts = defaultdict(set)
for e in edges:
    if e["rel"] == "acts_on": acts[e["src"]].add(e["dst"])
no_target = {g for g in mol if g not in acts and mol[g].get("modality") not in ("vaccine", "plasma-derived", "immunoglobulin")}
if no_target:
    add("WARN", "target-missing",
        "molecules with no target edge (vaccines/plasma products exempt) — fulfil graph/cache/TODO.md",
        no_target)

# ---------------------------------------------------------------- semantic plausibility
# a) modality vs name morphology: -mab/-cept/-tide etc. must not be small molecules
STEM_MODALITY = [
    (r"\w+mab\b", {"mab", "bispecific-ab", "adc", "biosimilar"}),
    (r"\w+cept\b", {"fusion-protein", "biosimilar"}),
    (r"\w+(tide|glutide)\b", {"peptide", "aso", "sirna", "hormone", "small-molecule"}),  # -parin = heparins (small molecule/polysaccharide)
    (r"\w+(leucel|cabtagene)\b", {"cell-therapy", "gene-therapy", "gene-editing"}),
    (r"\w+(tinib|ciclib|parib|prazole|sartan|statin|vastatin)\b", {"small-molecule", "formulation-smallmolecule"}),
    (r"\w+xaban\b", {"small-molecule", "formulation-smallmolecule"}),
]
bad_mod = set()
for g, n in mol.items():
    m = n.get("modality")
    if not m:
        continue
    for pat, allowed in STEM_MODALITY:
        if "lutetium" in g or "radio" in n.get("class","").lower(): break  # radioligands carry peptide-like names
        if re.search(pat, g) and m not in allowed:
            bad_mod.add(f"{g} [{m}]")
if bad_mod:
    add("ERROR", "modality-contradicts-stem",
        "generic-name stem implies a different modality (e.g. -mab labelled small-molecule)", bad_mod)

# b) biologic-sounding class text labelled small-molecule (the Cuvitru bug)
BIO_HINT = re.compile(r"globulin|immunoglob|plasma-derived|albumin|coagulation|clotting|recombinant|"
                      r"interferon|interleukin|colony-stimulating|growth hormone|neurotoxin|polyclonal|"
                      r"monoclonal|antibody|cell therapy|gene therapy|mrna|oligonucleotide", re.I)
bio_as_sm = {g for g, n in mol.items()
             if n.get("modality") == "small-molecule" and BIO_HINT.search(n.get("class", ""))}
if bio_as_sm:
    add("ERROR", "biologic-labelled-small-molecule",
        "class text describes a biologic but modality says small-molecule", bio_as_sm)

# c) explicit small-molecule class text labelled as a biologic or other format.
# This is the reverse of the check above. It catches rule-order failures where a
# pathway word wins over an explicit molecular-format statement, as happened for
# eltrombopag ("Small molecule (thrombopoietin receptor agonist)" -> cytokine).
explicit_sm_mismatch = {
    f"{g} [{n.get('modality')}]" for g, n in mol.items()
    if re.search(r"\bsmall[- ]molecule\b", n.get("class", ""), re.I)
    and n.get("modality") not in ("small-molecule", "formulation-smallmolecule")
}
if explicit_sm_mismatch:
    add("ERROR", "explicit-small-molecule-mismatch",
        "class text explicitly says small molecule but graph modality disagrees",
        explicit_sm_mismatch)

# e) independent source-to-graph modality census. These patterns intentionally
# overlap the extractor only at the conceptual level. The validator reasons from
# explicit format phrases in the source text, so a bad override and matching bad
# node/edge cannot validate one another.
SOURCE_MODALITY_ASSERTIONS = [
    (r"\b(?:antibody[- ]drug conjugate|adc\b|dxd antibody|directed adc)", {"adc"}),
    (r"\b(?:bispecific|trispecific|bite\b|t[- ]cell engager)", {"bispecific-ab"}),
    (r"\b(?:gene[- ]edited|gene editing|crispr)", {"gene-editing"}),
    (r"\b(?:car[- ]?t|cell therapy|stem[- ]cell[- ]derived)", {"cell-therapy"}),
    (r"\b(?:mrna|rna-lnp)", {"mrna"}),
    (r"\b(?:sirna|rnai)", {"sirna"}),
    (r"\b(?:antisense|oligonucleotide)", {"aso"}),
    (r"\b(?:gene therapy|aav\d*\b)", {"gene-therapy"}),
    (r"\b(?:radioligand|radiopharmaceutical|radioconjugate)", {"radioligand"}),
    (r"\b(?:vaccine|active immunization|viral vector)", {"vaccine"}),
    (r"\bbiosimilar\b", {"biosimilar"}),
    (r"\b(?:immunoglobulin|immune globulin)", {"immunoglobulin"}),
    (r"\b(?:plasma[- ]derived|albumin)", {"plasma-derived"}),
    (r"\b(?:monoclonal antibody|mab\b|antibody\b|fab\b)", {"mab"}),
    (r"\b(?:fusion protein|peptibody|receptor fusion|ligand trap)", {"fusion-protein"}),
    (r"\b(?:enzyme replacement|pegylated enzyme|enzyme\b)", {"enzyme"}),
    (r"\b(?:recombinant factor (?:viii|viia|ix|x)\b|factor viii(?:-|\s)|antihemophilic factor)",
     {"clotting-factor"}),
    (r"\b(?:inhaled protein|recombinant(?:\s+\w+){0,4}\s+protein|protein analogue)",
     {"recombinant-protein"}),
    (r"\b(?:peptide|insulin|amylin|natriuretic)", {"peptide"}),
    (r"\bsmall[- ]molecule\b", {"small-molecule", "formulation-smallmolecule"}),
]

def source_modality_assertion(text):
    for pattern, allowed in SOURCE_MODALITY_ASSERTIONS:
        if re.search(pattern, text or "", re.I):
            return allowed
    return None

source_modality_conflicts = set()
override_source_conflicts = set()
for generic, node in mol.items():
    source_text = node.get("class") or node.get("modality_note") or ""
    allowed = source_modality_assertion(source_text)
    if generic.endswith("xaban"):
        allowed = {"small-molecule", "formulation-smallmolecule"}
    if allowed and node.get("modality") not in allowed:
        source_modality_conflicts.add(
            f"{generic} [{node.get('modality')}; source={source_text}]"
        )
    record = modality_overrides.get(generic)
    if allowed and isinstance(record, dict) and record.get("modality") not in allowed:
        override_source_conflicts.add(
            f"{generic} [{record.get('modality')}; source={source_text}]"
        )
if source_modality_conflicts:
    add("ERROR", "modality-contradicts-source-format",
        "explicit source format disagrees with generated molecule modality",
        source_modality_conflicts)
if override_source_conflicts:
    add("ERROR", "modality-override-contradicts-source",
        "manual override contradicts explicit source format",
        override_source_conflicts)

# d) status vs graph membership: only marketed/legacy belong in the marketed graph
idx_status = {}
idx_used_for = defaultdict(set)
idx_path = os.path.join(ROOT, "reference", "02_drug_index.md")
for line in open(idx_path):
    s = line.strip()
    if not s.startswith("|") or s.startswith("| Brand"):
        continue
    body = s.replace("|", "").strip()
    if set(body) <= {"-", ":", " "}:
        continue
    c = [x.strip() for x in s.strip("|").split("|")]
    if len(c) == 7:
        generic = re.sub(r"\s*\(.*?\)", "", c[1].lower()).strip()
        idx_status.setdefault(generic, set()).add(c[5])
        idx_used_for[generic].add(c[4].lower())

# d1) indication semantics that naive substring matching has previously broken.
# A bipolar-depression phrase describes bipolar disorder, not unipolar
# depression. A separate major/standalone depression clause may legitimately
# produce both edges, so strip bipolar phrases before looking for that evidence.
BIPOLAR_PHRASE = re.compile(
    r"\bbipolar(?:\s+[ivx]+)?(?:\s+(?:disorder|depression))?\b", re.I
)
bipolar_as_depression = set()
bronchitis_fallback = set()
for generic, cells in idx_used_for.items():
    used_for = "; ".join(sorted(cells))
    without_bipolar = BIPOLAR_PHRASE.sub("", used_for)
    if ("bipolar" in used_for and "depression" in treats.get(generic, set())
            and "depress" not in without_bipolar):
        bipolar_as_depression.add(generic)
    if "bronchitis" in used_for and (
            "bronchitis" not in treats.get(generic, set())
            or "other" in treats.get(generic, set())):
        bronchitis_fallback.add(generic)
if bipolar_as_depression:
    add("ERROR", "bipolar-collapsed-to-depression",
        "bipolar terminology without a separate depression indication generated a depression edge",
        bipolar_as_depression)
if bronchitis_fallback:
    add("ERROR", "bronchitis-mapped-to-other",
        "drug-index text explicitly names bronchitis but the graph omits bronchitis or retains other",
        bronchitis_fallback)

LIVE = {"marketed", "legacy", "pipeline"}
wrong_tier = {g for g in mol if idx_status.get(g) and not (idx_status[g] & LIVE)
              and mol[g].get("phase") != "failed"}
if wrong_tier:
    add("ERROR", "status-graph-mismatch",
        "molecule is in the live graph but the index says it is not marketed/legacy/pipeline", wrong_tier)

# c2) phase must agree with the curated index status — the graph must never ASSERT approval.
# This is the check that would have caught 17 trial-stage assets being labelled "marketed".
phase_lie = {g for g, n in mol.items()
             if idx_status.get(g) and n.get("phase") in ("marketed", "legacy")
             and idx_status[g] == {"pipeline"}}
if phase_lie:
    add("ERROR", "phase-asserts-approval",
        "graph says marketed/legacy but the drug index says the asset is still pipeline", phase_lie)

# c3) vocabulary guard: an unrecognised phase means someone added a value without
# teaching the consumers (explorer colouring, convergence table) about it.
bad_phase = {g for g, n in mol.items() if n.get("phase") not in (LIVE | {"failed"})}
if bad_phase:
    add("ERROR", "unknown-phase", "molecule phase outside the controlled vocabulary", bad_phase)

import glob as _glob

# c5) sales that exist in a company assets table but never reached the graph.
# The failure mode this catches: the drug index and the company tables spell multi-brand
# entries differently ("Darzalex / Darzalex Faspro" vs "Darzalex/Darzalex Faspro"), so a
# raw string comparison silently dropped 22 sales figures — including J&J's largest
# product, which then rendered smaller than Stelara. Node SIZE encodes sales, so a missed
# match is not a blank field, it is a visibly WRONG picture.
def _brand_keys(s):
    s = re.sub(r"\s*\(.*?\)", "", str(s)).strip().strip("*").lower()
    s = re.sub(r"\s+franchise$", "", s)
    flat = re.sub(r"\s*([/+])\s*", r"\1", s)
    keys = {s, flat} | {p.strip() for p in re.split(r"[/+]", flat) if len(p.strip()) > 2}
    return {k for k in keys if k}

_prose_sales = {}
for _p in _glob.glob(os.path.join(ROOT, "companies", "*.md")):
    _sec = re.search(r"## Major marketed assets(.*?)## (?:Pipeline|History)", open(_p).read(), re.S)
    if not _sec:
        continue
    for _line in _sec.group(1).splitlines():
        _s = _line.strip()
        if not _s.startswith("|"):
            continue
        _c = [x.strip() for x in _s.strip("|").split("|")]
        if len(_c) < 5 or _c[0].lower().startswith("drug"):
            continue
        if not re.search(r"[\d.]+\s*[BM]\b", _c[3]):
            continue          # genuinely undisclosed — not a defect
        for _k in _brand_keys(re.match(r"([^(]+)", _c[0]).group(1) if re.match(r"([^(]+)", _c[0]) else _c[0]):
            _prose_sales[_k] = _c[3]

_graph_keys = set()
for _g, _n in mol.items():
    if _n.get("sales_2025_usd_bn"):
        for _b in (_n.get("brands") or [_g]):
            _graph_keys |= _brand_keys(_b)
lost_sales = {k for k in _prose_sales if k not in _graph_keys}
# only report the head of each multi-brand group to keep the list readable
lost_sales = {k for k in lost_sales if not any(k != o and k in o for o in lost_sales)}
if lost_sales:
    add("WARN", "sales-in-prose-not-in-graph",
        "company assets table states a sales figure the graph did not pick up", lost_sales)

# c4) coverage: pipeline assets named in prose but absent from the graph. A warn, counted
# so it shrinks — the KB's job is to make strategic bets queryable, not just readable.
prose_assets = set()
for _p in _glob.glob(os.path.join(ROOT, "companies", "*.md")):
    _t = open(_p).read()
    _m = re.search(r"## Pipeline \(clinical-stage\)(.*?)(?=\n## )", _t, re.S)
    if not _m:
        continue
    for _line in _m.group(1).splitlines():
        _s = _line.strip()
        if not _s.startswith("|") or _s.lower().startswith("| asset"):
            continue
        if set(_s.replace("|", "").strip()) <= {"-", ":", " "}:
            continue
        _c = [x.strip() for x in _s.strip("|").split("|")]
        if len(_c) >= 2 and _c[1] not in ("—", "-", ""):
            prose_assets.add(re.sub(r"\s*\(.*?\)", "", _c[1].lower()).strip())
missing_pipe = {a for a in prose_assets if a not in mol}
if missing_pipe:
    add("WARN", "pipeline-not-in-graph",
        "asset in a company Pipeline table has no graph node (add a drug-index row)", missing_pipe)

# d) failed molecules must not carry sales
failed_with_sales = {g for g, n in mol.items() if n.get("phase") == "failed" and n.get("sales_2025_usd_bn")}
if failed_with_sales:
    add("ERROR", "failed-with-sales", "graveyard molecule carries 2025 sales", failed_with_sales)

# e) ownerless molecules
owned = {e["dst"] for e in edges if e["rel"] == "owns"}
orphan = {g for g in mol if g not in owned and mol[g].get("phase") != "failed"}
if orphan:
    add("ERROR", "molecule-without-owner", "marketed molecule has no owning company", orphan)

# f) target symbol hygiene: near-duplicate symbols suggest an un-merged alias
targets = sorted({n["id"] for n in nodes if n["kind"] == "target"})
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
groups = defaultdict(list)
for t_ in targets:
    groups[norm(t_)].append(t_)
alias_suspects = {" / ".join(v) for v in groups.values() if len(v) > 1}
# also: a bare acronym that is a prefix-word of a longer symbol (IN vs HIV integrase won't catch, but AR vs AR-V7 will)
if alias_suspects:
    add("ERROR", "target-alias-duplicates",
        "target symbols that normalise to the same string — merge in TARGET_CANON", alias_suspects)

cryptic = {t_ for t_ in targets if len(t_) <= 3 and t_.isupper() and t_ not in
           {"AR", "ER", "PR", "GR", "MET", "RET", "KIT", "ALK", "BTK", "NET", "TPO", "CD3", "CD19", "CD20", "CD38"}}
if cryptic:
    add("WARN", "target-cryptic-symbol",
        "very short target symbols that a reader may not decode — consider spelling out", cryptic)

# g) tier discipline: cited companies should not look researched
cited = {n["id"] for n in nodes if n["kind"] == "company" and n.get("tier") == "cited"}
cited_rich = {c for c in cited if sum(1 for e in edges if e["rel"] == "owns" and e["src"] == c) >= 3}
if cited_rich:
    add("WARN", "cited-company-with-assets",
        "company has no KB file but owns 3+ assets in the graph — promote to players/", cited_rich)

# ---------------------------------------------------------------- coverage info
add("INFO", "counts", "node/edge census", ())
findings[-1]["detail"] = {"nodes": len(nodes), "edges": len(edges),
                          "by_kind": dict(Counter(n["kind"] for n in nodes)),
                          "by_rel": dict(Counter(e["rel"] for e in edges))}
n_mol = len(mol)
add("INFO", "completeness", "share of molecules with each attribute", ())
findings[-1]["detail"] = {
    "with_modality": round(sum(1 for n in mol.values() if n.get("modality") not in (None, "unclassified")) / n_mol, 3),
    "with_target": round(sum(1 for g in mol if g in acts) / n_mol, 3),
    "with_real_indication": round(sum(1 for g in mol if treats.get(g, set()) - {"other"}) / n_mol, 3),
    "with_sales": round(sum(1 for n in mol.values() if n.get("sales_2025_usd_bn")) / n_mol, 3),
}

# ---------------------------------------------------------------- output
if "--json" in sys.argv:
    print(json.dumps(findings, indent=1))
else:
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for f in sorted(findings, key=lambda x: order[x["level"]]):
        head = f"[{f['level']}] {f['check']}"
        if f["n"]:
            head += f" ({f['n']})"
        print(head)
        print(f"    {f['message']}")
        if f.get("detail"):
            print(f"    {json.dumps(f['detail'])}")
        if f["ids"]:
            shown = ", ".join(str(i) for i in f["ids"][:12])
            print(f"    e.g. {shown}" + (" …" if f["n"] > 12 else ""))
    errs = sum(1 for f in findings if f["level"] == "ERROR")
    warns = sum(1 for f in findings if f["level"] == "WARN")
    print(f"\n{errs} error check(s), {warns} warn check(s) triggered.")

if "--strict" in sys.argv and any(f["level"] == "ERROR" for f in findings):
    sys.exit(1)
