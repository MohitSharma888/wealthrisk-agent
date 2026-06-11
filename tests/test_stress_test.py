"""Stress test agent — deterministic math verification. No API key required."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.stress_test import run_stress_test


def make_state(allocations, scenario="oil_shock", drawdown=-15):
    return {
        "client_profile": {"name": "Test", "scenario": scenario,
                           "max_drawdown_tolerance": drawdown},
        "portfolio_allocation": {"status": "GENERATED", "allocations": allocations},
        "audit_trail": [],
    }


def test_weighted_impact_sums_correctly():
    state = make_state({"global_equities": 50, "cash": 50})
    result = run_stress_test(state)["stress_test_result"]
    impacts = result["asset_impacts"]
    total = sum(v["weighted_impact_pct"] for v in impacts.values())
    assert abs(total - result["total_portfolio_impact_pct"]) < 0.05


def test_breach_fires_when_impact_exceeds_tolerance():
    state = make_state({"global_equities": 100}, drawdown=-1)
    result = run_stress_test(state)["stress_test_result"]
    assert result["breach"] is True


def test_skipped_portfolio_skips_stress():
    state = {
        "client_profile": {"name": "Halted"},
        "portfolio_allocation": {"status": "SKIPPED", "reason": "halt"},
        "audit_trail": [],
    }
    result = run_stress_test(state)["stress_test_result"]
    assert result["status"] == "SKIPPED"


def test_all_cash_portfolio_within_tolerance():
    state = make_state({"cash": 100})
    result = run_stress_test(state)["stress_test_result"]
    assert result["breach"] is False
