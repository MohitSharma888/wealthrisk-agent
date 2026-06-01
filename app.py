import streamlit as st
import os

# Load API key FIRST before any agent imports
try:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()

import json
import plotly.express as px
import pandas as pd
from agents.orchestrator import graph
from data.scenarios import SCENARIOS

st.set_page_config(page_title="WealthRisk AI Agent", page_icon="💼", layout="wide")

st.title("💼 WealthRisk AI Agent")
st.markdown("*Multi-agent AI system for FCA-compliant wealth management · Built by Mohit Sharma*")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Client Profile")
    name = st.selectbox("Select Demo Client", [
    "Sarah Mitchell (Clean Pass)",
    "James Thornton (Compliance Fail)",
    "Viktor Petrov (AML Flag)",
    "Priya Sharma (ESG Focus)",
    "David Chen (Stress Test Breach)"
    ])

    if "Sarah" in name:
        default_age, default_income, default_assets = 52, 180000, 2500000
        default_risk, default_strategy, default_horizon = "balanced", "balanced", 15
        default_esg, default_drawdown = True, -15
    elif "James" in name:
        default_age, default_income, default_assets = 68, 45000, 380000
        default_risk, default_strategy, default_horizon = "conservative", "aggressive", 5
        default_esg, default_drawdown = False, -10
    elif "Priya" in name:
        default_age, default_income, default_assets = 38, 120000, 800000
        default_risk, default_strategy, default_horizon = "growth", "growth", 20
        default_esg, default_drawdown = True, -12

    elif "David" in name:
        default_age, default_income, default_assets = 61, 95000, 450000
        default_risk, default_strategy, default_horizon = "conservative", "conservative", 8
        default_esg, default_drawdown = False, -5
    else:
        default_age, default_income, default_assets = 45, 220000, 5000000
        default_risk, default_strategy, default_horizon = "growth", "growth", 10
        default_esg, default_drawdown = False, -20

    client_name = name.split(" (")[0]
    age = st.slider("Age", 30, 80, default_age)
    annual_income = st.number_input("Annual Income (£)", value=default_income, step=10000)
    investable_assets = st.number_input("Investable Assets (£)", value=default_assets, step=100000)

with col2:
    st.subheader("⚙️ Strategy & Scenario")
    risk_options = ["conservative", "moderate", "balanced", "growth", "aggressive"]
    risk_tolerance = st.selectbox("Risk Tolerance", risk_options, index=risk_options.index(default_risk))
    proposed_strategy = st.selectbox("Proposed Strategy", risk_options, index=risk_options.index(default_strategy))
    investment_horizon = st.slider("Investment Horizon (years)", 1, 30, default_horizon)
    esg_required = st.checkbox("ESG Screening Required", value=default_esg)
    max_drawdown = st.slider("Max Drawdown Tolerance (%)", -30, -5, default_drawdown)
    scenario_key = st.selectbox(
        "Geopolitical Stress Scenario",
        list(SCENARIOS.keys()),
        format_func=lambda k: SCENARIOS[k]["name"]
    )

st.markdown("---")

if st.button("⚡ Run WealthRisk Analysis", type="primary", use_container_width=True):
    client_profile = {
        "name": client_name,
        "age": age,
        "annual_income": annual_income,
        "investable_assets": investable_assets,
        "risk_tolerance": risk_tolerance,
        "proposed_strategy": proposed_strategy,
        "investment_horizon": investment_horizon,
        "esg_required": esg_required,
        "max_drawdown_tolerance": max_drawdown,
        "scenario": scenario_key
    }

    initial_state = {
        "client_profile": client_profile,
        "aml_result": None,
        "suitability_result": None,
        "portfolio_allocation": None,
        "stress_test_result": None,
        "final_report": None,
        "audit_trail": [],
        "error": None
    }

    with st.spinner("Running 5-agent analysis pipeline... (~20 seconds)"):
        result = graph.invoke(initial_state)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔍 AML Check", "✅ Suitability", "📊 Portfolio", "🌍 Stress Test", "📄 Report", "🔗 Audit Trail"
    ])

    with tab1:
        st.subheader("AML & Sanctions Check")
        aml = result["aml_result"]
        if aml["cleared"]:
            st.success("✅ AML CHECK PASSED")
            st.info(aml["action"])
        else:
            st.error("🚨 AML FLAG RAISED")
            st.warning(aml["flag"])
            st.error(aml["action"])

    with tab2:
        st.subheader("FCA Suitability Assessment")
        suit = result["suitability_result"]
        if suit["verdict"] == "SUITABLE":
            st.success(f"✅ VERDICT: {suit['verdict']}")
        else:
            st.error(f"❌ VERDICT: {suit['verdict']}")

        st.markdown("**FCA Rules Checked:**")
        for check in suit["checks"]:
            icon = "✅" if check["pass"] else "❌"
            status = "PASS" if check["pass"] else "FAIL"
            st.markdown(f"{icon} **{check['rule']}** — {check['description']} · *{check['detail']}* · **{status}**")

        st.markdown("**Suitability Explanation:**")
        st.write(suit["explanation"])

    with tab3:
        st.subheader("Portfolio Allocation")
        port = result["portfolio_allocation"]
        if port.get("status") == "SKIPPED":
            st.warning("⚠️ Portfolio not generated — suitability check failed")
        else:
            allocs = port["allocations"]
            df = pd.DataFrame({
                "Asset Class": [k.replace("_", " ").title() for k in allocs.keys()],
                "Allocation %": list(allocs.values())
            })
            fig = px.pie(df, values="Allocation %", names="Asset Class",
                        title="Portfolio Allocation",
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f"**Rationale:** {port['rationale']}")
            if port["esg_applied"]:
                st.info("🌿 ESG screening applied — fossil fuels excluded")

    with tab4:
        st.subheader("Geopolitical Stress Test")
        stress = result["stress_test_result"]
        if stress.get("status") == "SKIPPED":
            st.warning("⚠️ Stress test skipped — no portfolio to test")
        else:
            st.markdown(f"**Scenario:** {stress['scenario']}")
            st.markdown(f"**Description:** {stress['scenario_description']}")

            if stress["breach"]:
                st.error(f"🚨 BREACH: {stress['breach_message']}")
            else:
                st.success(f"✅ WITHIN TOLERANCE: Portfolio impact {stress['total_portfolio_impact_pct']}% (tolerance: {stress['max_drawdown_tolerance_pct']}%)")

            impacts = stress["asset_impacts"]
            df2 = pd.DataFrame([{
                "Asset": k.replace("_", " ").title(),
                "Allocation %": v["allocation_pct"],
                "Scenario Impact %": v["scenario_impact_pct"],
                "Weighted Impact %": v["weighted_impact_pct"]
            } for k, v in impacts.items()])

            fig2 = px.bar(df2, x="Asset", y="Scenario Impact %",
                         title=f"Asset Impact — {stress['scenario']}",
                         color="Scenario Impact %",
                         color_continuous_scale=["red", "yellow", "green"])
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(df2, use_container_width=True)

    with tab5:
        st.subheader("Compliance Report")
        st.markdown(result["final_report"])
        st.download_button(
            label="📥 Download Report",
            data=result["final_report"],
            file_name=f"wealthrisk_report_{client_name.replace(' ', '_')}.txt",
            mime="text/plain"
        )

    with tab6:
        st.subheader("Audit Trail")
        st.markdown("*Every agent decision logged with timestamp for regulatory review*")
        for i, entry in enumerate(result["audit_trail"], 1):
            st.markdown(f"**Step {i} — {entry['agent'].upper()}**")
            st.json(entry)
            st.markdown("---")
