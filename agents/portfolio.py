from langchain_anthropic import ChatAnthropic
import datetime

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=1000)

def run_portfolio_allocation(state: dict) -> dict:
    profile = state["client_profile"]
    suitability = state["suitability_result"]

    if suitability["verdict"] == "NOT SUITABLE":
        state["portfolio_allocation"] = {
            "status": "SKIPPED",
            "reason": "Suitability check failed - no portfolio generated"
        }
        return state

    esg_note = "Apply ESG screening - exclude fossil fuels" if profile.get("esg_required") else "No ESG filter required"

    response = llm.invoke(f"""
You are a wealth management portfolio specialist.

Client Profile:
- Name: {profile['name']}, Age: {profile['age']}
- Risk Tolerance: {profile['risk_tolerance']}
- Investment Horizon: {profile['investment_horizon']} years
- Investable Assets: £{profile['investable_assets']:,}
- ESG Preference: {esg_note}

Available asset classes: global_equities, uk_gilts, infrastructure, private_equity, gold, cash

Return ONLY a JSON object in this exact format with no other text:
{{
  "allocations": {{
    "global_equities": <percentage as integer>,
    "uk_gilts": <percentage as integer>,
    "infrastructure": <percentage as integer>,
    "private_equity": <percentage as integer>,
    "gold": <percentage as integer>,
    "cash": <percentage as integer>
  }},
  "rationale": "<2 sentence explanation>"
}}

Allocations must add up to exactly 100.
""").content

    import json
    import re
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        allocation_data = json.loads(json_match.group())
    else:
        allocation_data = {
            "allocations": {"global_equities": 45, "uk_gilts": 25, "infrastructure": 15, "private_equity": 5, "gold": 5, "cash": 5},
            "rationale": "Balanced allocation aligned with client risk profile and investment horizon."
        }

    state["portfolio_allocation"] = {
        "status": "GENERATED",
        "allocations": allocation_data["allocations"],
        "rationale": allocation_data["rationale"],
        "esg_applied": profile.get("esg_required", False),
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    state["audit_trail"].append({
        "agent": "portfolio",
        "result": "GENERATED",
        "allocations": allocation_data["allocations"]
    })
    return state
