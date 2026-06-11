"""
Counterparty Credit Risk Agent — Agent 2 in the WealthRisk pipeline.

Exposure methodology (v2 — CASS-aligned):
  • Broker accounts: settlement + margin exposure ≈ 15% of investable assets
    per account sleeve. Multiple sleeves with the same broker are SUMMED into
    a single counterparty exposure (unique-counterparty aggregation).
  • Custodians: client assets are ring-fenced under FCA CASS 6, so credit
    exposure is operational only ≈ 2% of assets under custody per custodian.
  • Product issuers (extra_counterparties): full notional — structured
    products and legacy notes carry direct issuer credit risk.

Risk checks per unique counterparty:
  1. Rating floor   — PD above BBB- threshold → HALT
  2. Concentration  — exposure > 40% of investable assets → HALT
  3. CDS spread     — > 100bps → REVIEW (soft alert, pipeline continues)

CVA proxy: CVA = Exposure × PD × LGD(45%)   [Basel III supervisory LGD]
"""

import json
import os

# ── Risk parameters ──────────────────────────────────────────────────────────
CONCENTRATION_LIMIT_PCT = 40.0   # max exposure to one counterparty, % of assets
CDS_ALERT_BPS           = 100    # CDS spread soft-alert threshold
RATING_FLOOR_PD         = 0.0200 # PD above this (~BBB-) → sub-investment grade
LGD                     = 0.45   # Basel III supervisory LGD

# ── Exposure weights (share of investable assets) ────────────────────────────
BROKER_EXPOSURE_PCT    = 0.15    # settlement + margin exposure per broker sleeve
CUSTODIAN_EXPOSURE_PCT = 0.02    # operational exposure only (CASS 6 ring-fencing)

COUNTERPARTY_DB = {
    "JPMorgan Chase": {"rating": "A+",   "cds_bps": 42,   "type": "prime_broker"},
    "UBS":            {"rating": "A",    "cds_bps": 58,   "type": "prime_broker"},
    "HSBC":           {"rating": "A",    "cds_bps": 61,   "type": "custodian"},
    "DBS Bank":       {"rating": "AA-",  "cds_bps": 35,   "type": "custodian"},
    "Barclays":       {"rating": "BBB+", "cds_bps": 89,   "type": "prime_broker"},
    "Vanguard":       {"rating": "AAA",  "cds_bps": 18,   "type": "fund_manager"},
    "BlackRock":      {"rating": "AA",   "cds_bps": 28,   "type": "fund_manager"},
    "Lehman Legacy":  {"rating": "D",    "cds_bps": 9999, "type": "product_issuer"},
}

RATING_PD = {
    "AAA": 0.0001, "AA+": 0.0002, "AA":  0.0003, "AA-": 0.0005,
    "A+":  0.0010, "A":   0.0015, "A-":  0.0020,
    "BBB+":0.0050, "BBB": 0.0100, "BBB-":0.0200,
    "BB":  0.0800, "B":   0.2500, "D":   1.0000,
}

_client = None  # lazy — lets tests import this module without an API key


def _get_client():
    global _client
    if _client is None:
        from anthropic import Anthropic
        _client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


# ── Pure, deterministic core (unit-testable, no LLM) ─────────────────────────

def compute_exposures(profile: dict) -> dict:
    """Aggregate credit exposure per UNIQUE counterparty name."""
    assets     = profile.get("investable_assets", 0)
    brokers    = profile.get("brokers", []) or []
    custodians = profile.get("custodians", []) or []
    extra_cps  = profile.get("extra_counterparties", {}) or {}

    exposure: dict[str, float] = {}
    for b in brokers:                      # each list entry = one account sleeve
        exposure[b] = exposure.get(b, 0.0) + assets * BROKER_EXPOSURE_PCT
    for c in custodians:                   # CASS 6: operational exposure only
        exposure[c] = exposure.get(c, 0.0) + assets * CUSTODIAN_EXPOSURE_PCT
    for cp, notional in extra_cps.items(): # issuer risk = full notional
        exposure[cp] = exposure.get(cp, 0.0) + float(notional)
    return exposure


def assess_counterparties(profile: dict) -> dict:
    """Run all risk checks. Returns dict with cleared/results/alerts/total_cva."""
    assets    = profile.get("investable_assets", 0)
    results   = {}
    alerts    = []
    total_cva = 0.0
    cleared   = True

    for cp_name, exposure in compute_exposures(profile).items():
        db     = COUNTERPARTY_DB.get(cp_name)
        rating = db["rating"] if db else "NR"
        pd_    = RATING_PD.get(rating, 0.05)          # unrated → conservative 5%
        cds    = db["cds_bps"] if db else 0
        cva    = exposure * pd_ * LGD
        conc   = round(exposure / assets * 100, 1) if assets > 0 else 0.0
        total_cva += cva

        cp_alerts, status = [], "PASS"

        if pd_ > RATING_FLOOR_PD:
            status, cleared = "HALT", False
            cp_alerts.append(f"Rating {rating} below BBB- floor")
            alerts.append(f"CRITICAL: {cp_name} rated {rating} — sub-investment-grade")
        if conc > CONCENTRATION_LIMIT_PCT:
            status, cleared = "HALT", False
            cp_alerts.append(f"Concentration {conc}% exceeds {CONCENTRATION_LIMIT_PCT}% limit")
            alerts.append(f"BREACH: {cp_name} at {conc:.1f}% — exceeds {CONCENTRATION_LIMIT_PCT}% limit")
        if cds > CDS_ALERT_BPS:
            if status == "PASS":
                status = "REVIEW"
            cp_alerts.append(f"CDS {cds}bps — elevated stress signal")
            alerts.append(f"CDS ALERT: {cp_name} spread {cds}bps")

        results[cp_name] = {
            "exposure":      round(exposure, 2),
            "concentration": conc,
            "rating":        rating,
            "pd_pct":        round(pd_ * 100, 4),
            "cva":           round(cva, 2),
            "cds_bps":       cds,
            "status":        status,
            "alerts":        cp_alerts,
        }

    return {
        "cleared":        cleared,
        "counterparties": results,
        "alerts":         alerts,
        "total_cva":      round(total_cva, 2),
    }


# ── LangGraph node (LLM narrative layered on top, with graceful fallback) ────

def run_counterparty_check(state: dict) -> dict:
    profile    = state["client_profile"]
    assessment = assess_counterparties(profile)

    try:
        prompt = f"""
You are a senior credit risk officer. Write 2 sentences summarising
the counterparty risk for {profile['name']}.
Results: {json.dumps(assessment['counterparties'], indent=2)}
Alerts: {assessment['alerts']}
Total CVA: {assessment['total_cva']:,.2f}
Be direct. Mention specific counterparty names. No bullet points.
"""
        narrative = _get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        ).content[0].text
    except Exception as exc:  # API outage must never crash the pipeline
        n = len(assessment["alerts"])
        narrative = (
            f"Automated summary: {len(assessment['counterparties'])} counterparties "
            f"assessed, {n} alert(s) raised, total CVA £{assessment['total_cva']:,.2f}. "
            f"(Narrative generation unavailable: {type(exc).__name__})"
        )

    assessment["narrative"] = narrative
    state["counterparty_result"] = assessment
    state["audit_trail"].append({
        "agent":  "counterparty_check",
        "result": "CLEARED" if assessment["cleared"] else "FLAGGED",
        "detail": f"{len(assessment['alerts'])} alerts | CVA {assessment['total_cva']:,.2f}",
    })
    return state
