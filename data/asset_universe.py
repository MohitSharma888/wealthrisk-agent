ASSET_UNIVERSE = {
    "global_equities": {
        "name": "Global Equities",
        "description": "Diversified global stock market exposure",
        "risk_level": 4,
        "esg_available": True,
        "typical_return": 0.08,
        "volatility": "high"
    },
    "uk_gilts": {
        "name": "UK Government Bonds (Gilts)",
        "description": "UK government fixed income securities",
        "risk_level": 1,
        "esg_available": False,
        "typical_return": 0.04,
        "volatility": "low"
    },
    "infrastructure": {
        "name": "Infrastructure",
        "description": "Roads, energy, utilities - inflation-linked income",
        "risk_level": 2,
        "esg_available": True,
        "typical_return": 0.06,
        "volatility": "low"
    },
    "private_equity": {
        "name": "Private Equity",
        "description": "Unlisted company ownership - illiquid but higher returns",
        "risk_level": 5,
        "esg_available": True,
        "typical_return": 0.12,
        "volatility": "high"
    },
    "gold": {
        "name": "Gold",
        "description": "Safe haven asset - performs well in crises",
        "risk_level": 2,
        "esg_available": False,
        "typical_return": 0.04,
        "volatility": "medium"
    },
    "cash": {
        "name": "Cash",
        "description": "Money market and short-term deposits",
        "risk_level": 1,
        "esg_available": False,
        "typical_return": 0.05,
        "volatility": "none"
    }
}
