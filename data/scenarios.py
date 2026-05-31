SCENARIOS = {
    "oil_shock": {
        "name": "Oil Price Shock (+40%)",
        "description": "Middle East escalation drives Brent crude above $130/barrel",
        "impacts": {
            "global_equities": -0.12,
            "uk_gilts": -0.04,
            "us_treasuries": -0.02,
            "energy_equities": 0.25,
            "private_equity": -0.08,
            "infrastructure": 0.05,
            "gold": 0.18,
            "cash": 0.0
        }
    },
    "us_china_tariffs": {
        "name": "US-China Trade Escalation (60% tariffs)",
        "description": "Full trade decoupling - tech and manufacturing most exposed",
        "impacts": {
            "global_equities": -0.18,
            "uk_gilts": 0.03,
            "us_treasuries": 0.04,
            "energy_equities": -0.06,
            "private_equity": -0.15,
            "infrastructure": -0.02,
            "gold": 0.12,
            "cash": 0.0
        }
    },
    "uk_rate_spike": {
        "name": "UK Interest Rate Spike (+200bps)",
        "description": "Bank of England raises rates to 7% to combat inflation",
        "impacts": {
            "global_equities": -0.10,
            "uk_gilts": -0.14,
            "us_treasuries": -0.06,
            "energy_equities": -0.04,
            "private_equity": -0.12,
            "infrastructure": -0.08,
            "gold": -0.05,
            "cash": 0.02
        }
    }
}
