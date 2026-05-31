from langchain_anthropic import ChatAnthropic
from data.fca_rules import RISK_LEVELS
import datetime

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=1000)

def run_suitability_check(state: dict) -> dict:
    profile = state["client_profile"]
    checks = []
    passed = True

    # COBS 9A.2.6 - Financial capacity check
    assets = profile["investable_assets"]
    income = profile["annual_income"]
    cobs_926 = {
        "rule": "COBS 9A.2.6",
        "description": "Financial capacity - assets vs income",
        "pass": assets >= income * 3,
        "detail": f"Assets £{assets:,} vs 3x Income £{income*3:,}"
    }
    checks.append(cobs_926)
    if not cobs_926["pass"]:
        passed = False

    # COBS 9A.2.7 - Risk alignment check
    client_risk = RISK_LEVELS.get(profile["risk_tolerance"], 0)
    proposed_risk = RISK_LEVELS.get(profile["proposed_strategy"], 0)
    cobs_927 = {
        "rule": "COBS 9A.2.7",
        "description": "Investment objectives alignment",
        "pass": abs(client_risk - proposed_risk) <= 1,
        "detail": f"Client risk: {profile['risk_tolerance']} ({client_risk}) | Proposed: {profile['proposed_strategy']} ({proposed_risk})"
    }
    checks.append(cobs_927)
    if not cobs_927["pass"]:
        passed = False

    # COBS 2.1.1 - Best interest check
    cobs_211 = {
        "rule": "COBS 2.1.1",
        "description": "Consumer Duty - act in client best interest",
        "pass": profile["investment_horizon"] >= 3,
        "detail": f"Investment horizon: {profile['investment_horizon']} years"
    }
    checks.append(cobs_211)
    if not cobs_211["pass"]:
        passed = False

    # AI generates plain English explanation
    verdict = "SUITABLE" if passed else "NOT SUITABLE"
    explanation = llm.invoke(f"""
You are an FCA-compliant wealth management advisor writing a suitability assessment.

Client: {profile['name']}, Age: {profile['age']}
Investable Assets: £{profile['investable_assets']:,}
Annual Income: £{profile['annual_income']:,}
Risk Tolerance: {profile['risk_tolerance']}
Proposed Strategy: {profile['proposed_strategy']}
Investment Horizon: {profile['investment_horizon']} years

FCA Rules Checked: {checks}
Overall Verdict: {verdict}

Write a professional 2-paragraph suitability explanation for the client file.
Reference the specific FCA rules. Use plain English, not jargon.
Keep it under 150 words.
""").content

    state["suitability_result"] = {
        "verdict": verdict,
        "checks": checks,
        "explanation": explanation,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    state["audit_trail"].append({
        "agent": "suitability",
        "result": verdict,
        "rules_checked": [c["rule"] for c in checks],
        "all_passed": passed
    })
    return state
