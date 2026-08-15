#!/usr/bin/env python3
"""build_overview.py — regenerate graph/overview.png from the graph. Deterministic, no LLM.

Usage (from repo root):  python3 graph/build_overview.py
Requires matplotlib. Companies (left) linked to the most crowded targets (right),
with graveyard counts annotated — the static companion to explorer.html.
"""
import json, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, "graph")
MIN_COMPANIES = 4      # a target is "crowded" at this many owners
TOP_N = 14

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit("build_overview.py needs matplotlib (pip install matplotlib)")

nodes = [json.loads(l) for l in open(os.path.join(G, "nodes.jsonl"))]
edges = [json.loads(l) for l in open(os.path.join(G, "edges.jsonl"))]
mol = {n["id"]: n for n in nodes if n["kind"] == "molecule"}
display = {n["id"]: n.get("display") for n in nodes if n["kind"] == "company"}

DISPLAY = {
    "amgen": "Amgen", "astrazeneca": "AstraZeneca", "bristol-myers-squibb": "Bristol Myers Squibb",
    "eli-lilly": "Eli Lilly", "johnson-and-johnson": "Johnson & Johnson", "novo-nordisk": "Novo Nordisk",
    "boehringer-ingelheim": "Boehringer Ingelheim", "daiichi-sankyo": "Daiichi Sankyo", "gsk": "GSK",
    "pfizer": "Pfizer", "merck": "Merck & Co.", "roche": "Roche", "novartis": "Novartis", "sanofi": "Sanofi",
    "abbvie": "AbbVie", "takeda": "Takeda", "gilead": "Gilead", "bayer": "Bayer", "vertex": "Vertex",
    "regeneron": "Regeneron", "biogen": "Biogen", "moderna": "Moderna", "legend": "Legend Biotech",
    "arcellx": "Arcellx", "genmab": "Genmab", "ionis": "Ionis", "akeso": "Akeso",
    "hansoh-pharma": "Hansoh Pharma", "kelun-biotech": "Kelun-Biotech", "3sbio": "3SBio",
    "zealand-pharma": "Zealand Pharma", "biontech": "BioNTech", "autolus": "Autolus",
    "summit": "Summit Therapeutics",
}
def disp(s):
    return DISPLAY.get(s, s.replace("-", " ").title())

owned_by = defaultdict(list)
acts, failed_on = defaultdict(set), defaultdict(set)
for e in edges:
    if e["rel"] == "owns":
        owned_by[e["dst"]].append(e["src"])
    elif e["rel"] == "acts_on":
        acts[e["dst"]].add(e["src"])
    elif e["rel"] == "failed_on":
        failed_on[e["dst"]].add(e["src"])

tgt_cos = {}
for t, gens in acts.items():
    live = [g for g in gens if mol.get(g, {}).get("phase") != "failed"]
    cos = {c for g in live for c in owned_by[g]}
    if len(cos) >= MIN_COMPANIES:
        tgt_cos[t] = cos
top = sorted(tgt_cos.items(), key=lambda kv: (len(kv[1]), kv[0]))[-TOP_N:]
if not top:
    sys.exit("no targets meet the crowding threshold — nothing to plot")

companies = sorted({c for _, cos in top for c in cos})
cy = {c: i for i, c in enumerate(companies)}
step = max(1, len(companies) - 1) / max(1, len(top) - 1)
ty = {t: i * step for i, (t, _) in enumerate(top)}

fig, ax = plt.subplots(figsize=(11, 8.5))
# Draw order must be sorted: iterating the set `cos` varies with the hash seed, and
# antialiasing blends differently where lines cross — the PNG pixels then differ between
# runs on identical data. Sorted iteration keeps the file byte-stable.
for t, cos in top:
    for c in sorted(cos):
        ax.plot([0, 1], [cy[c], ty[t]], color="#b9c6d2", lw=0.6, alpha=0.65, zorder=1)
for c in companies:
    ax.scatter([0], [cy[c]], s=42, color="#1f77b4", zorder=3)
    ax.text(-0.02, cy[c], disp(c), ha="right", va="center", fontsize=8)
for t, cos in top:
    dead = len(failed_on.get(t, ()))
    ax.scatter([1], [ty[t]], s=52 + len(cos) * 12, color="#d62728", zorder=3)
    lbl = f"{t}  ({len(cos)} companies" + (f" · {dead} failed" if dead else "") + ")"
    ax.text(1.02, ty[t], lbl, ha="left", va="center", fontsize=8)

ax.set_xlim(-0.42, 1.55)
ax.set_ylim(-1.2, max(len(companies), len(top)) + 0.4)
ax.invert_yaxis()
ax.axis("off")
ax.set_title("Target convergence: companies (left) with marketed assets on the industry's most crowded targets (right)",
             fontsize=10, loc="left", pad=14)
ax.text(0, 1.0, f"Node size = number of companies on the target · 'failed' counts clinical program deaths "
                f"on that target (graveyard registry) · threshold: \u2265{MIN_COMPANIES} companies",
        transform=ax.transAxes, fontsize=6.5, color="#666", va="bottom")
fig.tight_layout()
out = os.path.join(G, "overview.png")
# matplotlib stamps creation time into PNG metadata, which made every rebuild a binary
# diff even with identical data. Empty metadata keeps the file byte-stable.
fig.savefig(out, dpi=200, metadata={"Software": ""})
print(f"overview.png rebuilt: {len(top)} targets, {len(companies)} companies")
