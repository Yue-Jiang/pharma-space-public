#!/usr/bin/env python3
"""ctgov_failures.py — mine ClinicalTrials.gov for terminated drug programs.

Queries the CT.gov API v2 for INTERVENTIONAL Phase 2/3 studies with
overallStatus TERMINATED | WITHDRAWN | SUSPENDED for each lead sponsor,
clusters results by intervention name (a drug appearing in multiple
terminated trials = stronger program-death signal), and classifies the
whyStopped free text into coarse failure modes.

Stdlib only (urllib, json, re, time). Polite: >=0.5s between requests.

Usage:
    python ctgov_failures.py                 # run for the built-in 22 sponsor groups
    python ctgov_failures.py --out ctgov_raw.json

Caveats (read before trusting output):
  * CT.gov records trials, not programs. Terminated != program dead
    (most Ph3 efficacy failures COMPLETE normally and just never file).
    Treat clusters as candidate signals for verification, not ground truth.
  * whyStopped is free text and often missing/euphemistic ("business
    reasons" frequently means efficacy). Keyword classification is coarse.
  * Registry coverage starts ~2007-2008 (FDAAA); older corpses are invisible.
"""

import json
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://clinicaltrials.gov/api/v2/studies"
RATE_LIMIT_S = 0.5
PAGE_SIZE = 200

# canonical sponsor -> list of lead-sponsor name searches (current + historical)
SPONSOR_GROUPS = {
    "Pfizer": ["Pfizer"],
    "Merck & Co": ["Merck Sharp & Dohme"],
    "Johnson & Johnson": ["Janssen", "Johnson & Johnson"],
    "Roche": ["Hoffmann-La Roche", "Genentech", "Roche"],
    "Novartis": ["Novartis"],
    "AstraZeneca": ["AstraZeneca"],
    "Bristol-Myers Squibb": ["Bristol-Myers Squibb", "Celgene"],
    "Sanofi": ["Sanofi", "Genzyme"],
    "GSK": ["GlaxoSmithKline"],
    "AbbVie": ["AbbVie"],
    "Amgen": ["Amgen"],
    "Gilead": ["Gilead Sciences"],
    "Eli Lilly": ["Eli Lilly"],
    "Novo Nordisk": ["Novo Nordisk"],
    "Takeda": ["Takeda", "Shire", "Millennium Pharmaceuticals"],
    "Boehringer Ingelheim": ["Boehringer Ingelheim"],
    "Bayer": ["Bayer"],
    "Daiichi Sankyo": ["Daiichi Sankyo"],
    "Vertex": ["Vertex Pharmaceuticals"],
    "Regeneron": ["Regeneron"],
    "Biogen": ["Biogen"],
    "Moderna": ["ModernaTX", "Moderna"],
}

FIELDS = ",".join([
    "protocolSection.identificationModule.nctId",
    "protocolSection.identificationModule.briefTitle",
    "protocolSection.statusModule.overallStatus",
    "protocolSection.statusModule.whyStopped",
    "protocolSection.statusModule.startDateStruct",
    "protocolSection.statusModule.lastUpdatePostDateStruct",
    "protocolSection.sponsorCollaboratorsModule.leadSponsor",
    "protocolSection.designModule.phases",
    "protocolSection.designModule.studyType",
    "protocolSection.armsInterventionsModule.interventions",
    "protocolSection.conditionsModule.conditions",
])


def _get(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 - retry then re-raise
            if attempt == retries - 1:
                raise
            time.sleep(2.0 * (attempt + 1))
    return None


def fetch_sponsor(lead_name):
    """All TERMINATED/WITHDRAWN/SUSPENDED interventional Ph2/Ph3 trials
    whose lead sponsor matches `lead_name` (CT.gov query.lead search)."""
    studies = []
    page_token = None
    while True:
        params = {
            "query.lead": lead_name,
            "filter.overallStatus": "TERMINATED|WITHDRAWN|SUSPENDED",
            "filter.advanced": (
                "AREA[StudyType]INTERVENTIONAL AND "
                "(AREA[Phase]PHASE2 OR AREA[Phase]PHASE3)"
            ),
            "fields": FIELDS,
            "pageSize": str(PAGE_SIZE),
        }
        if page_token:
            params["pageToken"] = page_token
        url = API + "?" + urllib.parse.urlencode(params)
        data = _get(url)
        studies.extend(data.get("studies", []))
        page_token = data.get("nextPageToken")
        time.sleep(RATE_LIMIT_S)
        if not page_token:
            break
    return studies


def flatten(study):
    p = study.get("protocolSection", {})
    ident = p.get("identificationModule", {})
    status = p.get("statusModule", {})
    design = p.get("designModule", {})
    arms = p.get("armsInterventionsModule", {})
    conds = p.get("conditionsModule", {})
    lead = p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {})
    return {
        "nctId": ident.get("nctId"),
        "briefTitle": ident.get("briefTitle"),
        "overallStatus": status.get("overallStatus"),
        "whyStopped": status.get("whyStopped"),
        "startDate": (status.get("startDateStruct") or {}).get("date"),
        "lastUpdateDate": (status.get("lastUpdatePostDateStruct") or {}).get("date"),
        "leadSponsor": lead.get("name"),
        "phases": design.get("phases") or [],
        "interventions": [
            i.get("name") for i in (arms.get("interventions") or [])
            if i.get("type") in (None, "DRUG", "BIOLOGICAL", "GENETIC", "COMBINATION_PRODUCT")
            and i.get("name")
        ],
        "conditions": conds.get("conditions") or [],
    }


# ---------- whyStopped classification ----------

REASON_RULES = [
    ("safety", r"safet|adverse|toxicit|tolerab|risk[- /]benefit|benefit[- /]risk|dsmb|data safety|serious ae|sae"),
    ("efficacy", r"efficac|futilit|lack of (?:clinical )?(?:activity|effect|response|benefit)|insufficient (?:activity|effect|response)|did not meet|primary endpoint|no (?:clinical )?benefit|interim analys"),
    ("covid", r"covid|pandemic|sars[- ]cov"),
    ("enrollment", r"enrol|recruit|accrual|no (?:eligible )?(?:patients|subjects)|low (?:patient )?participation"),
    ("business", r"business|strateg|sponsor(?:'s)? decision|commercial|portfolio|prioriti|funding|financial|resource|program (?:was )?(?:discontinued|terminated)|development (?:of .{0,60})?(?:was )?(?:discontinued|halted|stopped)|company decision|merger|acquisition"),
]


def classify_reason(text):
    if not text or not text.strip():
        return "other-unknown"
    t = text.lower()
    for label, pat in REASON_RULES:
        if re.search(pat, t):
            return label
    return "other-unknown"


# ---------- intervention clustering ----------

NOISE_INTERVENTIONS = re.compile(
    r"^(placebo|vehicle|saline|standard of care|soc|best supportive care|"
    r"chemotherapy|observation|sham|comparator|control)\b", re.I)

STRIP_PAT = re.compile(
    r"\s*\((?:[^)]*)\)|\s*\d+(?:\.\d+)?\s*(?:mg|mcg|ug|g|ml|%)(?:/\w+)?|"
    r"\s+(?:tablets?|capsules?|injection|infusion|oral|iv|sc|solution|dose[sd]?)\b",
    re.I)


def norm_intervention(name):
    n = STRIP_PAT.sub("", name).strip().strip(",;")
    n = re.sub(r"\s+", " ", n)
    return n.lower()


def cluster(records, canonical_sponsor):
    clusters = {}
    for r in records:
        seen = set()
        for iv in r["interventions"]:
            key = norm_intervention(iv)
            if not key or len(key) < 3 or NOISE_INTERVENTIONS.match(key) or key in seen:
                continue
            seen.add(key)
            c = clusters.setdefault(key, {
                "intervention": key, "sponsor": canonical_sponsor,
                "n_terminated": 0, "phases": set(), "trials": [],
                "reasons": {}, "example_whyStopped": None, "example_nctId": None,
            })
            c["n_terminated"] += 1
            c["phases"].update(r["phases"])
            c["trials"].append(r["nctId"])
            reason = classify_reason(r["whyStopped"])
            c["reasons"][reason] = c["reasons"].get(reason, 0) + 1
            if r["whyStopped"] and (c["example_whyStopped"] is None
                                    or len(r["whyStopped"]) > len(c["example_whyStopped"])):
                c["example_whyStopped"] = r["whyStopped"]
                c["example_nctId"] = r["nctId"]
            if c["example_nctId"] is None:
                c["example_nctId"] = r["nctId"]
    out = []
    for c in clusters.values():
        c["phases"] = sorted(c["phases"])
        # dominant classified reason across the cluster's trials
        c["classified_reason"] = max(c["reasons"].items(), key=lambda kv: kv[1])[0]
        out.append(c)
    out.sort(key=lambda c: (-c["n_terminated"], c["intervention"]))
    return out


def main(out_path="ctgov_raw.json"):
    result = {"pulled_at": time.strftime("%Y-%m-%d"), "sponsors": {}}
    for canonical, variants in SPONSOR_GROUPS.items():
        records, seen_nct = [], set()
        for v in variants:
            studies = fetch_sponsor(v)
            for s in studies:
                r = flatten(s)
                if r["nctId"] in seen_nct:
                    continue
                seen_nct.add(r["nctId"])
                records.append(r)
            print(f"  {canonical} [{v}]: +{len(studies)} (total {len(records)})",
                  file=sys.stderr)
        result["sponsors"][canonical] = {
            "trials": records,
            "clusters": cluster(records, canonical),
        }
    with open(out_path, "w") as f:
        json.dump(result, f, indent=1)
    print(f"wrote {out_path}", file=sys.stderr)
    return result


if __name__ == "__main__":
    out = "ctgov_raw.json"
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    main(out)
