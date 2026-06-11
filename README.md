# WealthRisk AI Agent

**A multi-agent AI system for FCA-compliant wealth management — six specialised agents orchestrated with LangGraph, gating every portfolio recommendation behind AML, counterparty credit, and suitability checks before any capital is allocated.**

[![tests](https://github.com/MohitSharma888/wealthrisk-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/MohitSharma888/wealthrisk-agent/actions)
[![Live Demo](https://img.shields.io/badge/demo-Streamlit%20Cloud-FF4B4B)](https://wealthrisk-agent-ndkfxtkb5wlgvephg2p6gv.streamlit.app/)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)

**[▶ Live demo](https://wealthrisk-agent-ndkfxtkb5wlgvephg2p6gv.streamlit.app/)** — pick a demo client and run the full pipeline in ~30 seconds.

---

## Why this exists

In real wealth management, a portfolio recommendation is the *last* step of a regulated process, not the first. Most AI demos skip straight to "here's your allocation." This system models the actual control sequence a UK-regulated firm must run — and **halts the pipeline** the moment a client fails a gate, producing an auditable compliance report explaining exactly why.

Built by a delivery lead with 18 years in banking risk technology (DBS, Citi, UOB), as a working demonstration of agentic AI applied to regulated financial workflows.

## Pipeline architecture

```
                    ┌─────────────┐
 client profile ──▶ │  1. AML /   │  Neo4j graph: 2-hop sanctions
                    │  Sanctions  │  relationship detection
                    └──────┬──────┘
                     halt ─┤── pass
                    ┌──────▼──────┐
                    │ 2. Counter- │  Basel III PD mapping, CVA,
                    │ party risk  │  40% concentration limit,
                    └──────┬──────┘  CDS spread monitoring
                     halt ─┤── pass
                    ┌──────▼──────┐
                    │ 3. FCA      │  COBS 9A.2.6, 9A.2.7, 2.1.1
                    │ suitability │  deterministic rule engine
                    └──────┬──────┘
                     fail ─┤── pass
                    ┌──────▼──────┐
                    │ 4. Portfolio│  Claude API allocation
                    │ allocation  │  + ESG screening
                    └──────┬──────┘
                    ┌──────▼──────┐
                    │ 5. Stress   │  Oil shock · US-China tariffs
                    │ test        │  · UK rate spike
                    └──────┬──────┘
                    ┌──────▼──────┐
                    │ 6. Compliance│ Full audit trail +
                    │ report      │  halt-reason narrative
                    └─────────────┘
```

Routing is implemented as a **LangGraph `StateGraph` with conditional edges**: an AML flag or counterparty breach skips directly to the report agent, so a halted client never reaches portfolio construction.

## Counterparty credit methodology

| Check | Rule | Outcome |
|---|---|---|
| Rating floor | PD above BBB- threshold (2%) | HALT |
| Concentration | > 40% of investable assets to one counterparty | HALT |
| CDS spread | > 100bps | REVIEW (soft alert) |

- **CVA proxy:** `CVA = Exposure × PD × LGD(45%)` (Basel III supervisory LGD)
- **Exposure model:** broker sleeves carry settlement/margin exposure (15% of assets each, aggregated per unique counterparty); custodian exposure is operational-only (2%) reflecting **FCA CASS 6 client-asset ring-fencing**; product issuers carry full notional.

## Demo clients — one per failure mode

| Client | Scenario | Pipeline outcome |
|---|---|---|
| Sarah Mitchell | Clean profile | Full pass → portfolio + report |
| Viktor Petrov | Sanctions relationship in Neo4j graph | **HALT at AML** |
| Marcus Webb | All assets via Barclays (47% concentration) | **HALT at counterparty** |
| Helena Zhao | D-rated Lehman legacy note | **HALT at counterparty** |
| James Thornton | Conservative client, aggressive strategy | **FAIL at COBS 9A.2.7** |
| Priya Sharma | ESG-mandated next-gen HNW | Pass with ESG-screened allocation |
| David Chen | -5% drawdown tolerance | Pass, **stress test breach flagged** |

## Tech stack

`LangGraph` · `Claude API (Anthropic)` · `LangChain` · `Neo4j` · `Streamlit` · `Plotly` · `pytest`

## Run locally

```bash
git clone https://github.com/MohitSharma888/wealthrisk-agent.git
cd wealthrisk-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
streamlit run app.py
```

## Tests

The risk logic is deterministic and fully unit-tested — no API key needed:

```bash
pytest tests/ -v        # 15 tests: every demo scenario + methodology invariants
```

CI runs the suite on every push via GitHub Actions.

## Roadmap

- [ ] Live market data via `yfinance`; OFAC sanctions list; FCA Register API
- [ ] VaR / CVaR post-allocation analytics
- [ ] FastAPI service layer + Supabase persistence + Celery task queue
- [ ] Consumer Duty outcome-monitoring dashboard
- [ ] Human-in-the-loop approval gates with immutable audit log

## Disclaimer

Educational demonstration only. All counterparty data, ratings, and client profiles are fictional or illustrative. Not investment advice; not a regulated system.

---

*Built by [Mohit Sharma](https://www.linkedin.com/) — VP, IT Project Management · banking risk delivery · agentic AI.*
