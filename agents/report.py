from langchain_anthropic import ChatAnthropic
import datetime
import json

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=2000)

def generate_report(state: dict) -> dict:
    profile    = state["client_profile"]
    aml        = state["aml_result"]
    cp         = state.get("counterparty_result")
    suitability= state["suitability_result"]
    portfolio  = state["portfolio_allocation"]
    stress     = state["stress_test_result"]

    # Determine halt reason for early-exit pipelines
    halt_reason = "N/A"
    if not aml["cleared"]:
        halt_reason = f"AML FLAG — {aml.get('flag', 'sanctions match detected')}"
    elif cp and not cp["cleared"]:
        halt_reason = f"COUNTERPARTY HALT — {'; '.join(cp.get('alerts', ['breach detected']))}"

    # Safe accessors — handle None for skipped agents
    suit_verdict     = suitability["verdict"]        if suitability else "SKIPPED"
    suit_explanation = suitability["explanation"]    if suitability else "Pipeline halted before suitability check."
    port_allocations = json.dumps(portfolio.get("allocations", {}), indent=2) if portfolio else "N/A — pipeline halted"
    port_rationale   = portfolio.get("rationale", "N/A") if portfolio else "N/A"
    stress_scenario  = stress.get("scenario", "N/A")                   if stress else "N/A"
    stress_impact    = stress.get("total_portfolio_impact_pct", "N/A")  if stress else "N/A"
    stress_breach    = stress.get("breach", False)                      if stress else False
    cp_summary       = f"CVA £{cp['total_cva']:,.2f} | Alerts: {len(cp['alerts'])} | Status: {'CLEARED' if cp['cleared'] else 'HALTED'}" if cp else "Not assessed"

    report = llm.invoke(f"""
You are an FCA-compliant wealth management compliance officer.
Generate a professional client suitability report.

CLIENT: {profile['name']} | Age: {profile['age']} | Assets: £{profile['investable_assets']:,}
AML STATUS: {'CLEARED' if aml['cleared'] else 'FLAGGED'}
COUNTERPARTY RISK: {cp_summary}
HALT REASON: {halt_reason}
SUITABILITY: {suit_verdict}
SUITABILITY EXPLANATION: {suit_explanation}
PORTFOLIO: {port_allocations}
PORTFOLIO RATIONALE: {port_rationale}
STRESS TEST: {stress_scenario} | Impact: {stress_impact}% | Breach: {stress_breach}

Write a formal compliance report with these sections:
1. EXECUTIVE SUMMARY
2. CLIENT PROFILE SUMMARY
3. AML CLEARANCE STATUS
4. COUNTERPARTY RISK ASSESSMENT
5. SUITABILITY ASSESSMENT
6. PORTFOLIO RECOMMENDATION
7. STRESS TEST RESULTS
8. COMPLIANCE SIGN-OFF

If the pipeline was halted early, clearly state the halt reason in the Executive Summary
and mark skipped sections as NOT ASSESSED due to pipeline halt.
Keep it professional, reference FCA rules where relevant, under 500 words.
""").content

    state["final_report"] = report
    state["audit_trail"].append({
        "agent":  "report",
        "result": "COMPLETED",
        "detail": f"Report generated at {datetime.datetime.now().isoformat()}",
    })
    return state
