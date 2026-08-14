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

# c) status vs graph membership: only marketed/legacy belong in the marketed graph
idx_status = {}
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
        idx_status.setdefault(re.sub(r"\s*\(.*?\)", "", c[1].lower()).strip(), set()).add(c[5])
wrong_tier = {g for g in mol if idx_status.get(g) and not (idx_status[g] & {"marketed", "legacy"})
              and mol[g].get("phase") != "failed"}
if wrong_tier:
    add("ERROR", "status-graph-mismatch",
        "molecule is in the marketed graph but the index says it is not marketed/legacy", wrong_tier)

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
