# import streamlit as st
# import plotly.express as px
# import gurobipy as gp
# from gurobipy import GRB
# import polars as pl
# from datetime import datetime
# from models import run_model

# # TODO: Profit Decomposition Header
# # •	Green for positive effects, red for negative.
# #	•	Show both £ and % change.
# # TODO: Variables & Parameters Change
# # Extract changed parameter values vs base (electricity_price, fuel_price, co2_price, so2_cap, etc.).
# # TODO: Strategy Differences
# 	# •	Prepare a combined dataframe:
# 	# •	Columns: fuel, month, band, x_base, x_exp, Δtons
# 	# •	Add FGD_flag if included.
# 	# •	Create two bar charts (Base vs Experiment) by fuel × month/band using Plotly or Altair.
# 	# •	Example: horizontal grouped bar.
# 	# •	Tooltip: tons and Δ%.
# 	# •	Label each chart with FGD Yes/No depending on decision variable value.
# # TODO: Impactful Constraints Change (Workflow 1 & 2)
# # TODO: Managerial Narrative Block (LLM)

# # st.session_state['experiments']
# months = ["June", "July", "August", "September", "October"]
# bands  = ["WE_offpeak", "WE_peak", "WD_offpeak", "WD_peak"]
# fuels  = st.session_state['fuels']
# cv     = st.session_state['cv']
# so2    = st.session_state['so2']

# efficiency   = 0.35
# exchange_rate = 0.86
# # st.session_state



# def dashboard():
  
#   side_control = st.sidebar
#   kpi_section = st.container()

#   change_log = (
#     pl.DataFrame(st.session_state['experiments']['change_log'])
#     .unique(pl.all().exclude('timestamp')) # type: ignore
#   )
#   st.dataframe(change_log)

#   with side_control:
#     experiment_timestamp = st.selectbox("Choose your experiment", change_log['timestamp'].unique())
#     base_line = change_log.filter(pl.col('base_case')).unique('timestamp')
#     change_log = change_log.filter(pl.col('timestamp').eq(experiment_timestamp)).unique('timestamp')

#   with kpi_section:
#     p_col, eq_col, r_col, plus_col, c_col = st.columns([1,0.3,1,0.3,1])
#     with p_col:
#       st.metric("Total Profit (£)", f"{change_log['profit'][0]:,.2f}", )
#     with eq_col:
#       st.markdown("## =")
#     with r_col:
#       st.metric("Revenue (£)", f"{change_log['profit'] + change_log['fuel_cost'] + change_log['co2_cost'] + change_log['so2_cost'] + change_log['fgd_cost']:,.2f}")
#       st.metric("ROC Income (£)", f"{change_log['roc_incentive']:,.2f}")
#     with plus_col:
#       st.markdown("## -")
#     with c_col:
#       st.metric("Total Cost (£)", f"{change_log['total_fuel_cost'] + change_log['total_co2_cost'] + change_log['total_so2_cost'] + results['fgd_cost']:,.2f}")

# if __name__ == "__main__":
#   st.markdown(
#       """
#   <style>
#   [data-testid="stMetricValue"] {
#       font-size: 20px;
#   }
#   </style>
#   """,
#       unsafe_allow_html=True,
#   )
#   st.set_page_config(layout="wide")
#   dashboard()