#!/usr/bin/env python3
"""build_explorer.py — regenerate graph/explorer.html from graph/*.jsonl + the prose KB.

Usage (from repo root):
    python3 graph/build_explorer.py

FULLY DETERMINISTIC — NO LLM CALLS. Run it after `extract.py` and it reproduces the
interactive explorer byte-for-byte from:
    graph/nodes.jsonl, graph/edges.jsonl     (the graph)
    reference/02_drug_index.md               (brands, class, status, indications, notes)
    reference/00_company_list.md             (company snapshots)
    players/*.md                             (partner blurbs)
    graph/cache/graveyard.json               (failure records)
    graph/cache/layout.json                  (node positions — see below)
    graph/explorer_template.html             (the UI: CSS + JS, data injected)

LLM involvement is confined to `extract.py`'s caches (targets.json, deals.json,
modality_overrides.json). Those are checked in, so a rebuild here never calls a model.

LAYOUT: positions live in graph/cache/layout.json so the picture is stable across
rebuilds (a node doesn't jump because an unrelated node appeared). New nodes are
placed at the centroid of their already-placed neighbours with a deterministic
name-hash jitter — no randomness, no model. Pass --relayout to recompute the whole
layout with networkx (only if installed); that intentionally moves everything, so
do it rarely and eyeball the result.
"""
import json, os, re, sys, glob, hashlib
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, "graph")
CACHE = os.path.join(G, "cache")
W, H = 1800, 1400

nodes = [json.loads(l) for l in open(os.path.join(G, "nodes.jsonl"))]
edges = [json.loads(l) for l in open(os.path.join(G, "edges.jsonl"))]
node_by_id = {n["id"]: n for n in nodes}
mol_node = {n["id"]: n for n in nodes if n["kind"] == "molecule"}

# ---------------------------------------------------------------- display names
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

KIND_STYLE = {"company": {"color": "#1f77b4", "size": 22}, "molecule": {"color": "#2ca02c", "size": 8},
              "target": {"color": "#d62728", "size": 10}, "indication": {"color": "#9467bd", "size": 9},
              "modality": {"color": "#ff7f0e", "size": 14}, "disease_area": {"color": "#8c564b", "size": 16}}
TIER_STYLE = {"core": {"size": 24, "color": "#1f77b4"}, "partner": {"size": 15, "color": "#5fa8d3"},
              "cited": {"size": 10, "color": "#7f9cb0"}}
TIER_NOTE = {
    "core": "KB coverage: full deep dive (Core 22).",
    "partner": "KB coverage: one-page partner profile in players/ — appears here because it licenses or co-owns assets with covered companies.",
    "cited": "KB coverage: NAME ONLY — appears solely because a deal or asset row cites it. No KB file; details are not verified.",
}
LAYOUT_RELS = {"owns": 3.0, "acts_on": 1.6, "treats": 0.9, "has_modality": 0.5, "in_area": 1.2, "failed_on": 1.0}

# ---------------------------------------------------------------- KB side-tables
def index_rows():
    out = defaultdict(list)
    for line in open(os.path.join(ROOT, "reference", "02_drug_index.md")):
        s = line.strip()
        if not s.startswith("|") or s.startswith("| Brand"):
            continue
        if set(s.replace("|", "").strip()) <= {"-", ":", " "}:
            continue
        c = [x.strip() for x in s.strip("|").split("|")]
        if len(c) == 7:
            key = re.sub(r"\s*\(.*?\)", "", c[1].lower()).strip()
            out[key].append(dict(zip(["brand", "generic", "company", "cls", "used_for", "status", "notes"], c)))
    return out

def company_rows():
    out = {}
    alias = {"j&j": "johnson-and-johnson", "merck-and-co": "merck", "gilead-sciences": "gilead",
             "vertex-pharmaceuticals": "vertex"}
    for line in open(os.path.join(ROOT, "reference", "00_company_list.md")):
        s = line.strip()
        if not s.startswith("|"):
            continue
        c = [x.strip() for x in s.strip("|").split("|")]
        if len(c) == 6 and c[0].isdigit():
            k = re.sub(r"\s*\(.*?\)", "", c[1]).lower().replace(" ", "-").replace(".", "").replace("&", "and")
            out[alias.get(k, k)] = {"name": c[1], "hq": c[2], "ticker": c[3], "rev": c[4], "fr": c[5]}
    return out

def player_blurbs():
    out = {}
    for p in glob.glob(os.path.join(ROOT, "players", "*.md")):
        slug = os.path.basename(p)[:-3]
        m = re.search(r"## What it is\s*\n(.+?)(?:\n\n|\n#)", open(p).read(), re.S)
        if m:
            out[slug] = " ".join(m.group(1).split())[:400]
    out.setdefault("legend", out.get("legend-biotech", ""))
    return out

def graveyard():
    p = os.path.join(CACHE, "graveyard.json")
    if not os.path.exists(p):
        return {}
    gy = json.load(open(p))
    out = {}
    for k, g in gy.items():
        mk = re.sub(r"\s*\(.*?\)", "", str(g.get("molecule", ""))).lower().split("—")[0].strip()
        out.setdefault(mk, g)
        out.setdefault(k, g)
    return out

IDX, CO, PLAYERS, GY = index_rows(), company_rows(), player_blurbs(), graveyard()

# ---------------------------------------------------------------- adjacency
owns_m, owned_by = defaultdict(list), defaultdict(list)
acts, acted = defaultdict(list), defaultdict(list)
by_ind, by_mod, failed_t = defaultdict(list), defaultdict(list), defaultdict(list)
deal_party, mol_deals, deals_of = defaultdict(list), defaultdict(list), defaultdict(list)
for e in edges:
    r = e["rel"]
    if r == "owns":
        owns_m[e["src"]].append(e["dst"]); owned_by[e["dst"]].append(e["src"])
    elif r == "acts_on":
        acts[e["src"]].append(e["dst"]); acted[e["dst"]].append(e["src"])
    elif r == "treats":
        by_ind[e["dst"]].append(e["src"])
    elif r == "failed_on":
        failed_t[e["dst"]].append(e["src"])
    elif r == "has_modality":
        by_mod[e["dst"]].append(e["src"])
    elif r == "party_to":
        deal_party[e["dst"]].append((e["src"], e.get("role")))
for e in edges:
    if e["rel"] in ("acquired_via", "via"):
        mol_deals[e["src"]].append(node_by_id.get(e["dst"], {}))
for did, parties in deal_party.items():
    for p, _ in parties:
        deals_of[p].append(node_by_id.get(did, {}))

def mname(g):
    b = (mol_node.get(g, {}).get("brands") or [None])[0]
    return f"{b} ({g})" if b else g

def fmt(gens, cap=8):
    gs = sorted(gens, key=lambda g: -(mol_node.get(g, {}).get("sales_2025_usd_bn") or 0))
    return ", ".join(mname(g) for g in gs[:cap]) + (f" … +{len(gs)-cap} more" if len(gs) > cap else "")

# ---------------------------------------------------------------- nodes
viz_nodes = []
for n in nodes:
    if n["kind"] == "deal":
        continue
    d = {"id": n["id"], "kind": n["kind"], **KIND_STYLE[n["kind"]]}
    if n["kind"] == "molecule":
        d["size"] = 6 + min(n.get("sales_2025_usd_bn") or 0, 40) * 0.9
        d["label"] = (n.get("brands") or [n["id"]])[0] if n.get("brands") else n["id"]
        if n.get("phase") == "failed":
            d["color"] = "#9a9a9a"; d["failed"] = True
    elif n["kind"] == "company":
        tier = n.get("tier", "cited")
        d["tier"] = tier; d.update(TIER_STYLE[tier])
        if tier == "cited":
            d["hollow"] = True
        d["label"] = disp(n["id"])
    else:
        d["label"] = n["id"]
    d["title"] = d["label"]
    viz_nodes.append(d)
kept = {d["id"] for d in viz_nodes}

# ---------------------------------------------------------------- detail panels
for d in viz_nodes:
    nid, parts = d["id"], []
    if d["kind"] == "company":
        ci = CO.get(nid)
        if ci:
            parts.append(f"{ci['name']} — HQ {ci['hq']}, {ci['ticker']}, revenue {ci['rev']}. {ci['fr']}")
        elif PLAYERS.get(nid):
            parts.append(PLAYERS[nid])
        live = [g for g in owns_m[nid] if mol_node.get(g, {}).get("phase") != "failed"]
        if live:
            parts.append(f"Marketed assets in graph ({len(live)}): {fmt(live)}")
        dead = [g for g in owns_m[nid] if mol_node.get(g, {}).get("phase") == "failed"]
        if dead:
            parts.append(f"Graveyard: {fmt(dead, 5)}")
        ds = sorted(deals_of.get(nid, []), key=lambda x: -(x.get("value_usd_bn") or 0))
        if ds:
            ls = [f"• {dn.get('type')} {dn.get('year') or ''}"
                  + (f" ${dn['value_usd_bn']}B" if dn.get("value_usd_bn") else "")
                  + f": {dn.get('counterparty')}"
                  + (f" — {', '.join(str(x) for x in (dn.get('assets') or [])[:3])}" if dn.get("assets") else "")
                  for dn in ds[:7]]
            parts.append(f"Deal history ({len(ds)}):\n" + "\n".join(ls)
                         + (f"\n… +{len(ds)-7} more in KB" if len(ds) > 7 else ""))
        for rel_dir in ("companies", "players"):
            if os.path.exists(os.path.join(ROOT, rel_dir, f"{nid}.md")):
                parts.append(f"KB file: {rel_dir}/{nid}.md")
                break
        parts.append(TIER_NOTE[d.get("tier", "cited")])
    elif d["kind"] == "molecule":
        rws, n = IDX.get(nid, []), mol_node[nid]
        if rws:
            r0 = rws[0]
            brands = ", ".join(sorted({x["brand"] for x in rws}))
            parts.append(f"{nid} (brand: {brands}) — {r0['cls']}. Status: {r0['status']}.\nIndications: {r0['used_for']}")
            if r0["notes"] not in ("—", "-", ""):
                parts.append(f"Notes: {r0['notes']}")
        l2 = f"Owner(s): {', '.join(disp(c) for c in owned_by[nid]) or '—'}."
        if n.get("modality"):
            l2 += f" Modality: {n['modality']}."
        if n.get("sales_2025_usd_bn"):
            l2 += f" 2025 sales ~${n['sales_2025_usd_bn']}B."
        if n.get("loe_year"):
            l2 += f" LOE ~{n['loe_year']}."
        if acts.get(nid):
            l2 += f" Target(s): {', '.join(sorted(set(acts[nid])))}."
        parts.append(l2)
        g = GY.get(nid)
        if g:
            parts.append(f"GRAVEYARD: {g.get('phase_reached')} {g.get('failure_mode')} ({g.get('year_died')}) — "
                         f"{str(g.get('note',''))[:200]}\nLesson: {str(g.get('lesson',''))[:200]}")
        seen, dls = set(), []
        for dn in mol_deals.get(nid, []):
            key = (dn.get("type"), dn.get("year"), dn.get("value_usd_bn"))
            if key in seen:
                continue
            seen.add(key)
            parties = deal_party.get(dn.get("id"), [])
            p0 = parties[0][0] if parties else "?"
            role = parties[0][1] if parties else None
            cp = dn.get("counterparty", "?")
            if dn.get("type") == "divestiture" and role == "acquirer":
                verb = f"{disp(p0)} bought it from {cp}"
            elif dn.get("type") == "divestiture":
                verb = f"{disp(p0)} sold it to {cp}"
            elif dn.get("type") == "acquisition":
                verb = f"{disp(p0)} acquired {cp} (asset came with)"
            elif dn.get("type") == "license":
                verb = f"licensed between {disp(p0)} and {cp}"
            else:
                verb = f"{dn.get('type')} between {disp(p0)} and {cp}"
            dls.append(f"• {dn.get('year') or '?'}"
                       + (f", ${dn['value_usd_bn']}B" if dn.get("value_usd_bn") else "") + f": {verb}")
        if dls:
            parts.append("Deal/ownership history:\n" + "\n".join(sorted(dls)))
    elif d["kind"] == "target":
        live = [g for g in acted[nid] if mol_node.get(g, {}).get("phase") != "failed"]
        dead = failed_t.get(nid, [])
        cos = sorted({disp(c) for g in live for c in owned_by[g]})
        parts.append(f"Target {nid} — {len(live)} marketed asset(s) from {len(cos)} company(ies)"
                     + (f", {len(dead)} failed program(s)" if dead else "") + ".")
        if live:
            parts.append(f"Marketed: {fmt(live)}")
        if cos:
            parts.append(f"Companies: {', '.join(cos)}")
        if dead:
            parts.append(f"Graveyard: {fmt(dead, 6)}")
    elif d["kind"] == "indication":
        ms = by_ind.get(nid, [])
        parts.append(f"Indication: {nid} — {len(ms)} molecule(s) in graph.")
        if ms:
            parts.append(fmt(ms, 12))
    elif d["kind"] == "modality":
        ms = by_mod.get(nid, [])
        parts.append(f"Modality: {nid} — {len(ms)} molecule(s).")
        if ms:
            parts.append(fmt(ms, 12))
    else:
        parts.append(f"{d['kind']}: {nid}")
    d["detail"] = "\n\n".join(parts)

# ---------------------------------------------------------------- layout
layout_path = os.path.join(CACHE, "layout.json")
pos = {k: tuple(v) for k, v in json.load(open(layout_path)).items()} if os.path.exists(layout_path) else {}

if "--relayout" in sys.argv:
    try:
        import networkx as nx
        Gx = nx.Graph(); Gx.add_nodes_from(kept)
        for e in edges:
            if e["rel"] in LAYOUT_RELS and e["src"] in kept and e["dst"] in kept:
                w = max(Gx.get_edge_data(e["src"], e["dst"], {}).get("weight", 0), LAYOUT_RELS[e["rel"]])
                Gx.add_edge(e["src"], e["dst"], weight=w)
        comps = sorted(nx.connected_components(Gx), key=len, reverse=True)
        main = comps[0]
        sp = nx.spring_layout(Gx.subgraph(main), weight="weight", k=1.8 / (len(main) ** 0.5),
                              iterations=250, seed=42)
        xs = [p[0] for p in sp.values()]; ys = [p[1] for p in sp.values()]
        rx, ry = (max(xs) - min(xs)) or 1, (max(ys) - min(ys)) or 1
        pos = {n: (40 + (x - min(xs)) / rx * (W - 80), 30 + (y - min(ys)) / ry * (H * 0.88 - 60))
               for n, (x, y) in sp.items()}
        sats = [n for c in comps[1:] for n in c] + [n for n in kept if n not in Gx or Gx.degree(n) == 0]
        ncols = 26
        for i, n in enumerate(sorted(set(sats))):
            pos[n] = (60 + (i % ncols) * ((W - 120) / ncols), H * 0.90 + (i // ncols) * 26)
        print(f"relayout: {len(main)} in main component, {len(set(sats))} satellites")
    except ImportError:
        sys.exit("--relayout needs networkx (pip install networkx); omit the flag to reuse cached positions")

new_ids = sorted(kept - set(pos))
Gadj = defaultdict(set)
for e in edges:
    if e["rel"] in LAYOUT_RELS and e["src"] in kept and e["dst"] in kept:
        Gadj[e["src"]].add(e["dst"]); Gadj[e["dst"]].add(e["src"])
for nid in new_ids:
    nbrs = [pos[x] for x in Gadj.get(nid, ()) if x in pos]
    cx, cy = (sum(p[0] for p in nbrs) / len(nbrs), sum(p[1] for p in nbrs) / len(nbrs)) if nbrs else (W / 2, H * 0.95)
    h = int(hashlib.md5(nid.encode()).hexdigest()[:6], 16)
    pos[nid] = (cx + (h % 100 - 50) * 0.9, cy + ((h // 100) % 100 - 50) * 0.9)
for d in viz_nodes:
    d["x"], d["y"] = round(pos[d["id"]][0], 1), round(pos[d["id"]][1], 1)
json.dump({k: [round(v[0], 1), round(v[1], 1)] for k, v in pos.items() if k in kept},
          open(layout_path, "w"), indent=0, sort_keys=True)

# ---------------------------------------------------------------- edges
ROLE_VERB = {"acquirer": "acquired", "seller": "sold to", "licensor": "licensed to",
             "licensee": "licensed from", "partner": "partnered with"}
viz_edges = []
for did, parties in deal_party.items():
    dn = node_by_id.get(did, {})
    cp = dn.get("counterparty")
    if len(parties) != 1 or not cp:
        continue
    cslug = cp.lower().replace(" ", "-").replace(".", "").replace("&", "and")
    if cslug not in kept:
        continue
    p0, role = parties[0]
    a = dn.get("assets") or []
    what = ", ".join(str(x) for x in a[:5]) + (f" … +{len(a)-5}" if len(a) > 5 else "")
    ttl = f"{disp(p0)} {ROLE_VERB.get(role, dn.get('type','deal'))} {cp} — {dn.get('type')}"
    if dn.get("year"):
        ttl += f", {dn['year']}"
    if dn.get("value_usd_bn"):
        ttl += f", ${dn['value_usd_bn']}B"
    ttl += f".\nWhat: {what}" if what else ".\nWhat: not specified in the source history"
    viz_edges.append({"source": p0, "target": cslug, "rel": "deal", "title": ttl})

for e in edges:
    if e["rel"] in ("party_to", "acquired_via", "via"):
        continue
    if e["src"] not in kept or e["dst"] not in kept:
        continue
    r = e["rel"]
    if r == "owns":
        ttl = f"{disp(e['src'])} owns/markets {mname(e['dst'])}"
    elif r == "acts_on":
        ttl = f"{mname(e['src'])} acts on {e['dst']}" + (f" ({e['action']})" if e.get("action") else "")
    elif r == "treats":
        ttl = f"{mname(e['src'])} treats {e['dst']}"
    elif r == "failed_on":
        g = GY.get(e["src"], {})
        ttl = f"{mname(e['src'])} FAILED on {e['dst']}" + (
            f" — {g.get('phase_reached')} {g.get('failure_mode')} {g.get('year_died')}: {str(g.get('note',''))[:150]}" if g else "")
    elif r == "competes_with":
        ttl = f"{mname(e['src'])} competes with {mname(e['dst'])}" + (
            f" — shared indication: {e['basis'].split(':')[-1]}" if e.get("basis") else "")
    elif r == "has_modality":
        ttl = f"{mname(e['src'])} is a {e['dst']} drug"
    elif r == "in_area":
        ttl = f"{e['src']} belongs to disease area {e['dst']}"
    else:
        ttl = r
    viz_edges.append({"source": e["src"], "target": e["dst"], "rel": r, "title": ttl})

# ---------------------------------------------------------------- render
tmpl_path = os.path.join(G, "explorer_template.html")
tmpl = open(tmpl_path).read()
out = tmpl.replace("__NODES__", json.dumps(viz_nodes)).replace("__EDGES__", json.dumps(viz_edges))
open(os.path.join(G, "explorer.html"), "w").write(out)
print(f"explorer.html rebuilt: {len(out)//1024} KB | {len(viz_nodes)} nodes, {len(viz_edges)} edges "
      f"| {len(new_ids)} new node(s) placed")
