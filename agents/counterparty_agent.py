# agents/counterparty_agent.py
# WealthRisk Agent — Counterparty Credit Risk
# Inserts between aml_check and suitability in orchestrator.py

from anthropic import Anthropic
import json
import os

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── Counterparty database ─────────────────────────────────────
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

CONCENTRATION_LIMIT = 25.0   # % max per counterparty
CDS_ALERT_BPS       = 100    # flag if spread exceeds
RATING_FLOOR_PD     = 0.0200 # BBB- minimum

def run_counterparty_check(state: dict) -> dict:
    """
    Counterparty credit risk agent.
    Takes state dict, mutates it, returns it — matches your existing agent pattern.
    """
    profile    = state["client_profile"]
    assets     = profile.get("investable_assets", 0)
    brokers    = profile.get("brokers", ["JPMorgan Chase"])
    custodians = profile.get("custodians", ["HSBC"])
    extra_cps  = profile.get("extra_counterparties", {})

    # Build exposure map
    cp_exposure = {}
    broker_share = assets / len(brokers) if brokers else 0
    cust_share   = assets / len(custodians) if custodians else 0
    for b in brokers:
        cp_exposure[b] = cp_exposure.get(b, 0) + broker_share * 0.5
    for c in custodians:
        cp_exposure[c] = cp_exposure.get(c, 0) + cust_share * 0.5
    for cp, amt in extra_cps.items():
        cp_exposure[cp] = cp_exposure.get(cp, 0) + amt

    results   = {}
    alerts    = []
    total_cva = 0.0
    cleared   = True

    for cp_name, exposure in cp_exposure.items():
        db     = COUNTERPARTY_DB.get(cp_name)
        rating = db["rating"] if db else "NR"
        pd     = RATING_PD.get(rating, 0.05)
        cva    = exposure * pd * 0.45
        conc   = round((exposure / assets * 100), 1) if assets > 0 else 0
        cds    = db["cds_bps"] if db else 0
        total_cva += cva
        cp_alerts = []
        status = "PASS"

        if pd > RATING_FLOOR_PD:
            status = "HALT"; cleared = False
            cp_alerts.append(f"Rating {rating} below BBB- floor")
            alerts.append(f"CRITICAL: {cp_name} rated {rating} — sub-investment-grade")
        if conc > CONCENTRATION_LIMIT:
            status = "HALT"; cleared = False
            cp_alerts.append(f"Concentration {conc}% exceeds {CONCENTRATION_LIMIT}% limit")
            alerts.append(f"BREACH: {cp_name} at {conc:.1f}% — exceeds {CONCENTRATION_LIMIT}% limit")
        if cds > CDS_ALERT_BPS:
            if status == "PASS": status = "REVIEW"
            cp_alerts.append(f"CDS {cds}bps — elevated stress signal")
            alerts.append(f"CDS ALERT: {cp_name} spread {cds}bps")

        results[cp_name] = {
            "exposure":       round(exposure, 2),
            "concentration":  conc,
            "rating":         rating,
            "pd_pct":         round(pd * 100, 4),
            "cva":            round(cva, 2),
            "cds_bps":        cds,
            "status":         status,
            "alerts":         cp_alerts,
        }

    # Claude narrative
    narrative_prompt = f"""
You are a senior credit risk officer. Write 2 sentences summarising
the counterparty risk for {profile['name']}.
Results: {json.dumps(results, indent=2)}
Alerts: {alerts}
Total CVA: £{total_cva:,.2f}
Be direct. Mention specific counterparty names. No bullet points.
"""
    narrative = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": narrative_prompt}]
    ).content[0].text

    cp_result = {
        "cleared":        cleared,
        "counterparties": results,
        "alerts":         alerts,
        "total_cva":      round(total_cva, 2),
        "narrative":      narrative,
    }

    state["counterparty_result"] = cp_result
    state["audit_trail"].append({
        "agent":  "counterparty_check",
        "result": "CLEARED" if cleared else "FLAGGED",
        "detail": f"{len(alerts)} alerts | CVA £{total_cva:,.2f}",
    })
    return state
