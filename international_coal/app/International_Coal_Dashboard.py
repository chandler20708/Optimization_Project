import streamlit as st
import plotly.express as px
import gurobipy as gp
from gurobipy import GRB
import polars as pl
from models import run_model #, explain_model_results
from datetime import datetime

months = ["June", "July", "August", "September", "October"]
bands = ["WE_offpeak", "WE_peak", "WD_offpeak", "WD_peak"]
fuels = ["Stockpile", "Columbian","Russian", "Scottish", "Biomass"]
cv    = {"Stockpile":25.81, "Columbian":25.12, "Russian":24.50, "Scottish":26.20, "Biomass":18.00}
so2   = {"Stockpile":0.0138, "Columbian":0.0070, "Russian":0.0035, "Scottish":0.0172, "Biomass":0.0001}

if "fuels" not in st.session_state:
  st.session_state.fuels = fuels

if "cv" not in st.session_state:
  st.session_state.cv = cv

if "so2" not in st.session_state:
  st.session_state.so2 = so2

def dashboard():
  # st.session_state
  if "experiments" not in st.session_state:
    st.session_state.experiments = {"change_log":[], "sens_var": [], "sens_const": []}  # list of dicts

  ## init container ##
  experiment_section = st.container()
  llm_explain_section = st.container()
  kpi_section = st.container()
  # energy_section = st.container()
  fuel_strat_section = st.container()
  side_control = st.sidebar

  with side_control:
    st.title("International Coal Model Dashboard")
    # summary = st.toggle("Summary Sensitivity Analysis", value=False, key='summary')
    with st.expander("Optional Parameters Change"):
      edited_price = st.data_editor(
        gp.tupledict({
          ("June","WD_peak"):36.00, ("June","WD_offpeak"):27.00, ("June","WE_peak"):33.50, ("June","WE_offpeak"):26.20,
          ("July","WD_peak"):36.35, ("July","WD_offpeak"):27.00, ("July","WE_peak"):34.30, ("July","WE_offpeak"):26.30,
          ("August","WD_peak"):37.65, ("August","WD_offpeak"):28.20, ("August","WE_peak"):35.65, ("August","WE_offpeak"):27.50,
          ("September","WD_peak"):38.35, ("September","WD_offpeak"):28.50, ("September","WE_peak"):35.80, ("September","WE_offpeak"):27.65,
          ("October","WD_peak"):43.70, ("October","WD_offpeak"):31.70, ("October","WE_peak"):38.70, ("October","WE_offpeak"):30.10,
        }),
        column_config={'value':st.column_config.NumberColumn("Price per electricity sold (£/MWh)", min_value=0., max_value=200., step=0.01, format="%0.2f £/MWh")},
        key='edited_price'
      )
      edited_fuel_cost = st.data_editor(
        {
          "Stockpile":42.56,
          "Columbian":43.93,
          "Russian":43.80,
          "Scottish":42.00,
          "Biomass":73.77,
        },
        column_config={'value':st.column_config.NumberColumn("Cost of fuel (£/tonne)", min_value=0., max_value=200., step=0.01, format="%0.2f £/tonne")},
        key='edited_fuel_cost'
      )
      roc = st.number_input("ROC (£/MWh)", min_value=0., max_value=200., value=45., step=0.001, format="%0.3f", key='roc')

    decimals = st.slider("sensitivity to change", min_value=0.001, max_value=10., step=0.001)
    co2_price = st.slider("CO2 Price (€/tonne)", min_value=0., max_value=300., value=15., step=decimals, key='co2_price')
    so2_bubble_limit = st.slider("SO2 Bubble Limit (tonnes)", min_value=0, max_value=30_000, value=9_000, step=100, key='so2_bubble_limit')
    so2_price = st.slider("SO2 Price (£/tonne)", min_value=0, max_value=300, value=0, step=decimals, key='so2_price')
    biomass_limit=st.slider("Biomass Limit (%)", min_value=0., max_value=1., value=.1, step=.1, key='biomass_limit')
    if so2_price:
      st.warning("Setting a direct SO2 price will disable the SO2 bubble limit constraint.")
      so2_bubble_limit = float('inf')
    if st.toggle("Invest FGD System"):
      so2_reduced_eff = st.slider("SO2 Reduction Efficiency", min_value=0.0, max_value=1.0, value=0.0, step=0.01, key='so2_reduced_eff')
      fgd_cost = st.slider("FGD Cost (£)", min_value=0, max_value=110_000_000, value=10_000_000, step=1_000_000, format="%e", key='fgd_cost')
    else:
      so2_reduced_eff = 0.0
      fgd_cost = 0
    
  with st.spinner("Running optimization model..."):
    st.session_state.result = model, fuel_strat_df, results, biomass_share_df, sensitivity_var_lf, sensitivity_constr_lf, sensitivity_map_lf, sensitivity_map_buffer_lf = run_model( #, energy_mb
      roc=roc,
      fuel_cost=edited_fuel_cost,
      price=edited_price,
      co2_price=co2_price,
      so2_reduced_eff=so2_reduced_eff,
      so2_price=so2_price,
      so2_bubble_limit=so2_bubble_limit,
      fgd_cost=fgd_cost,
      biomass_limit=biomass_limit,
      # summary=summary,
    )
    change_log = {
      "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      "base_case": True if all((
        roc==45,
        edited_fuel_cost=={"Stockpile":42.56, "Columbian":43.93, "Russian":43.80, "Scottish":42.00, "Biomass":73.77},
        edited_price==gp.tupledict({
          ("June","WD_peak"):36.00, ("June","WD_offpeak"):27.00, ("June","WE_peak"):33.50, ("June","WE_offpeak"):26.20,
          ("July","WD_peak"):36.35, ("July","WD_offpeak"):27.00, ("July","WE_peak"):34.30, ("July","WE_offpeak"):26.30,
          ("August","WD_peak"):37.65, ("August","WD_offpeak"):28.20, ("August","WE_peak"):35.65, ("August","WE_offpeak"):27.50,
          ("September","WD_peak"):38.35, ("September","WD_offpeak"):28.50, ("September","WE_peak"):35.80, ("September","WE_offpeak"):27.65,
          ("October","WD_peak"):43.70, ("October","WD_offpeak"):31.70, ("October","WE_peak"):38.70, ("October","WE_offpeak"):30.10,
        }),
        co2_price==15,
        so2_reduced_eff==0,
        so2_price==0,
        so2_bubble_limit==9000,
        fgd_cost==0,
        biomass_limit==0.1,
      )) else False,
      "profit": results['total_profit'],
      **{key: results[key] for key in results if key in fuels},
      **dict(
        co2_price=co2_price,
        so2_reduced_eff=so2_reduced_eff,
        so2_price=so2_price,
        so2_bubble_limit=so2_bubble_limit,
        fgd_cost=fgd_cost,
        biomass_limit=biomass_limit,
        Stockpile_cost=edited_fuel_cost['Stockpile'],
        Columbian_cost=edited_fuel_cost['Columbian'],
        Russian_cost=edited_fuel_cost['Russian'],
        Scottish_cost=edited_fuel_cost['Scottish'],
        Biomass_cost=edited_fuel_cost['Biomass'],
        roc=roc,
        # **{f: sum(model.getVarByName(x[f,m,b]) for m in months for b in bands) for f in fuels},
      ),
      **{"_".join(key): value for key, value in edited_price.items()},
      # "summary": summary,
    }
    st.session_state.experiments['change_log'].append(change_log)
    st.session_state.experiments['sens_var'].append(
      sensitivity_var_lf
      .select(pl.lit(change_log['timestamp']).alias('timestamp'), pl.all(), base_case=pl.lit(change_log["base_case"]))
      .with_columns(
        BindingChange=pl.col("Binding") != pl.col("Binding").first().over("Variable"),
        RCChange=(pl.col('RC') - pl.col('RC').first().over("Variable")).abs() > pl.lit(1e-3)
      )
      .collect()
    )
    st.session_state.experiments['sens_const'].append(
      sensitivity_constr_lf
      .select(pl.lit(change_log['timestamp']).alias('timestamp'), pl.all(), base_case=pl.lit(change_log["base_case"]))
      .with_columns(
        BindingChange=pl.col("Binding") != pl.col("Binding").first().over("Constraint"),
        PiChange=(pl.col('Pi (Dual Value)') - pl.col('Pi (Dual Value)').first().over("Constraint")).abs() > pl.lit(1e-3)
      )
      .collect()
    )

  with experiment_section.expander("💡 Experiments Records"):
    st.dataframe(
      pl.DataFrame(st.session_state.experiments['change_log'])
      .unique(pl.col("*").exclude('timestamp', 'summary')) # type: ignore
      .sort('timestamp')
      # .with_columns()
    )
    ## sensitivity_var_df
    st.dataframe(
      pl.concat(st.session_state.experiments['sens_var'])
    )
    ## sensitivity_constr_df
    st.dataframe(
      pl.concat(st.session_state.experiments['sens_const'])
    )
  
#   with llm_explain_section.expander("💡 Model Explanation using Gemini-2.5"):
#     st.markdown("## Model Explanation using Gemini-2.5")
#     st.markdown("The following explanations are generated by Gemini-2.5 based on the optimization model results.")
#     response = explain_model_results(
#         df=fuel_strat_df.select(pl.all().exclude("month_index")), prompt=f"Based on data. Please conclude the fuel strategy as easy and short as possible in two bullets"
#     )
#     st.markdown(f"""## Fuel Strategy
# ###### {response.text}""", unsafe_allow_html=True)
    
#     var_col, constr_col = st.columns(2)
#     response = explain_model_results(
#         df=sensitivity_var_lf.collect(), prompt=f"Based on data. Please conclude Sensitivity Analysis on Variables as easy and short as possible on variables in three bullets"
#     )
#     var_col.markdown(f"""## Sensitivity Analysis on Variables
# ###### {response.text}""", unsafe_allow_html=True)

#     response = explain_model_results(
#         df=sensitivity_constr_lf.collect(), prompt=f"Based on data. Please conclude Sensitivity Analysis on Constraints as easy and short as possible on constraints in three bullets"
#     )
#     constr_col.markdown(f"""## Sensitivity Analysis on Constraints
# ###### {response.text}""", unsafe_allow_html=True)

  with kpi_section:

    p_col, eq_col, r_col, plus_col, c_col = st.columns([1,0.3,1,0.3,1])
    with p_col:
      st.metric("Total Profit (£)", f"{results['total_profit']:,.2f}", )
    with eq_col:
      st.markdown("## =")
    with r_col:
      st.metric("Revenue (£)", f"{results['total_profit'] + results['total_fuel_cost'] + results['total_co2_cost'] + results['total_so2_cost'] + results['fgd_cost']:,.2f}")
      st.metric("ROC Income (£)", f"{results['roc_incentive']:,.2f}")
    with plus_col:
      st.markdown("## -")
    with c_col:
      st.metric("Total Cost (£)", f"{results['total_fuel_cost'] + results['total_co2_cost'] + results['total_so2_cost'] + results['fgd_cost']:,.2f}")
  
  env_impact_section, op_eff_section = kpi_section.columns(2)

  with env_impact_section:
    col1, col2 = st.columns(2)
    col1.metric("CO2 Emissions (tons)", f"{results['co2_emissions']:,.2f}")
    
    bio_bar = (
      px.bar(biomass_share_df, x=["Biomass_MWh", "Other_MWh"], orientation='h', labels="", height=220)
      .add_annotation(y=0,text=f"{biomass_share_df['Biomass Share (%)'][0,0][0]:.0%}", arrowsize=0.5, font={'size': 40})
      .update_layout(yaxis_title=None, xaxis_title=None, showlegend=False, title="Biomass Share", yaxis={'showticklabels': False})
    )
    col1.plotly_chart(bio_bar)
    col2.metric("SO2 Emissions (tons)", f"{results['so2_emissions']:,.2f}")
    col2.metric("SO2 Bubble Used %", f"{results['so2_emissions'] / so2_bubble_limit:,.2%}")
    
  with op_eff_section:
    st.metric("Total Generation (MWh)", f"{results['total_generation']:,}")
    # st.dataframe(fuel_strat_df)
    # st.text(fuel_strat_df['Stockpile'].sum() / 600_000)
    stockpile_bar = (
      px.bar(pl.DataFrame({'Stockpile': fuel_strat_df['Stockpile'].sum(), 'Slack': 600_000 - fuel_strat_df['Stockpile'].sum()}),
             x=["Stockpile", "Slack"], orientation='h', labels="", height=220)
      .add_annotation(y=0,text=f"{fuel_strat_df['Stockpile'].sum() / 600_000:.0%}", arrowsize=0.5, font={'size': 40})
      .update_layout(yaxis_title=None, xaxis_title=None, showlegend=False, title="Stockpile Usage", yaxis={'showticklabels': False})
    )
    st.plotly_chart(stockpile_bar)

  with fuel_strat_section:
    st.markdown("## Fuel Strategy (tons)")
    bar_chart = px.bar(
      fuel_strat_df, x="Period", y=fuels, facet_col="Month"
    )
    st.plotly_chart(bar_chart)

    st.markdown("### Sensitivity Analysis")
    var_col, constr_col = st.columns([2,1.5])
    with var_col:
      with st.expander("Variable Sensitivity Full Table"):
        st.dataframe(sensitivity_var_lf.collect(), height=600)
      st.dataframe(
        sensitivity_var_lf
        .with_columns(
          Fuel=pl.col("Variable").str.extract("x\[([a-zA-Z]+),([^,]+),([^\]]+)\]",1),
          Months=pl.col("Variable").str.extract("x\[([a-zA-Z]+),([^,]+),([^\]]+)\]",2),
          Bands=pl.col("Variable").str.extract("x\[([a-zA-Z]+),([^,]+),([^\]]+)\]",3),
        )
        .group_by("Fuel")
        .agg(
          pl.sum("Final Value").alias("total_tons"),
          pl.mean("RC").alias("avg_RC"),
          pl.len().alias("n_vars")
        )
        .sort("total_tons", descending=True)
        .collect()
      )
      st.text("""
  ✅ Final Value>0 & RC≈0 → model is using it.
  ⚙️ Final Value=0 & RC<0 → model wants it (blocked by constraint).
  🚫 Final Value=0 & RC>0 → model avoids it (too costly or limited value).""")
      

    with constr_col:
      with st.expander("Constraint Sensitivity Full Table"):
        st.dataframe(sensitivity_constr_lf.collect(), height=600)
      st.dataframe(
        sensitivity_constr_lf
        .with_columns(
          pl.col("Constraint").str.replace(r"\[.*\]", "").alias("constraint_group")
        )
        .group_by("constraint_group")
        .agg(
          pl.mean("Pi (Dual Value)").alias("avg_pi"),
          pl.max("Pi (Dual Value)").alias("max_pi"),
          pl.len().alias("count"),
          ((pl.col("constraint_status")==pl.lit("binding_resource")).cast(pl.Int32)).sum().alias("n_binding"),
          pl.mean("Slack").alias("avg_slack"),
          pl.col("Constraint").filter(pl.col("Pi (Dual Value)")>0).alias("active_members")
        )
        .sort("avg_pi", descending=True)
        .collect()
      )
      st.text("""
  🟥 Binding → π ≠ 0 and slack = 0 → drives the strategy.
  🟩 Non-binding → π = 0 and slack > 0 → safe to tighten without affecting profit.""")
    
    map_col, buffer_col = st.columns([2,1.5])
    with map_col:
      st.dataframe(sensitivity_map_lf.collect())
      st.text("""
    •	total_margin_profit_gain: Approximate total profit increase if that constraint were relaxed.
    •	Large total_gain + high π = this constraint dominates the strategy.
    •	Small π = mild or local effect.
    •	Negative total_gain = relaxing that constraint actually hurts another fuel’s profit (substitution effect).""")
    
    with buffer_col:
      st.dataframe(sensitivity_map_buffer_lf.collect())
    

if __name__ == "__main__":
  st.set_page_config(layout="wide")
  dashboard()
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