from data.scenarios import SCENARIOS
import datetime

def run_stress_test(state: dict) -> dict:
    portfolio = state["portfolio_allocation"]
    profile = state["client_profile"]

    if portfolio.get("status") == "SKIPPED":
        state["stress_test_result"] = {"status": "SKIPPED", "reason": "No portfolio to stress test"}
        return state

    scenario_key = profile.get("scenario", "oil_shock")
    scenario = SCENARIOS[scenario_key]
    allocations = portfolio["allocations"]

    total_impact = 0
    asset_impacts = {}

    for asset, pct in allocations.items():
        scenario_impact = scenario["impacts"].get(asset, 0)
        weighted_impact = (pct / 100) * scenario_impact
        total_impact += weighted_impact
        asset_impacts[asset] = {
            "allocation_pct": pct,
            "scenario_impact_pct": round(scenario_impact * 100, 1),
            "weighted_impact_pct": round(weighted_impact * 100, 2)
        }

    total_pct = round(total_impact * 100, 2)
    max_drawdown = profile.get("max_drawdown_tolerance", -15)
    breach = total_pct < max_drawdown

    state["stress_test_result"] = {
        "status": "COMPLETED",
        "scenario": scenario["name"],
        "scenario_description": scenario["description"],
        "asset_impacts": asset_impacts,
        "total_portfolio_impact_pct": total_pct,
        "max_drawdown_tolerance_pct": max_drawdown,
        "breach": breach,
        "breach_message": f"WARNING: Impact {total_pct}% exceeds tolerance {max_drawdown}%" if breach else "Within tolerance",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    state["audit_trail"].append({
        "agent": "stress_test",
        "scenario": scenario["name"],
        "total_impact": total_pct,
        "breach": breach
    })
    return state
