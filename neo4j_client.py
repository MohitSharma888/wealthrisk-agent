from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def check_aml_clearance(state: dict) -> dict:
    client = state["client_profile"]
    
    # For demo purposes - simulate AML check
    # In production this connects to real Neo4j
    flagged_names = ["Viktor Petrov"]
    
    if client["name"] in flagged_names:
        result = {
            "cleared": False,
            "flag": "CLIENT FLAGGED - 2 hops from OFAC sanctioned entity via Meridian Holdings Ltd -> Albatross Capital",
            "action": "Refer to Compliance Officer immediately"
        }
    else:
        result = {
            "cleared": True,
            "flag": None,
            "action": "AML check passed - proceed to suitability assessment"
        }
    
    state["aml_result"] = result
    state["audit_trail"].append({
        "agent": "aml_check",
        "result": "CLEARED" if result["cleared"] else "FLAGGED",
        "detail": result["action"]
    })
    return state
