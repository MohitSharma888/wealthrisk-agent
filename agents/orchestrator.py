from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from agents.suitability import run_suitability_check
from agents.portfolio import run_portfolio_allocation
from agents.stress_test import run_stress_test
from agents.report import generate_report
from neo4j_client import check_aml_clearance

class WealthRiskState(TypedDict):
    client_profile: dict
    aml_result: Optional[dict]
    suitability_result: Optional[dict]
    portfolio_allocation: Optional[dict]
    stress_test_result: Optional[dict]
    final_report: Optional[str]
    audit_trail: list
    error: Optional[str]

def build_graph():
    g = StateGraph(WealthRiskState)
    g.add_node("aml_check", check_aml_clearance)
    g.add_node("suitability", run_suitability_check)
    g.add_node("portfolio", run_portfolio_allocation)
    g.add_node("stress_test", run_stress_test)
    g.add_node("report", generate_report)
    g.set_entry_point("aml_check")
    g.add_edge("aml_check", "suitability")
    g.add_edge("suitability", "portfolio")
    g.add_edge("portfolio", "stress_test")
    g.add_edge("stress_test", "report")
    g.add_edge("report", END)
    return g.compile()

graph = build_graph()
