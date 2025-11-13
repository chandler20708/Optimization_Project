import streamlit as st
import plotly.express as px
import gurobipy as gp
from gurobipy import GRB
import polars as pl


def summary() -> None:
  st.set_page_config(page_title="International Coal • Case Summary", layout="wide")
  st.title("International Coal: Case Overview")
  st.markdown("### Fuel-mix optimisation for a 1,000 MW UK coal plant across the June–October planning window.")

  kpi_col1, kpi_col2, kpi_col3 = st.columns([1,2,1])
  kpi_col1.metric("Plant Capacity", "1,000 MW")
  kpi_col2.metric("Planning Horizon", "5 months · 20 periods")
  kpi_col3.metric("Objective", "Maximise net profit")

  st.markdown("### Mission")
  st.write(
    "Operate the 1,000 MW unit profitably (June–October) while respecting every environmental and operational guardrail."
  )

  st.markdown("### Case Snapshot Table")
  snapshot_rows = [
    {
      "Area": "Decisions",
      "Highlights": "Fuel blend (stockpile/imported/biomass), burn per period (20 bands), and optional FGD build for more SO₂ headroom.",
    },
    {
      "Area": "Why Difficult",
      "Highlights": "SO₂/CO₂ compliance pressure, multi-band operational complexity, and constant profit vs. cleanliness trade-offs.",
    },
    {
      "Area": "Uncertainty",
      "Highlights": "Future SO₂ policy, carbon-price shocks, electricity-price volatility, and fuel/logistics swings.",
    },
  ]
  st.table(pl.DataFrame(snapshot_rows).to_pandas())
  st.info("Use the table for a quick read; expand the maths below when you need the full formulation.")

  st.markdown("### Mathematical Model")
  st.write("Key pieces of the optimisation model, now at your fingertips.")
  with st.expander("Show equations", expanded=True):
    st.latex(
      r"""
      \max Z = \sum_{m,b} \Big[(p_{m,b} - 0.65)E_{m,b} + 45E_{m,b}^{\text{bio}} - \sum_f P_f x_{f,m,b} - 15 \times 0.86 \times 0.8 \, E_{m,b}\Big]
      """
    )
  with st.expander("Variable glossary", expanded=False):
    st.markdown(
      """
      - $x_{f,m,b}$ — tonnes of fuel $f$ burned in month $m$, band $b$.
      - $E_{m,b}$ — electricity output (MWh) in month $m$, band $b$; $E_{m,b}^{\\text{bio}}$ is the biomass portion.
      - $p_{m,b}$ — electricity price (£/MWh) in month $m$, band $b$.
      - $P_f$ — cost (£/tonne) of fuel $f$.
      - $CV_f$ — calorific value (GJ/tonne) of fuel $f$; $\\eta$ — plant efficiency (35%).
      - $SO2_f$ — tonnes of SO₂ emitted per tonne of fuel $f$; $S_{m,b}$ — resulting SO₂ emission in period $(m,b)$.
      - $H_{m,b}$ — available operating hours in month $m$, band $b$.
      """
    )

  st.markdown("### Constraints (Mathematical View)")
  constraints_md = r"""
| Constraint | Expression |
| --- | --- |
| Stockpile limit | $\sum_m \sum_b x_{\text{Stockpile},m,b} \le 600{,}000$ |
| Energy generated | $E_{m,b} = \frac{\eta}{3.6} \sum_f \big(CV_f \, x_{f,m,b}\big)$ |
| Biomass share | $E_{m,b}^{\text{bio}} \le 0.1 \, E_{m,b}$ |
| Sulphur accounting | $S_{m,b} = \sum_f \left(x_{f,m,b} \, SO2_f\right)$ |
| SO₂ bubble | $\sum_m \sum_b S_{m,b} \le 0.3 \times 30{,}000$ |
| Capacity ceiling | $E_{m,b} \le 1000 \times H_{m,b}$ |
| Import availability | $x_{\text{Colombian},m,b} = x_{\text{Russian},m,b} = x_{\text{Scottish},m,b} = 0 \quad \text{(summer)}$ |
"""
  st.markdown(constraints_md)

  st.markdown("### Supporting Notes")
  st.write(
    "Scenarios stress-test the plan against SO₂ rules, CO₂ prices, market volatility, and fuel logistics so the recommendations stay robust."
  )

  st.markdown("### How This App Helps")
  st.markdown(
    """
    - Surfaces the optimal fuel mix under base conditions.
    - Tests policy shocks (CO₂ / SO₂ price moves, renewable incentives).
    - Shows the value of FGD investment and other flexibility levers.
    - Compares profit outcomes under electricity-price volatility and alternative fuel-price decks.
    - Provides explainable recommendations backed by optimisation logic.
    """
  )


if __name__ == "__main__":
  summary()
  st.markdown("---")
  st.markdown(
      """
      <div style='text-align: center; font-size: 0.9em; color: gray;'>
          © 2025 <b>Chia-Te Liu</b>. All rights reserved.  
          Made with ❤️ using Streamlit.  
          <a href='https://www.linkedin.com/in/chia-te-liu/' target='_blank'>LinkedIn</a>
      </div>
      """,
      unsafe_allow_html=True
  )
