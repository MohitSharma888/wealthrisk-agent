from langchain_anthropic import ChatAnthropic
import datetime
import json

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=2000)

def generate_report(state: dict) -> dict:
    profile = state["client_profile"]
    aml = state["aml_result"]
    suitability = state["suitability_result"]
    portfolio = state["portfolio_allocation"]
    stress = state["stress_test_result"]

    report = llm.invoke(f"""
You are an FCA-compliant wealth management compliance officer.
Generate a professional client suitability report.

CLIENT: {profile['name']} | Age: {profile['age']} | Assets: £{profile['investable_assets']:,}
AML STATUS: {'CLEARED' if aml['cleared'] else 'FLAGGED'}
SUITABILITY: {suitability['verdict']}
SUITABILITY EXPLANATION: {suitability['explanation']}
PORTFOLIO: {json.dumps(portfolio.get('allocations', {}), indent=2)}
PORTFOLIO RATIONALE: {portfolio.get('rationale', 'N/A')}
STRESS TEST: {stress.get('scenario', 'N/A')} | Impact: {stress.get('total_portfolio_impact_pct', 'N/A')}% | Breach: {stress.get('breach', False)}

Write a formal compliance report with these sections:
1. EXECUTIVE SUMMARY
2. CLIENT PROFILE SUMMARY
3. AML CLEARANCE STATUS
4. SUITABILITY ASSESSMENT
5. PORTFOLIO RECOMMENDATION
6. STRESS TEST RESULTS
7. COMPLIANCE SIGN-OFF

Keep it professional, reference FCA rules where relevant, under 400 words.
""").content

    state["final_report"] = report
    state["audit_trail"].append({
        "agent": "report",
        "result": "GENERATED",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "word_count": len(report.split())
    })
    return state
