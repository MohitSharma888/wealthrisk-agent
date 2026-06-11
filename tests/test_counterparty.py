"""
Counterparty agent unit tests — verifies every demo client produces the
intended pipeline outcome. Pure logic only; no API key required.

Run:  pytest tests/ -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.counterparty_agent import (
    assess_counterparties,
    compute_exposures,
    CONCENTRATION_LIMIT_PCT,
)

# ── Demo client fixtures (mirror app.py maps) ────────────────────────────────

SARAH = {"name": "Sarah Mitchell", "investable_assets": 2_500_000,
         "brokers": ["JPMorgan Chase"], "custodians": ["DBS Bank"],
         "extra_counterparties": {}}

JAMES = {"name": "James Thornton", "investable_assets": 380_000,
         "brokers": ["JPMorgan Chase"], "custodians": ["HSBC"],
         "extra_counterparties": {}}

VIKTOR = {"name": "Viktor Petrov", "investable_assets": 1_000_000,
          "brokers": ["UBS"], "custodians": ["HSBC"],
          "extra_counterparties": {}}

PRIYA = {"name": "Priya Sharma", "investable_assets": 800_000,
         "brokers": ["JPMorgan Chase"], "custodians": ["HSBC"],
         "extra_counterparties": {}}

DAVID = {"name": "David Chen", "investable_assets": 1_500_000,
         "brokers": ["JPMorgan Chase"], "custodians": ["DBS Bank"],
         "extra_counterparties": {}}

MARCUS = {"name": "Marcus Webb", "investable_assets": 950_000,
          "brokers": ["Barclays", "Barclays", "Barclays"],
          "custodians": ["Barclays"], "extra_counterparties": {}}

HELENA = {"name": "Helena Zhao", "investable_assets": 1_200_000,
          "brokers": ["JPMorgan Chase", "UBS"], "custodians": ["HSBC"],
          "extra_counterparties": {"Lehman Legacy": 350_000}}


# ── Clean-pass clients must clear the counterparty gate ──────────────────────

def test_sarah_clears():
    assert assess_counterparties(SARAH)["cleared"] is True

def test_james_clears_counterparty_gate():
    # James fails COBS later — counterparty must NOT be what halts him
    assert assess_counterparties(JAMES)["cleared"] is True

def test_viktor_priya_david_clear():
    for p in (VIKTOR, PRIYA, DAVID):
        assert assess_counterparties(p)["cleared"] is True, p["name"]


# ── Marcus Webb: Barclays concentration breach ───────────────────────────────

def test_marcus_halts_on_concentration():
    r = assess_counterparties(MARCUS)
    assert r["cleared"] is False
    barclays = r["counterparties"]["Barclays"]
    assert barclays["status"] == "HALT"
    assert barclays["concentration"] > CONCENTRATION_LIMIT_PCT
    assert any("BREACH" in a for a in r["alerts"])

def test_marcus_sleeves_aggregate_to_one_counterparty():
    # 3 broker sleeves + 1 custodian, all Barclays → ONE unique counterparty
    assert list(compute_exposures(MARCUS).keys()) == ["Barclays"]
    # 3 × 15% + 1 × 2% = 47% of assets
    assert compute_exposures(MARCUS)["Barclays"] == 950_000 * 0.47


# ── Helena Zhao: D-rated Lehman legacy position ──────────────────────────────

def test_helena_halts_on_rating_floor():
    r = assess_counterparties(HELENA)
    assert r["cleared"] is False
    lehman = r["counterparties"]["Lehman Legacy"]
    assert lehman["status"] == "HALT"
    assert lehman["rating"] == "D"
    assert any("sub-investment-grade" in a for a in r["alerts"])

def test_helena_issuer_exposure_is_full_notional():
    assert compute_exposures(HELENA)["Lehman Legacy"] == 350_000


# ── Methodology invariants ───────────────────────────────────────────────────

def test_cva_formula():
    r = assess_counterparties(SARAH)
    jpm = r["counterparties"]["JPMorgan Chase"]
    expected = round(2_500_000 * 0.15 * 0.0010 * 0.45, 2)  # Exp × PD × LGD
    assert jpm["cva"] == expected

def test_custodian_exposure_is_operational_only():
    # CASS 6 ring-fencing → custodian concentration must stay small
    r = assess_counterparties(SARAH)
    assert r["counterparties"]["DBS Bank"]["concentration"] <= 5.0

def test_unrated_counterparty_gets_conservative_pd():
    p = dict(SARAH, extra_counterparties={"Unknown Broker Ltd": 100_000})
    r = assess_counterparties(p)
    assert r["counterparties"]["Unknown Broker Ltd"]["pd_pct"] == 5.0

def test_zero_assets_no_division_error():
    p = dict(SARAH, investable_assets=0)
    r = assess_counterparties(p)  # must not raise
    assert isinstance(r["total_cva"], float)
