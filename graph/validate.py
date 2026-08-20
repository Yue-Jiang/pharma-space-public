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

claims_path = os.path.join(G, "claims.jsonl")
claims = [json.loads(l) for l in open(claims_path)] if os.path.exists(claims_path) else []
claims_by_id = {c["id"]: c for c in claims}
indication_schema_path = os.path.join(G, "schema", "indications.json")
indication_schema = json.load(open(indication_schema_path)) if os.path.exists(indication_schema_path) else {"concepts": {}}
indication_concepts = indication_schema.get("concepts", {})

HAS_PRIVATE_CACHE = os.path.isdir(os.path.join(G, "cache"))
override_path = os.path.join(G, "cache", "modality_overrides.json")
modality_overrides = json.load(open(override_path)) if os.path.exists(override_path) else {}
graveyard_path = os.path.join(G, "cache", "graveyard.json")
graveyard = json.load(open(graveyard_path)) if os.path.exists(graveyard_path) else {}
targets_path = os.path.join(G, "cache", "targets.json")
target_cache = json.load(open(targets_path)) if os.path.exists(targets_path) else {}
sales_path = os.path.join(G, "cache", "sales.json")
sales_cache = json.load(open(sales_path)) if os.path.exists(sales_path) else {}
development_path = os.path.join(G, "cache", "development.json")
development_cache = json.load(open(development_path)) if os.path.exists(development_path) else {}
field_bets_path = os.path.join(G, "cache", "field_bets.json")
field_bets = json.load(open(field_bets_path)) if os.path.exists(field_bets_path) else None
bet_assets_path = os.path.join(G, "cache", "bet_assets.json")
bet_assets = json.load(open(bet_assets_path)) if os.path.exists(bet_assets_path) else None
oncology_vocab_path = os.path.join(G, "cache", "oncology_vocabulary.json")
oncology_vocab = json.load(open(oncology_vocab_path)) if os.path.exists(oncology_vocab_path) else None

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

# Field-bet records are a private display layer over the shared graph. They may
# only point at existing companies, field nodes, and curated pipeline assets.
# The visible categorical tier is deliberately validated separately from the
# underlying numeric audit fields so the UI cannot invent a precise ranking.
if field_bets is not None:
    bad_field_bets = set()
    allowed_tiers = {"leader", "challenger", "material", "exploratory"}
    portfolio_pairs = {
        (e["src"], e["dst"]) for e in edges if e.get("rel") == "portfolio_includes"
    }
    if field_bets.get("schema_version") != 1 or not isinstance(field_bets.get("fields"), dict):
        bad_field_bets.add("root [schema_version must be 1 and fields must be an object]")
    for source in field_bets.get("sources", []):
        if not isinstance(source, str) or not os.path.exists(os.path.join(ROOT, source)):
            bad_field_bets.add(f"source [{source} does not exist]")
    for field_slug, field in (field_bets.get("fields") or {}).items():
        if not isinstance(field, dict):
            bad_field_bets.add(f"{field_slug} [field record must be an object]")
            continue
        field_node = field.get("node_id")
        field_kind = by_id.get(field_node, {}).get("kind")
        if field_kind not in {"indication", "disease_area"} and not (
            field.get("composite") is True and field_node not in by_id
        ):
            bad_field_bets.add(f"{field_slug} [invalid field node {field_node}]")
        companies = field.get("companies")
        if not field.get("label") or not field.get("metric") or not isinstance(companies, dict) or not companies:
            bad_field_bets.add(f"{field_slug} [label, metric, and companies are required]")
            continue
        for company_id, record in companies.items():
            prefix = f"{field_slug}/{company_id}"
            if by_id.get(company_id, {}).get("kind") != "company":
                bad_field_bets.add(f"{prefix} [company node missing]")
            if not isinstance(record, dict) or record.get("tier") not in allowed_tiers:
                bad_field_bets.add(f"{prefix} [invalid categorical tier]")
                continue
            asset_ids = record.get("graph_asset_ids")
            active_assets = record.get("active_assets")
            coverage = record.get("graph_asset_coverage")
            studies = record.get("active_studies")
            if not isinstance(asset_ids, list) or len(asset_ids) != len(set(asset_ids)):
                bad_field_bets.add(f"{prefix} [graph_asset_ids must be a unique list]")
                asset_ids = []
            if not isinstance(active_assets, list) or not active_assets:
                bad_field_bets.add(f"{prefix} [active_assets must be a non-empty list]")
                active_assets = []
            if (not isinstance(coverage, dict)
                    or coverage.get("shown") != len(asset_ids)
                    or coverage.get("active") != len(active_assets)
                    or coverage.get("shown", 0) > coverage.get("active", 0)):
                bad_field_bets.add(f"{prefix} [graph asset coverage is inconsistent]")
            if (not isinstance(studies, dict)
                    or any(not isinstance(studies.get(k), int) or studies.get(k) < 0
                           for k in ("efficacy", "support"))
                    or not isinstance(record.get("planned_studies"), int)
                    or record.get("planned_studies") < 0):
                bad_field_bets.add(f"{prefix} [study counts must be non-negative integers]")
            for asset_id in asset_ids:
                if by_id.get(asset_id, {}).get("kind") != "molecule" or mol.get(asset_id, {}).get("phase") != "pipeline":
                    bad_field_bets.add(f"{prefix}/{asset_id} [must be a pipeline molecule node]")
                if (company_id, asset_id) not in portfolio_pairs:
                    bad_field_bets.add(f"{prefix}/{asset_id} [missing portfolio association]")
    if bad_field_bets:
        add("ERROR", "field-bet-contract-invalid",
            "field-bet display records must resolve to curated graph nodes and preserve categorical evidence invariants",
            bad_field_bets)

# The Bets reconciliation cache is the canonical boundary between registry
# intervention labels and graph molecule nodes. Every active asset used by the
# field layer must resolve here, even when it remains in the explicit review
# queue and therefore has no graph node yet.
if bet_assets is not None:
    bad_bet_assets = set()
    portfolio_pairs = {
        (e["src"], e["dst"]) for e in edges if e.get("rel") == "portfolio_includes"
    }
    records = bet_assets.get("assets")
    lookup = bet_assets.get("field_company_lookup")
    metrics = bet_assets.get("metrics")
    field_sources = bet_assets.get("fields")
    if (bet_assets.get("schema_version") != 1 or not isinstance(records, list)
            or not isinstance(lookup, dict) or not isinstance(field_sources, dict)):
        bad_bet_assets.add("root [schema_version must be 1; assets, fields, and field_company_lookup are required]")
        records, lookup, field_sources = [], {}, {}
    for source in bet_assets.get("sources", []):
        if not isinstance(source, str) or not os.path.exists(os.path.join(ROOT, source)):
            bad_bet_assets.add(f"source [{source} does not exist]")
    asset_ids = [record.get("asset_id") for record in records if isinstance(record, dict)]
    if len(asset_ids) != len(set(asset_ids)):
        bad_bet_assets.add("assets [asset_id values must be unique]")
    allowed_dispositions = {
        "existing_pipeline_node", "needs_identity_and_market_status_review",
        "ambiguous_graph_match", "status_conflict_review", "phase4_market_status_review",
        "reviewed_but_public_identity_opaque",
    }
    resolved_unique = 0
    awaiting_curation = set()
    reviewed_opaque = set()
    nct_ids = set()
    entry_count = 0
    resolved_entry_count = 0
    bet_phase_rank = {
        "NA": 0, "EARLY_PHASE1": 1, "PHASE1": 1, "PHASE1|PHASE2": 2,
        "PHASE2": 2, "PHASE2|PHASE3": 3, "PHASE3": 3, "PHASE4": 4,
    }
    for record in records:
        if not isinstance(record, dict):
            bad_bet_assets.add("assets [every asset record must be an object]")
            continue
        asset_id = record.get("asset_id", "<missing>")
        graph_id = record.get("graph_id")
        disposition = record.get("disposition")
        appearances = record.get("appearances")
        studies = record.get("active_studies")
        if disposition not in allowed_dispositions:
            bad_bet_assets.add(f"{asset_id} [invalid disposition]")
        if not isinstance(appearances, list) or not appearances:
            bad_bet_assets.add(f"{asset_id} [appearances must be a non-empty list]")
            appearances = []
        if not isinstance(studies, list) or not studies:
            bad_bet_assets.add(f"{asset_id} [active_studies must be a non-empty list]")
            studies = []
        curation_evidence = record.get("curation_evidence")
        if not isinstance(curation_evidence, list):
            bad_bet_assets.add(f"{asset_id} [curation_evidence must be a list]")
            curation_evidence = []
        for evidence in curation_evidence:
            if (not isinstance(evidence, dict) or not evidence.get("evidence")
                    or not evidence.get("sources")
                    or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", evidence.get("reviewed_as_of", ""))):
                bad_bet_assets.add(f"{asset_id} [invalid reviewed curation evidence]")
        entry_count += len(appearances)
        if graph_id is not None:
            resolved_unique += 1
            resolved_entry_count += len(appearances)
            if by_id.get(graph_id, {}).get("kind") != "molecule" or mol.get(graph_id, {}).get("phase") != "pipeline":
                bad_bet_assets.add(f"{asset_id}/{graph_id} [graph match must be a pipeline molecule]")
            if disposition != "existing_pipeline_node":
                bad_bet_assets.add(f"{asset_id}/{graph_id} [resolved pipeline node has wrong disposition]")
            for owner_id in record.get("current_owner_ids", []):
                if (owner_id, graph_id) not in portfolio_pairs:
                    bad_bet_assets.add(f"{asset_id}/{owner_id} [owner lacks portfolio edge]")
        else:
            if disposition == "reviewed_but_public_identity_opaque":
                reviewed_opaque.add(asset_id)
                if not curation_evidence:
                    bad_bet_assets.add(f"{asset_id} [reviewed opaque asset must retain curation evidence]")
            else:
                awaiting_curation.add(asset_id)
            if record.get("global_market_status") != "unverified":
                bad_bet_assets.add(f"{asset_id} [unresolved asset must retain unverified market status]")
        appearance_keys = {
            (appearance.get("field_id"), appearance.get("company_id"), appearance.get("display_name"))
            for appearance in appearances
        }
        if len(appearance_keys) != len(appearances):
            bad_bet_assets.add(f"{asset_id} [duplicate field/company/display appearance]")
        for study in studies:
            nct_id = study.get("nct_id")
            if (study.get("status") not in {"RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"}
                    or not isinstance(nct_id, str) or not re.fullmatch(r"NCT\d{8}", nct_id)
                    or study.get("source") != f"https://clinicaltrials.gov/study/{nct_id}"):
                bad_bet_assets.add(f"{asset_id}/{nct_id} [invalid active ClinicalTrials.gov evidence]")
            else:
                nct_ids.add(nct_id)
            if "PHASE4" in study.get("phases", []):
                bad_bet_assets.add(
                    f"{asset_id}/{nct_id} [Phase 4 intervention cannot remain in unmarketed Bets without adjudication]"
                )
        if record.get("phase4_registry_flag") != any(
                "PHASE4" in study.get("phases", []) for study in studies):
            bad_bet_assets.add(f"{asset_id} [Phase 4 registry flag is inconsistent]")
        observed_phases = sorted(
            {phase for study in studies for phase in study.get("phases", [])},
            key=lambda phase: (bet_phase_rank.get(phase, -1), phase),
        )
        expected_max_phase = max(
            observed_phases, key=lambda phase: (bet_phase_rank.get(phase, -1), phase), default="NA"
        )
        if (record.get("registered_phases") != observed_phases
                or record.get("max_registered_phase") != expected_max_phase
                or record.get("active_nct_count") != len({study.get("nct_id") for study in studies})):
            bad_bet_assets.add(f"{asset_id} [registered phase or active-NCT summary is inconsistent]")
    if isinstance(metrics, dict):
        expected_metrics = {
            "company_field_asset_entries": entry_count,
            "unique_reconciled_assets": len(records),
            "unique_active_nct_records": len(nct_ids),
            "graph_resolved_company_field_asset_entries": resolved_entry_count,
            "unique_graph_resolved_assets": resolved_unique,
        }
        for key, expected in expected_metrics.items():
            if metrics.get(key) != expected:
                bad_bet_assets.add(f"metrics/{key} [expected {expected}, found {metrics.get(key)}]")
    else:
        bad_bet_assets.add("metrics [required object missing]")
    if field_bets is not None:
        if set(field_sources) != set(field_bets.get("fields", {})):
            bad_bet_assets.add("fields [source map must cover the field-bet fields exactly]")
        for field_id, source in field_sources.items():
            if (not isinstance(source, dict) or source.get("registry") != "ClinicalTrials.gov API v2"
                    or not source.get("condition_query")):
                bad_bet_assets.add(f"{field_id} [missing registry or condition-query provenance]")
        for field_id, field in field_bets.get("fields", {}).items():
            for company_id, company in field.get("companies", {}).items():
                company_lookup = lookup.get(field_id, {}).get(company_id, {})
                if set(company_lookup) != set(company.get("active_assets", [])):
                    bad_bet_assets.add(f"{field_id}/{company_id} [lookup does not cover active assets exactly]")
                resolved_entries = [
                    company_lookup[name].get("graph_id") for name in company.get("active_assets", [])
                    if name in company_lookup and company_lookup[name].get("graph_id")
                ]
                if len(resolved_entries) != len(set(resolved_entries)):
                    bad_bet_assets.add(
                        f"{field_id}/{company_id} [multiple active labels resolve to one graph asset]"
                    )
                resolved = list(dict.fromkeys(resolved_entries))
                if resolved != company.get("graph_asset_ids"):
                    bad_bet_assets.add(f"{field_id}/{company_id} [field display is stale versus reconciliation]")
    if bad_bet_assets:
        add("ERROR", "bet-asset-reconciliation-invalid",
            "registry assets must have reproducible aliases, active NCT evidence, and consistent graph resolution",
            bad_bet_assets)
    if awaiting_curation:
        add("WARN", "bet-assets-awaiting-curation",
            "registry-backed active assets awaiting canonical identity, ownership, and global market-status review",
            awaiting_curation)
    if reviewed_opaque:
        add("INFO", "bet-assets-reviewed-publicly-opaque",
            "reviewed registry-backed programs whose public evidence does not disclose a defensible canonical molecular identity or mechanism",
            reviewed_opaque)

# Oncology intervention normalization is kept separate from the published Bets
# fields until its identity and disposition gates pass. The cache must account
# for every frozen intervention occurrence and may never infer ownership from a
# vocabulary identity alone.
if oncology_vocab is not None:
    bad_oncology_vocab = set()
    fields = oncology_vocab.get("fields")
    if oncology_vocab.get("schema_version") != 1 or not isinstance(fields, dict) or not fields:
        bad_oncology_vocab.add("root [schema_version 1 and non-empty fields object are required]")
        fields = {}
    for source in oncology_vocab.get("sources", []):
        if not isinstance(source, str) or not os.path.exists(os.path.join(ROOT, source)):
            bad_oncology_vocab.add(f"source [{source} does not exist]")
    portfolio_pairs = {
        (edge["src"], edge["dst"]) for edge in edges if edge.get("rel") == "portfolio_includes"
    }
    allowed_statuses = {
        "graph_exact", "vocabulary_alias_to_graph", "ncit_exact", "rxnorm_exact",
        "combination_resolved", "non_specific_control_or_regimen", "unresolved",
        "ambiguous_graph_match", "ambiguous_vocabulary_match", "reviewed_override",
    }
    allowed_roles = {
        "investigational_asset", "marketed_or_legacy_drug", "marketed_drug", "regimen",
        "diagnostic_or_support", "non_specific_control_or_regimen", "combination_regimen",
        "drug_market_status_review", "other_concept_review", "review",
        "inactive_investigational", "biosimilar_candidate",
    }
    ready_roles = {
        "investigational_asset", "marketed_or_legacy_drug", "marketed_drug", "regimen",
        "diagnostic_or_support", "non_specific_control_or_regimen", "combination_regimen",
        "inactive_investigational", "biosimilar_candidate",
    }
    identity_unresolved_statuses = {
        "unresolved", "ambiguous_graph_match", "ambiguous_vocabulary_match",
    }
    below_identity_gate = set()
    below_disposition_gate = set()
    for field_id, field in fields.items():
        labels = field.get("labels") if isinstance(field, dict) else None
        if not isinstance(labels, list) or not labels:
            bad_oncology_vocab.add(f"{field_id} [labels must be a non-empty list]")
            continue
        label_names = [record.get("label") for record in labels if isinstance(record, dict)]
        if len(label_names) != len(labels) or len(label_names) != len(set(label_names)):
            bad_oncology_vocab.add(f"{field_id} [labels must be unique named objects]")
        status_counts = Counter()
        role_counts = Counter()
        total = 0
        for record in labels:
            if not isinstance(record, dict):
                continue
            label = record.get("label", "<missing>")
            occurrences = record.get("occurrences")
            status = record.get("status")
            role = record.get("role")
            if not isinstance(occurrences, int) or occurrences < 1:
                bad_oncology_vocab.add(f"{field_id}/{label} [occurrences must be a positive integer]")
                continue
            total += occurrences
            status_counts[status] += occurrences
            role_counts[role] += occurrences
            if status not in allowed_statuses or role not in allowed_roles or not record.get("basis"):
                bad_oncology_vocab.add(f"{field_id}/{label} [invalid or silent status, role, or basis]")
            if not isinstance(record.get("company_ids"), list) or not record.get("company_ids"):
                bad_oncology_vocab.add(f"{field_id}/{label} [company context is required]")
            nct_ids = record.get("nct_ids")
            if (not isinstance(nct_ids, list) or not nct_ids
                    or any(not isinstance(nct_id, str) or not re.fullmatch(r"NCT\d{8}", nct_id) for nct_id in nct_ids)):
                bad_oncology_vocab.add(f"{field_id}/{label} [valid NCT context is required]")
            graph_ids = record.get("graph_ids")
            if not isinstance(graph_ids, list) or len(graph_ids) != len(set(graph_ids)):
                bad_oncology_vocab.add(f"{field_id}/{label} [graph_ids must be a unique list]")
                graph_ids = []
            for graph_id in graph_ids:
                if by_id.get(graph_id, {}).get("kind") != "molecule":
                    bad_oncology_vocab.add(f"{field_id}/{label}/{graph_id} [unknown molecule node]")
            if role == "investigational_asset":
                if not graph_ids:
                    bad_oncology_vocab.add(f"{field_id}/{label} [investigational role requires a canonical graph node]")
                for graph_id in graph_ids:
                    if mol.get(graph_id, {}).get("phase") != "pipeline":
                        bad_oncology_vocab.add(f"{field_id}/{label}/{graph_id} [investigational role requires pipeline status]")
                for owner_id in record.get("current_owner_ids", []):
                    if not any((owner_id, graph_id) in portfolio_pairs for graph_id in graph_ids):
                        bad_oncology_vocab.add(f"{field_id}/{label}/{owner_id} [owner lacks portfolio association]")
            if role == "marketed_or_legacy_drug" and any(
                    mol.get(graph_id, {}).get("phase") == "pipeline" for graph_id in graph_ids):
                bad_oncology_vocab.add(f"{field_id}/{label} [marketed role points to pipeline graph node]")
            if role in {"marketed_or_legacy_drug", "marketed_drug"} and record.get("market_status") not in {"marketed", "legacy"}:
                bad_oncology_vocab.add(f"{field_id}/{label} [marketed role requires marketed or legacy status]")
            if role == "inactive_investigational" and record.get("market_status") not in {
                    "failed", "withdrawn", "discontinued", "inactive_or_deprioritized"}:
                bad_oncology_vocab.add(f"{field_id}/{label} [inactive role requires an inactive status]")
            if role == "biosimilar_candidate" and record.get("market_status") != "pipeline":
                bad_oncology_vocab.add(f"{field_id}/{label} [biosimilar candidate requires pipeline status]")
            components = record.get("components")
            if role == "combination_regimen" and (not isinstance(components, list) or not components):
                bad_oncology_vocab.add(f"{field_id}/{label} [resolved combination requires components]")
        resolved_identity = total - sum(status_counts[status] for status in identity_unresolved_statuses)
        resolved_disposition = sum(role_counts[role] for role in ready_roles)
        expected_identity = {
            "resolved": resolved_identity, "total": total,
            "fraction": round(resolved_identity / total, 4) if total else 0,
        }
        expected_disposition = {
            "resolved": resolved_disposition, "total": total,
            "fraction": round(resolved_disposition / total, 4) if total else 0,
        }
        if (field.get("identity_resolution") != expected_identity
                or field.get("publication_disposition") != expected_disposition
                or field.get("status_occurrences") != dict(sorted(status_counts.items()))
                or field.get("role_occurrences") != dict(sorted(role_counts.items()))
                or field.get("intervention_occurrences") != total
                or field.get("unique_intervention_labels") != len(labels)):
            bad_oncology_vocab.add(f"{field_id} [coverage summaries disagree with label records]")
        if expected_identity["fraction"] < 0.9:
            below_identity_gate.add(field_id)
        if expected_disposition["fraction"] < 0.9:
            below_disposition_gate.add(field_id)
    if bad_oncology_vocab:
        add("ERROR", "oncology-vocabulary-reconciliation-invalid",
            "oncology labels require complete occurrence accounting, provenance, graph-safe identity, and reproducible summaries",
            bad_oncology_vocab)
    if below_identity_gate:
        add("WARN", "oncology-identity-gate-not-met",
            "oncology fields below the 90 percent occurrence-weighted identity-resolution gate",
            below_identity_gate)
    if below_disposition_gate:
        add("WARN", "oncology-publication-gate-not-met",
            "oncology fields below the 90 percent occurrence-weighted role, market-status, and ownership disposition gate",
            below_disposition_gate)

# ---------------------------------------------------- source-backed indication claims
dupe_claim_ids = [i for i, c in Counter(c["id"] for c in claims).items() if c > 1]
if dupe_claim_ids:
    add("ERROR", "duplicate-claim-ids", "same claim id appears more than once", dupe_claim_ids)

INDICATION_RELATIONS = {"treats", "prevents", "studied_for"}
indication_edges = [
    e for e in edges if e.get("rel") in INDICATION_RELATIONS and e.get("etype") == "fact"
]
missing_claim_links = {
    f"{e['src']} {e['rel']} {e['dst']}" for e in indication_edges if not e.get("claim_id")
}
unknown_claim_links = {
    f"{e['src']} {e['rel']} {e['dst']} [{e.get('claim_id')}]" for e in indication_edges
    if e.get("claim_id") and e["claim_id"] not in claims_by_id
}
claim_edge_mismatches = set()
edge_claim_ids = set()
for e in indication_edges:
    claim_id = e.get("claim_id")
    if not claim_id or claim_id not in claims_by_id:
        continue
    edge_claim_ids.add(claim_id)
    c = claims_by_id[claim_id]
    if (c.get("subject"), c.get("relation"), c.get("object")) != (e["src"], e["rel"], e["dst"]):
        claim_edge_mismatches.add(
            f"{claim_id} [claim={c.get('subject')}->{c.get('object')}; edge={e['src']}->{e['dst']}]"
        )
    if c.get("phase") != e.get("phase") or c.get("phase") != mol.get(e["src"], {}).get("phase"):
        claim_edge_mismatches.add(
            f"{claim_id} [claim phase={c.get('phase')}; edge phase={e.get('phase')}; "
            f"node phase={mol.get(e['src'], {}).get('phase')}]"
        )
    if c.get("relation") == "studied_for" and c.get("intended_use") != e.get("intended_use"):
        claim_edge_mismatches.add(
            f"{claim_id} [claim intent={c.get('intended_use')}; edge intent={e.get('intended_use')}]"
        )
    if (c.get("development_stage"), c.get("study"), c.get("study_status"),
            c.get("status_as_of")) != (
            e.get("development_stage"), e.get("study"), e.get("study_status"),
            e.get("status_as_of")):
        claim_edge_mismatches.add(
            f"{claim_id} [claim development={c.get('development_stage')}/{c.get('study')}; "
            f"claim status={c.get('study_status')}/{c.get('status_as_of')}; "
            f"edge development={e.get('development_stage')}/{e.get('study')}; "
            f"edge status={e.get('study_status')}/{e.get('status_as_of')}]"
        )
orphan_claims = {
    c["id"] for c in claims
    if c.get("relation") in INDICATION_RELATIONS and c["id"] not in edge_claim_ids
}
bad_claim_provenance = set()
claim_relation_conflicts = set()
claim_phase_conflicts = set()
prevention_language = re.compile(r"\bprevent(?:ion|ive)?\b|\bprophylaxis\b|\bprep\b", re.I)
treatment_language = re.compile(r"\btreat(?:ment|s|ed|ing)?\b|\bacute\b", re.I)
for c in claims:
    source = c.get("source", "")
    evidence = c.get("evidence")
    if not source or not evidence:
        bad_claim_provenance.add(c.get("id", "<missing-id>"))
    elif not source.startswith(("http://", "https://")) and not os.path.exists(os.path.join(ROOT, source)):
        bad_claim_provenance.add(f"{c.get('id')} [missing source: {source}]")
    context = " ".join(c.get("context") or [])
    class_text = mol.get(c.get("subject"), {}).get("class", "")
    preventive_support = bool(prevention_language.search(context) or re.search(r"\bvaccine\b", class_text, re.I))
    effective_relation = c.get("intended_use") if c.get("relation") == "studied_for" else c.get("relation")
    if effective_relation == "prevents" and not preventive_support:
        claim_relation_conflicts.add(f"{c.get('id')} [prevents lacks preventive evidence]")
    if (effective_relation == "treats" and prevention_language.search(context)
            and not treatment_language.search(context)):
        claim_relation_conflicts.add(f"{c.get('id')} [preventive evidence labeled treats]")
    subject_phase = mol.get(c.get("subject"), {}).get("phase")
    if subject_phase == "pipeline" and c.get("relation") != "studied_for":
        claim_phase_conflicts.add(f"{c.get('id')} [pipeline claim uses {c.get('relation')}]")
    if (subject_phase != "pipeline" and c.get("relation") == "studied_for"
            and not c.get("development_stage")):
        claim_phase_conflicts.add(f"{c.get('id')} [non-pipeline claim uses studied_for]")
    if c.get("relation") == "studied_for" and effective_relation not in {"treats", "prevents"}:
        claim_phase_conflicts.add(f"{c.get('id')} [studied_for lacks intended_use]")
if missing_claim_links:
    add("ERROR", "indication-edge-missing-claim",
        "every factual indication edge must link to a source-backed claim", missing_claim_links)
if unknown_claim_links:
    add("ERROR", "indication-edge-unknown-claim",
        "indication edge references a claim id that does not exist", unknown_claim_links)
if claim_edge_mismatches:
    add("ERROR", "indication-claim-edge-mismatch",
        "claim subject/relation/object disagrees with its graph edge", claim_edge_mismatches)
if orphan_claims:
    add("ERROR", "indication-claim-orphan",
        "source-backed indication claim has no matching graph edge", orphan_claims)
if bad_claim_provenance:
    add("ERROR", "indication-claim-missing-provenance",
        "indication claims require existing sources and non-empty evidence", bad_claim_provenance)
if claim_relation_conflicts:
    add("ERROR", "indication-use-relation-conflict",
        "treatment versus prevention relation disagrees with source context", claim_relation_conflicts)
if claim_phase_conflicts:
    add("ERROR", "indication-phase-relation-conflict",
        "pipeline uses must be studied_for and established uses must be treats/prevents",
        claim_phase_conflicts)

expected_subtypes = {
    (child, record["parent"]) for child, record in indication_concepts.items()
    if record.get("parent") and child in by_id
}
observed_subtypes = {
    (e["src"], e["dst"]) for e in edges if e.get("rel") == "subtype_of"
}
missing_subtypes = {f"{a} -> {b}" for a, b in expected_subtypes - observed_subtypes}
unexpected_subtypes = {f"{a} -> {b}" for a, b in observed_subtypes - expected_subtypes}
if missing_subtypes:
    add("ERROR", "indication-hierarchy-missing",
        "exact indication concept is missing its declared parent edge", missing_subtypes)
if unexpected_subtypes:
    add("ERROR", "indication-hierarchy-unexpected",
        "subtype edge is not declared in the indication schema", unexpected_subtypes)

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

uses = defaultdict(set)
for e in edges:
    if e["rel"] in INDICATION_RELATIONS: uses[e["src"]].add(e["dst"])
only_other = {g for g in mol if uses.get(g) == {"other"}}
no_ind = {g for g in mol if g not in uses}
if only_other:
    add("WARN", "indication-other-only",
        "molecules whose ONLY indication is the catch-all 'other' — add an IND_RULES pattern "
        "or fix the drug-index 'Used for' cell", only_other)
if no_ind:
    add("WARN", "indication-missing", "molecules with no indication at all", no_ind)

acts = defaultdict(set)
for e in edges:
    if e["rel"] == "acts_on": acts[e["src"]].add(e["dst"])

# Cycle-5 external audit: newer pipeline assets had explicit target language in
# primary sources but stale/missing cache records, so the graph silently omitted
# every one. Keep the 24 sampled assertions exact (including selective CDK4,
# which must not be widened to CDK4/6), and require inspectable provenance.
AUDITED_TARGETS_CYCLE_5 = {
    ("abbv-400", "MET"),
    ("arlo-cel", "GPRC5D"),
    ("atirmociclib", "CDK4"),
    ("bleximenib", "menin"),
    ("brivekimig", "TNF-alpha"),
    ("brivekimig", "OX40L"),
    ("domvanalimab", "TIGIT"),
    ("garetosmab", "activin-A"),
    ("ifinatamab deruxtecan", "B7-H3"),
    ("obrixtamig", "DLL3"),
    ("obrixtamig", "CD3"),
    ("pasritamig", "KLK2"),
    ("pasritamig", "CD3"),
    ("prifetrastat", "KAT6A"),
    ("prifetrastat", "KAT6B"),
    ("sigvotatug vedotin", "integrin beta-6"),
    ("frexalimab", "CD40L"),
    ("felzartamab", "CD38"),
    ("inaxaplin", "APOL1"),
    ("gocatamig", "DLL3"),
    ("gocatamig", "CD3"),
    ("bnt327", "PD-L1"),
    ("bnt327", "VEGF-A"),
    ("etentamig", "BCMA"),
}
audited_cache = []
for generic, records in target_cache.items():
    for record in records:
        if record.get("audit_cycle") == 5:
            audited_cache.append((generic, record))
bad_audited_cache = {
    f"{generic} -> {record.get('target', '<missing>')}"
    for generic, record in audited_cache
    if not record.get("source") or not record.get("evidence")
}
observed_audited_edges = {
    (e["src"], e["dst"]): e for e in edges
    if e.get("rel") == "acts_on" and (e["src"], e["dst"]) in AUDITED_TARGETS_CYCLE_5
}
missing_audited_targets = {
    f"{generic} -> {target}"
    for generic, target in AUDITED_TARGETS_CYCLE_5
    if (generic, target) not in observed_audited_edges
}
unproven_audited_edges = {
    f"{generic} -> {target}"
    for (generic, target), edge in observed_audited_edges.items()
    if not edge.get("source") or not edge.get("evidence")
}
if HAS_PRIVATE_CACHE and len(audited_cache) != 24:
    bad_audited_cache.add(f"expected 24 cycle-5 target records, found {len(audited_cache)}")
if bad_audited_cache:
    add("ERROR", "audited-target-cache-provenance",
        "cycle-5 externally audited target records require source and evidence",
        bad_audited_cache)
if missing_audited_targets or unproven_audited_edges:
    add("ERROR", "audited-target-regression",
        "cycle-5 target assertion is missing, widened, or lost generated provenance",
        missing_audited_targets | unproven_audited_edges)

# Cycle 9 returns to the largest remaining coverage gap, but audits action as
# well as target identity. Exact selectivity matters: a PARP1-selective asset
# must not be widened to the established PARP class, and both arms of a
# bispecific or dual agonist must survive extraction with primary provenance.
AUDITED_TARGET_ACTIONS_CYCLE_9 = {
    ("amlitelimab", "OX40L"): "antagonist",
    ("anitocabtagene autoleucel", "BCMA"): "engager",
    ("bimagrumab", "ActRII"): "antagonist",
    ("brigimadlin", "MDM2"): "inhibitor",
    ("enicepatide", "GLP-1R"): "agonist",
    ("enicepatide", "GIPR"): "agonist",
    ("ianalumab", "BAFF-R"): "blocker",
    ("itepekimab", "IL-33"): "antagonist",
    ("iza-bren", "EGFR"): "binder",
    ("iza-bren", "HER3"): "binder",
    ("rilvegostomig", "PD-1"): "antagonist",
    ("rilvegostomig", "TIGIT"): "antagonist",
    ("volrustomig", "PD-1"): "antagonist",
    ("volrustomig", "CTLA-4"): "antagonist",
    ("fianlimab", "LAG-3"): "antagonist",
    ("mezagitamab", "CD38"): "binder",
    ("raludotatug deruxtecan", "CDH6"): "binder",
    ("xaluritamig", "STEAP1"): "engager",
    ("xaluritamig", "CD3"): "engager",
    ("sasanlimab", "PD-1"): "antagonist",
    ("saruparib", "PARP1"): "inhibitor",
    ("zidesamtinib", "ROS1"): "inhibitor",
    ("olatorepatide", "GLP-1R"): "agonist",
    ("olatorepatide", "GIPR"): "agonist",
}
audited_target_actions = [
    (generic, record) for generic, records in target_cache.items() for record in records
    if record.get("audit_cycle") == 9
]
audited_target_action_cache = {
    (generic, record.get("target")): record for generic, record in audited_target_actions
}
bad_target_action_cache = {
    f"{generic} -> {record.get('target', '<missing>')}"
    for generic, record in audited_target_actions
    if generic not in mol or not record.get("source") or not record.get("evidence")
    or record.get("action") not in {
        "agonist", "antagonist", "inhibitor", "blocker", "degrader",
        "silencer", "engager", "binder", "substitution",
    }
}
if HAS_PRIVATE_CACHE and len(audited_target_actions) != 24:
    bad_target_action_cache.add(
        f"expected 24 cycle-9 target-action records, found {len(audited_target_actions)}"
    )
if HAS_PRIVATE_CACHE and set(audited_target_action_cache) != set(AUDITED_TARGET_ACTIONS_CYCLE_9):
    bad_target_action_cache.add("cycle-9 audited molecule/target identity set changed")
for key, expected_action in AUDITED_TARGET_ACTIONS_CYCLE_9.items():
    record = audited_target_action_cache.get(key)
    if record and record.get("action") != expected_action:
        bad_target_action_cache.add(
            f"{key[0]} -> {key[1]} action {record.get('action')} != {expected_action}"
        )
observed_target_action_edges = {
    (edge.get("src"), edge.get("dst")): edge for edge in edges
    if edge.get("rel") == "acts_on"
    and (edge.get("src"), edge.get("dst")) in AUDITED_TARGET_ACTIONS_CYCLE_9
}
target_action_regressions = set()
for key, expected_action in AUDITED_TARGET_ACTIONS_CYCLE_9.items():
    edge = observed_target_action_edges.get(key)
    record = audited_target_action_cache.get(key)
    if (not edge or edge.get("action") != expected_action
            or not edge.get("source") or not edge.get("evidence")
            or (HAS_PRIVATE_CACHE and (
                not record or edge.get("source") != record.get("source")
                or edge.get("evidence") != record.get("evidence")
            ))):
        target_action_regressions.add(f"{key[0]} -> {key[1]} / {expected_action}")
if bad_target_action_cache:
    add("ERROR", "audited-target-action-cache-provenance",
        "cycle-9 target-action records require exact identity, action, and primary evidence",
        bad_target_action_cache)
if target_action_regressions:
    add("ERROR", "audited-target-action-regression",
        "cycle-9 target identity, action, selectivity, or generated provenance was lost",
        target_action_regressions)

# Cycle 6 audited source-backed product sales. Exact component boundaries matter:
# combined table rows must not be copied wholesale onto every molecule in the row.
audited_sales = [
    (generic, record) for generic, records in sales_cache.items() for record in records
    if record.get("audit_cycle") == 6
]
bad_sales_cache = {
    f"{generic} / {record.get('label', '<missing>')}"
    for generic, record in audited_sales
    if generic not in mol or not record.get("source") or not record.get("evidence")
    or record.get("reported_currency") not in {"USD", "EUR", "GBP"}
    or not isinstance(record.get("reported_bn"), (int, float))
    or not isinstance(record.get("usd_bn"), (int, float))
}
sales_total_conflicts = {
    generic for generic, records in sales_cache.items() if generic in mol
    and abs((mol[generic].get("sales_2025_usd_bn") or 0)
            - round(sum(r["usd_bn"] for r in records), 3)) > 0.0001
}
sales_component_conflicts = {
    generic for generic, records in sales_cache.items() if generic in mol
    and mol[generic].get("sales_2025_components") != records
}
if HAS_PRIVATE_CACHE and len(audited_sales) != 24:
    bad_sales_cache.add(f"expected 24 cycle-6 sales records, found {len(audited_sales)}")
if bad_sales_cache:
    add("ERROR", "audited-sales-cache-provenance",
        "cycle-6 externally audited sales require exact reported units and primary evidence",
        bad_sales_cache)
if sales_total_conflicts or sales_component_conflicts:
    add("ERROR", "audited-sales-regression",
        "source-backed sales components were lost, duplicated, or changed in the graph",
        sales_total_conflicts | sales_component_conflicts)

# Cycle 7 audited indication-specific development assertions. Portfolio status is
# molecule-level, but clinical stage belongs to the molecule-indication claim. This
# permits, for example, marketed remibrutinib for CSU to remain `marketed` while its
# multiple-sclerosis program is represented as a sourced Phase 3 `studied_for` edge.
audited_development = [
    (generic, record) for generic, records in development_cache.items() for record in records
    if record.get("audit_cycle") == 7
]
valid_development_stages = {"phase-1", "phase-1/2", "phase-2", "phase-2/3", "phase-3"}
bad_development_cache = {
    f"{generic} / {record.get('indication', '<missing>')}"
    for generic, record in audited_development
    if generic not in mol or by_id.get(record.get("indication"), {}).get("kind") != "indication"
    or record.get("stage") not in valid_development_stages
    or record.get("intended_use") not in {"treats", "prevents"}
    or not re.fullmatch(r"NCT\d{8}", str(record.get("study", "")))
    or record.get("source") != f"https://clinicaltrials.gov/study/{record.get('study')}"
    or not record.get("evidence")
}
audited_development_keys = {
    (generic, record["indication"]): record for generic, record in audited_development
}
observed_development_edges = {
    (edge.get("src"), edge.get("dst")): edge for edge in indication_edges
    if (edge.get("src"), edge.get("dst")) in audited_development_keys
}
development_regressions = set()
for key, record in audited_development_keys.items():
    edge = observed_development_edges.get(key)
    if (not edge or edge.get("rel") != "studied_for"
            or edge.get("intended_use") != record["intended_use"]
            or edge.get("development_stage") != record["stage"]
            or edge.get("study") != record["study"]
            or edge.get("source") != record["source"]
            or edge.get("evidence") != record["evidence"]):
        development_regressions.add(f"{key[0]} -> {key[1]}")
if HAS_PRIVATE_CACHE and len(audited_development) != 24:
    bad_development_cache.add(
        f"expected 24 cycle-7 development records, found {len(audited_development)}"
    )
if HAS_PRIVATE_CACHE and len(audited_development_keys) != len(audited_development):
    bad_development_cache.add("duplicate cycle-7 molecule/indication development record")
if bad_development_cache:
    add("ERROR", "audited-development-cache-provenance",
        "cycle-7 development records require exact stage, registered study, and primary evidence",
        bad_development_cache)
if development_regressions:
    add("ERROR", "audited-development-regression",
        "audited indication-specific development stage or investigational relation was lost",
        development_regressions)

# Cycle 8 audits the lifecycle state of a registered study. Phase alone cannot
# distinguish active recruitment from a completed or terminated pivotal trial.
# Preserve the registry's exact overall status and the date it was checked on the
# indication-specific claim; an inactive study remains historical `studied_for`
# evidence and must not silently look active.
audited_study_status = [
    (generic, record) for generic, records in development_cache.items() for record in records
    if record.get("audit_cycle") == 8
]
valid_study_statuses = {
    "not-yet-recruiting", "recruiting", "enrolling-by-invitation",
    "active-not-recruiting", "suspended", "terminated", "completed", "withdrawn",
}
bad_study_status_cache = {
    f"{generic} / {record.get('indication', '<missing>')}"
    for generic, record in audited_study_status
    if generic not in mol or by_id.get(record.get("indication"), {}).get("kind") != "indication"
    or record.get("stage") not in valid_development_stages
    or record.get("intended_use") not in {"treats", "prevents"}
    or not re.fullmatch(r"NCT\d{8}", str(record.get("study", "")))
    or record.get("source") != f"https://clinicaltrials.gov/study/{record.get('study')}"
    or record.get("study_status") not in valid_study_statuses
    or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(record.get("status_as_of", "")))
    or not record.get("evidence")
}
audited_study_status_keys = {
    (generic, record["indication"]): record for generic, record in audited_study_status
}
observed_study_status_edges = {
    (edge.get("src"), edge.get("dst")): edge for edge in indication_edges
    if (edge.get("src"), edge.get("dst")) in audited_study_status_keys
}
study_status_regressions = set()
for key, record in audited_study_status_keys.items():
    edge = observed_study_status_edges.get(key)
    if (not edge or edge.get("rel") != "studied_for"
            or edge.get("intended_use") != record["intended_use"]
            or edge.get("development_stage") != record["stage"]
            or edge.get("study") != record["study"]
            or edge.get("study_status") != record["study_status"]
            or edge.get("status_as_of") != record["status_as_of"]
            or edge.get("source") != record["source"]
            or edge.get("evidence") != record["evidence"]):
        study_status_regressions.add(f"{key[0]} -> {key[1]}")
if HAS_PRIVATE_CACHE and len(audited_study_status) != 24:
    bad_study_status_cache.add(
        f"expected 24 cycle-8 study-status records, found {len(audited_study_status)}"
    )
if HAS_PRIVATE_CACHE and len(audited_study_status_keys) != len(audited_study_status):
    bad_study_status_cache.add("duplicate cycle-8 molecule/indication study-status record")
if bad_study_status_cache:
    add("ERROR", "audited-study-status-cache-provenance",
        "cycle-8 development records require exact registered status, check date, and primary evidence",
        bad_study_status_cache)
if study_status_regressions:
    add("ERROR", "audited-study-status-regression",
        "audited registered study status or indication-specific development evidence was lost",
        study_status_regressions)

# Cycle 10 is a mixed capstone audit: for each fresh molecule it locks one
# target/action assertion and three independent registered-development facts
# (exact indication, phase, and lifecycle status). It also prevents the
# elecoglipron/AZD5004 alias from splitting into contradictory molecule nodes.
AUDITED_MIXED_TARGETS_CYCLE_10 = {
    ("elecoglipron", "GLP-1R"): "agonist",
    ("apecotrep", "TRPC6"): "inhibitor",
    ("atumelnant", "MC2R"): "antagonist",
    ("cemdisiran", "C5"): "silencer",
    ("delpacibart braxlosiran", "DUX4"): "silencer",
    ("gefurulimab", "C5"): "antagonist",
    ("zorevunersen", "SCN1A"): "substitution",
    ("paltusotine", "SST2"): "agonist",
    ("patritumab deruxtecan", "HER3"): "binder",
    ("pegozafermin", "FGF21R"): "agonist",
    ("rusfertide", "ferroportin"): "blocker",
    ("pelacarsen", "LPA"): "silencer",
}
audited_mixed_targets = [
    (generic, record) for generic, records in target_cache.items() for record in records
    if record.get("audit_cycle") == 10
]
audited_mixed_target_cache = {
    (generic, record.get("target")): record for generic, record in audited_mixed_targets
}
audited_mixed_development = [
    (generic, record) for generic, records in development_cache.items() for record in records
    if record.get("audit_cycle") == 10
]
audited_mixed_development_cache = {
    (generic, record.get("indication")): record
    for generic, record in audited_mixed_development
}
mixed_regressions = set()
if HAS_PRIVATE_CACHE and len(audited_mixed_targets) != 12:
    mixed_regressions.add(
        f"expected 12 cycle-10 target/action records, found {len(audited_mixed_targets)}"
    )
if HAS_PRIVATE_CACHE and set(audited_mixed_target_cache) != set(AUDITED_MIXED_TARGETS_CYCLE_10):
    mixed_regressions.add("cycle-10 audited molecule/target identity set changed")
for key, expected_action in AUDITED_MIXED_TARGETS_CYCLE_10.items():
    record = audited_mixed_target_cache.get(key)
    edge = next((e for e in edges if e.get("rel") == "acts_on"
                 and (e.get("src"), e.get("dst")) == key), None)
    if (not edge or edge.get("action") != expected_action
            or not edge.get("source") or not edge.get("evidence")
            or (HAS_PRIVATE_CACHE and (
                not record or record.get("action") != expected_action
                or not record.get("source") or not record.get("evidence")
                or edge.get("source") != record.get("source")
                or edge.get("evidence") != record.get("evidence")
            ))):
        mixed_regressions.add(f"{key[0]} -> {key[1]} / {expected_action}")
if HAS_PRIVATE_CACHE and len(audited_mixed_development) != 12:
    mixed_regressions.add(
        f"expected 12 cycle-10 development records, found {len(audited_mixed_development)}"
    )
for key, record in audited_mixed_development_cache.items():
    edge = next((e for e in indication_edges
                 if (e.get("src"), e.get("dst")) == key), None)
    if (not edge or edge.get("rel") != "studied_for"
            or edge.get("intended_use") != record.get("intended_use")
            or edge.get("development_stage") != record.get("stage")
            or edge.get("study") != record.get("study")
            or edge.get("study_status") != record.get("study_status")
            or edge.get("status_as_of") != record.get("status_as_of")
            or edge.get("source") != record.get("source")
            or edge.get("evidence") != record.get("evidence")):
        mixed_regressions.add(f"{key[0]} -> {key[1]} development bundle")
if "azd5004" in mol:
    mixed_regressions.add("AZD5004 duplicated as a molecule instead of an elecoglipron alias")
elecoglipron = mol.get("elecoglipron", {})
if (elecoglipron.get("phase") != "pipeline"
        or not any("AZD5004" in brand for brand in elecoglipron.get("brands", []))):
    mixed_regressions.add("elecoglipron/AZD5004 canonical identity or pipeline status changed")
if mol.get("gefurulimab", {}).get("phase") != "pipeline":
    mixed_regressions.add("gefurulimab investigational portfolio status changed")
if mixed_regressions:
    add("ERROR", "audited-cycle-10-mixed-regression",
        "cycle-10 target, indication, phase, study status, provenance, or canonical identity was lost",
        mixed_regressions)

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
    (r"(?<!non-)\bpeptide\b|\b(?:insulins?|amylin|natriuretic)\b", {"peptide"}),
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
investigational_status_conflicts = set()
INVESTIGATIONAL_LANGUAGE = re.compile(
    r"\binvestigational\b|\bpipeline candidate\b|\bclinical-stage candidate\b|"
    r"\bcandidate in development\b",
    re.I,
)
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
        if c[5].lower() in {"marketed", "legacy"} and INVESTIGATIONAL_LANGUAGE.search(c[4]):
            investigational_status_conflicts.add(
                f"{generic} [{c[5].lower()}; source={c[4]}]"
            )

if investigational_status_conflicts:
    add("ERROR", "investigational-status-conflict",
        "source text describes an investigational pipeline candidate but status asserts approval",
        investigational_status_conflicts)

# d1) indication semantics that naive substring matching has previously broken.
# A bipolar-depression phrase describes bipolar disorder, not unipolar
# depression. A separate major/standalone depression clause may legitimately
# produce both edges, so strip bipolar phrases before looking for that evidence.
BIPOLAR_PHRASE = re.compile(
    r"\bbipolar(?:\s+[ivx]+)?(?:\s+(?:disorder|depression))?\b", re.I
)
bipolar_as_depression = set()
bronchitis_fallback = set()
indication_phrase_conflicts = set()
registry_aliases = []
for concept, record in indication_concepts.items():
    for alias in record.get("aliases", []):
        tokens = [re.escape(t) for t in re.split(r"[\s-]+", alias.lower()) if t]
        if tokens:
            registry_aliases.append((len(alias), concept, re.compile(
                r"(?<![a-z0-9])" + r"[\s-]+".join(tokens) + r"(?![a-z0-9])", re.I)))
registry_aliases.sort(key=lambda item: (-item[0], item[1]))
for generic, cells in idx_used_for.items():
    if generic not in mol or mol[generic].get("phase") == "failed":
        continue
    used_for = "; ".join(sorted(cells))
    without_bipolar = BIPOLAR_PHRASE.sub("", used_for)
    if ("bipolar" in used_for and "depression" in uses.get(generic, set())
            and "depress" not in without_bipolar):
        bipolar_as_depression.add(generic)
    if "bronchitis" in used_for and (
            "bronchitis" not in uses.get(generic, set())
            or "other" in uses.get(generic, set())):
        bronchitis_fallback.add(generic)
    observed = uses.get(generic, set())
    normalized_used = re.sub(r"[\u2010-\u2015]", "-", used_for.lower())
    remaining_exact = normalized_used
    required_exact = set()
    for _, concept, alias_pattern in registry_aliases:
        if alias_pattern.search(remaining_exact):
            required_exact.add(concept)
            remaining_exact = alias_pattern.sub(" ", remaining_exact)
    for concept in required_exact - observed:
        indication_phrase_conflicts.add(f"{generic} [missing exact concept {concept}]")

    without_psa = re.sub(r"\bpsoriatic arthritis\b|\bpsa\b", "", used_for, flags=re.I)
    if re.search(r"\bpsoriatic arthritis\b|\bpsa\b", used_for, re.I):
        if "psoriatic-arthritis" not in observed:
            indication_phrase_conflicts.add(f"{generic} [missing psoriatic-arthritis]")
        if "psoriasis" in observed and not re.search(r"\bpsoriasis\b", without_psa, re.I):
            indication_phrase_conflicts.add(f"{generic} [psoriatic arthritis became psoriasis]")

    without_uc = re.sub(r"\bulcerative colitis\b|\buc\b", "", used_for, flags=re.I)
    if re.search(r"\bulcerative colitis\b|\buc\b", used_for, re.I):
        if "ulcerative-colitis" not in observed:
            indication_phrase_conflicts.add(f"{generic} [missing ulcerative-colitis]")
        if "gi-other" in observed and not re.search(
                r"\b(?:constipation|reflux|peptic ulcer|gastric ulcer|duodenal ulcer|irritable bowel)\b",
                without_uc, re.I):
            indication_phrase_conflicts.add(f"{generic} [ulcerative colitis became gi-other]")
        if "ibd" in observed and not re.search(r"\binflammatory bowel disease\b|\bibd\b", without_uc, re.I):
            indication_phrase_conflicts.add(f"{generic} [ulcerative colitis flattened to ibd]")

    without_crohn = re.sub(r"\bcrohn(?:'s)?(?: disease)?\b", "", used_for, flags=re.I)
    if re.search(r"\bcrohn(?:'s)?(?: disease)?\b", used_for, re.I):
        if "crohns-disease" not in observed:
            indication_phrase_conflicts.add(f"{generic} [missing crohns-disease]")
        if "ibd" in observed and not re.search(r"\binflammatory bowel disease\b|\bibd\b", without_crohn, re.I):
            indication_phrase_conflicts.add(f"{generic} [Crohn disease flattened to ibd]")

    without_t1 = re.sub(r"\btype (?:1|i) diabetes(?: mellitus)?\b|\bt1d\b", "", used_for, flags=re.I)
    if re.search(r"\btype (?:1|i) diabetes(?: mellitus)?\b|\bt1d\b", used_for, re.I):
        if "type-1-diabetes" not in observed:
            indication_phrase_conflicts.add(f"{generic} [missing type-1-diabetes]")
        if "type-2-diabetes" in observed and not re.search(
                r"\btype (?:2|ii) diabetes(?: mellitus)?\b|\bt2d\b", without_t1, re.I):
            indication_phrase_conflicts.add(f"{generic} [type 1 diabetes became type 2]")

    if "overactive bladder" in used_for:
        if "urology-other" not in observed or "bladder-cancer" in observed:
            indication_phrase_conflicts.add(f"{generic} [overactive bladder confused with bladder cancer]")
    if "thyroid eye" in used_for:
        if "thyroid-eye-disease" not in observed or "retinal-disease" in observed:
            indication_phrase_conflicts.add(f"{generic} [thyroid eye disease confused with retinal disease]")
    without_thal = re.sub(r"\b(?:beta )?thalassemia\b", "", used_for, flags=re.I)
    if "thalassemia" in used_for:
        if "beta-thalassemia" not in observed:
            indication_phrase_conflicts.add(f"{generic} [missing beta-thalassemia]")
        if "sickle-cell" in observed and "sickle" not in without_thal:
            indication_phrase_conflicts.add(f"{generic} [thalassemia became sickle-cell]")
if bipolar_as_depression:
    add("ERROR", "bipolar-collapsed-to-depression",
        "bipolar terminology without a separate depression indication generated a depression edge",
        bipolar_as_depression)
if bronchitis_fallback:
    add("ERROR", "bronchitis-mapped-to-other",
        "drug-index text explicitly names bronchitis but the graph omits bronchitis or retains other",
        bronchitis_fallback)
if indication_phrase_conflicts:
    add("ERROR", "indication-specific-phrase-conflict",
        "specific source phrase was flattened, omitted, or mapped to an incompatible concept",
        indication_phrase_conflicts)

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

def _brand_group_key(s):
    s = re.sub(r"\s*\(.*?\)", "", str(s)).strip().strip("*").lower()
    s = re.sub(r"\s+franchise$", "", s)
    return re.sub(r"\s*([/+])\s*", r"\1", s)

def _brand_group_parts(s):
    return {p.strip() for p in re.split(r"[/+]", _brand_group_key(s)) if len(p.strip()) > 2}

_prose_sales = {}
_prose_sales_groups = set()
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
        _brand_cell = re.match(r"([^(]+)", _c[0]).group(1) if re.match(r"([^(]+)", _c[0]) else _c[0]
        _prose_sales_groups.add(_brand_group_key(_brand_cell))
        for _k in _brand_keys(_brand_cell):
            _prose_sales[_k] = _c[3]

# A combined franchise row is not component-level evidence. The fallback extractor may
# attach it to the one exact normalized brand group, but it must never copy the same
# aggregate onto multiple overlapping molecule nodes. Audited component records carry
# their own source boundaries and are intentionally excluded here.
duplicated_aggregate_sales = set()
for _group in _prose_sales_groups:
    _source_parts = _brand_group_parts(_group)
    if len(_source_parts) < 2:
        continue
    _matches = set()
    for _generic, _node in mol.items():
        if not _node.get("sales_2025_usd_bn") or _node.get("sales_2025_components"):
            continue
        if any(_brand_group_parts(_brand) <= _source_parts
               for _brand in (_node.get("brands") or [_generic])):
            _matches.add(_generic)
    if len(_matches) > 1:
        duplicated_aggregate_sales.add(f"{_group}: {', '.join(sorted(_matches))}")
if duplicated_aggregate_sales:
    add("ERROR", "aggregate-sales-copied-to-components",
        "one combined franchise sales row was copied onto multiple molecule nodes",
        duplicated_aggregate_sales)

_graph_keys = set()
for _g, _n in mol.items():
    if _n.get("sales_2025_usd_bn"):
        for _b in (_n.get("brands") or [_g]):
            _graph_keys |= _brand_keys(_b)
        for _component in _n.get("sales_2025_components") or []:
            _graph_keys |= _brand_keys(_component.get("label", ""))
def _sales_key_covered(key):
    if key in _graph_keys:
        return True
    parts = {p.strip() for p in re.split(r"[/+]", key) if len(p.strip()) > 2}
    return bool(parts) and parts <= _graph_keys
lost_sales = {k for k in _prose_sales if not _sales_key_covered(k)}
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

valid_failure_scopes = {
    "program-death", "indication-failure", "regional-failure", "trial-setback",
    "launch-failure", "launch-event",
}
bad_failure_scope = set()
for e in edges:
    if e.get("rel") != "failed_on":
        continue
    scope = e.get("scope")
    phase = mol.get(e["src"], {}).get("phase")
    if scope not in valid_failure_scopes:
        bad_failure_scope.add(f"{e['src']} -> {e['dst']} [scope={scope}]")
    elif scope == "program-death" and phase != "failed":
        bad_failure_scope.add(f"{e['src']} -> {e['dst']} [program-death but phase={phase}]")
    elif scope != "program-death" and phase == "failed":
        bad_failure_scope.add(
            f"{e['src']} -> {e['dst']} [{scope}, phase={phase}, indication={e.get('failed_indication')}]"
        )
    elif scope == "indication-failure" and not e.get("failed_indication"):
        bad_failure_scope.add(
            f"{e['src']} -> {e['dst']} [{scope} missing failed_indication]"
        )
    elif scope == "regional-failure" and (not e.get("failed_indication") or not e.get("territory")):
        bad_failure_scope.add(
            f"{e['src']} -> {e['dst']} [{scope} requires failed_indication and territory]"
        )
    elif scope == "trial-setback" and not e.get("active_program"):
        bad_failure_scope.add(
            f"{e['src']} -> {e['dst']} [{scope} requires active_program context]"
        )
if bad_failure_scope:
    add("ERROR", "failure-scope-conflict",
        "failed_on must distinguish molecule death from indication or launch failure",
        bad_failure_scope)

# A graveyard row's target/mechanism must agree with independently curated
# molecule targets when those targets are available. This catches copied
# mechanisms that otherwise remain internally self-consistent in the failure
# cache, as happened for olaratumab, voxelotor, and Opdualag.
def normalized_target(value):
    return re.sub(r"[^A-Za-z0-9]", "", str(value)).upper()


failure_target_conflicts = set()
for e in edges:
    if e.get("rel") != "failed_on" or not acts.get(e["src"]):
        continue
    observed = {normalized_target(target) for target in acts[e["src"]]}
    declared = {
        normalized_target(part)
        for part in re.split(r"\s+\+\s+", str(e.get("dst") or ""))
        if part.strip()
    }
    if not declared or not declared.issubset(observed):
        failure_target_conflicts.add(
            f"{e['src']} -> {e.get('dst')} [acts_on={', '.join(sorted(acts[e['src']]))}]"
        )
if failure_target_conflicts:
    add("ERROR", "failure-target-conflict",
        "graveyard failure target disagrees with independently curated acts_on targets",
        failure_target_conflicts)

live_aliases = {}
for generic, node in mol.items():
    if node.get("phase") == "failed":
        continue
    live_aliases[generic.lower()] = generic
    for brand in node.get("brands") or []:
        live_aliases[re.sub(r"\s*\(.*?\)", "", brand).lower().strip()] = generic
graveyard_live_deaths = set()
for key, record in graveyard.items():
    if record.get("entity_type", "molecule") != "molecule" or record.get("scope") != "program-death":
        continue
    label = re.sub(r"\s*\(.*?\)", "", str(record.get("molecule") or "")).lower().strip()
    resolved = live_aliases.get(key.lower()) or live_aliases.get(label)
    if resolved:
        graveyard_live_deaths.add(f"{key} -> {resolved}")
if graveyard_live_deaths:
    add("ERROR", "graveyard-live-program-death",
        "program-death record resolves to a marketed or pipeline molecule; narrow the failure scope",
        graveyard_live_deaths)

active_language_deaths = set()
for key, record in graveyard.items():
    if record.get("scope") != "program-death":
        continue
    note = str(record.get("note") or "")
    if re.search(
            r"\b(?:later approved|remains approved|remains active|continues? in|"
            r"active,? not recruiting|eu/japan approved|approved for [^.;]+ instead)\b",
            note, re.I):
        active_language_deaths.add(f"{key}: {note[:120]}")
if active_language_deaths:
    add("ERROR", "program-death-active-language",
        "program-death evidence itself describes an active or approved state; narrow the scope",
        active_language_deaths)

bad_competition_stage = set()
for e in edges:
    if e.get("rel") != "competes_with":
        continue
    expected = "+".join(sorted((mol.get(e["src"], {}).get("phase", "unknown"),
                                mol.get(e["dst"], {}).get("phase", "unknown"))))
    if e.get("stage_pair") != expected:
        bad_competition_stage.add(f"{e['src']} -> {e['dst']} [{e.get('stage_pair')} != {expected}]")
if bad_competition_stage:
    add("ERROR", "competition-stage-mismatch",
        "derived competition edges must preserve both molecules' current phases",
        bad_competition_stage)

# e) portfolio associations are broad provenance, never legal ownership claims
legacy_owns = {f"{e['src']} -> {e['dst']}" for e in edges if e["rel"] == "owns"}
if legacy_owns:
    add("ERROR", "legacy-owns-edge",
        "drug-index company cells must emit portfolio_includes, not unqualified legal ownership",
        legacy_owns)
portfolio_edges = [e for e in edges if e["rel"] == "portfolio_includes"]
bad_portfolio_provenance = {
    f"{e['src']} -> {e['dst']}" for e in portfolio_edges
    if not e.get("source") or not e.get("evidence")
    or not os.path.exists(os.path.join(ROOT, e["source"]))
}
if bad_portfolio_provenance:
    add("ERROR", "portfolio-association-missing-provenance",
        "portfolio associations require an existing source and exact company-cell evidence",
        bad_portfolio_provenance)
associated = {e["dst"] for e in portfolio_edges}
orphan = {g for g in mol if g not in associated and mol[g].get("phase") != "failed"}
if orphan:
    add("ERROR", "molecule-without-portfolio", "live molecule has no portfolio association", orphan)

typed_role_map = {
    "acquired_asset": "acquirer",
    "inherited_asset": "successor",
    "divested_asset": "seller",
    "licensed_asset": "licensee",
    "licensed_out": "licensor",
    "partnered_on": "partner",
}
typed_deal_types = {
    "acquired_asset": {"acquisition", "divestiture"},
    "inherited_asset": {"merger"},
    "divested_asset": {"divestiture", "acquisition"},
    "licensed_asset": {"license", "partnership"},
    "licensed_out": {"license", "partnership"},
    "partnered_on": {"partnership", "license"},
}
deal_parties = {(e["src"], e["dst"], e.get("role")) for e in edges if e["rel"] == "party_to"}
bad_typed_roles = set()
for e in edges:
    if e.get("rel") not in typed_role_map:
        continue
    did = e.get("via_deal")
    source = e.get("source", "")
    expected_role = typed_role_map[e["rel"]]
    if (not did or by_id.get(did, {}).get("kind") != "deal"
            or (e["src"], did, expected_role) not in deal_parties
            or by_id.get(did, {}).get("type") not in typed_deal_types[e["rel"]]
            or not source or not os.path.exists(os.path.join(ROOT, source))):
        bad_typed_roles.add(f"{e['src']} {e['rel']} {e['dst']} via {did}")
if bad_typed_roles:
    add("ERROR", "typed-asset-role-missing-provenance",
        "typed company-asset roles must agree with a sourced deal and party role",
        bad_typed_roles)

divested_pairs = {
    (e["src"], e["dst"]) for e in edges if e.get("rel") == "divested_asset"
}
bad_historical_portfolio = {
    f"{e['src']} -> {e['dst']}" for e in portfolio_edges
    if (e["src"], e["dst"]) in divested_pairs
    and (e.get("association_status") != "historical-divested" or not e.get("status_year"))
}
if bad_historical_portfolio:
    add("ERROR", "divested-portfolio-missing-history",
        "a divested portfolio association must be explicitly historical and dated",
        bad_historical_portfolio)

bad_deal_status = {
    n["id"] for n in nodes if n.get("kind") == "deal" and n.get("status")
    and n["status"] not in {"announced-pending", "closed"}
}
if bad_deal_status:
    add("ERROR", "invalid-deal-status", "deal status must use the controlled vocabulary", bad_deal_status)

explicit_deal_chronology = {
    n["id"]: n for n in nodes if n.get("kind") == "deal"
    and any(n.get(k) is not None for k in ("announced_year", "closed_year", "announcement_source"))
}
bad_deal_chronology = set()
for did, deal in explicit_deal_chronology.items():
    announced = deal.get("announced_year")
    closed = deal.get("closed_year")
    source = deal.get("announcement_source")
    if (not isinstance(announced, int) or deal.get("year") != announced
            or (closed is not None and (not isinstance(closed, int) or closed < announced))
            or not isinstance(source, str) or not source.startswith("https://")):
        bad_deal_chronology.add(did)
if bad_deal_chronology:
    add("ERROR", "deal-announcement-chronology-conflict",
        "explicit deal chronology must use the sourced announcement year; closing year is separate and cannot precede it",
        bad_deal_chronology)

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
cited_rich = {c for c in cited if sum(1 for e in edges if e["rel"] == "portfolio_includes" and e["src"] == c) >= 3}
if cited_rich:
    add("WARN", "cited-company-with-assets",
        "company has no KB file but is associated with 3+ portfolio assets — promote to players/", cited_rich)

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
    "with_real_indication": round(sum(1 for g in mol if uses.get(g, set()) - {"other"}) / n_mol, 3),
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
