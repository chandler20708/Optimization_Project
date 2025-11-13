import gurobipy as gp
from gurobipy import GRB
import polars as pl
import streamlit as st

def run_model(
  roc=45.,
  fuel_cost={"Stockpile":42.56, "Columbian":43.93, "Russian":43.80, "Scottish":42.00, "Biomass":73.77},
  price=gp.tupledict({
    ("June","WD_peak"):36.00, ("June","WD_offpeak"):27.00, ("June","WE_peak"):33.50, ("June","WE_offpeak"):26.20,
    ("July","WD_peak"):36.35, ("July","WD_offpeak"):27.00, ("July","WE_peak"):34.30, ("July","WE_offpeak"):26.30,
    ("August","WD_peak"):37.65, ("August","WD_offpeak"):28.20, ("August","WE_peak"):35.65, ("August","WE_offpeak"):27.50,
    ("September","WD_peak"):38.35, ("September","WD_offpeak"):28.50, ("September","WE_peak"):35.80, ("September","WE_offpeak"):27.65,
    ("October","WD_peak"):43.70, ("October","WD_offpeak"):31.70, ("October","WE_peak"):38.70, ("October","WE_offpeak"):30.10,
  }),
  co2_price=15.0,          # £/ton CO2
  so2_reduced_eff=0.0,            # e.g., 0.0 (no FGD), 0.7, 0.8, 0.9
  fgd_cost=0.0,           # £/year fixed cost added once to objective
  so2_bubble_limit=0.3*30_000,
  so2_price=0.0,        # £/t SO2; None means no direct SO2 cost
  exchange_rate=0.87,
  biomass_limit=0.1,
  summary=False,
):
  if so2_price:
    so2_bubble_limit = float('inf')
  if not fgd_cost or not so2_reduced_eff:
    so2_reduced_eff = 0.0
    fgd_cost = 0.0

  # Data
  fuels = {'Stockpile', 'Columbian', 'Russian', 'Scottish', 'Biomass'}
  mixes_3 = {'Columbian', 'Russian', 'Scottish'}
  assert mixes_3.issubset(fuels)

  months = {'June', 'July', 'August', 'September', 'October'}
  jun_aug = {'June', 'July', 'August'}
  assert jun_aug.issubset(months)

  bands = {'WD_peak', 'WD_offpeak', 'WE_peak', 'WE_offpeak'}

  fuels, cv, so2 = gp.multidict({
    "Stockpile": [25.81, 0.0138],
    "Columbian": [25.12, 0.0070],
    "Russian"  : [24.50, 0.0035],
    "Scottish" : [26.20, 0.0172],
    "Biomass": [18.00, 0.0001],
  })

  Hours = gp.tupledict({
    ('June', 'WD_peak'): 264,
    ('June', 'WD_offpeak'): 264,
    ('June', 'WE_peak'): 96,
    ('June', 'WE_offpeak'): 96,

    ('July', 'WD_peak'): 264,
    ('July', 'WD_offpeak'): 264,
    ('July', 'WE_peak'): 108,
    ('July', 'WE_offpeak'): 108,

    ('August', 'WD_peak'): 264,
    ('August', 'WD_offpeak'): 264,
    ('August', 'WE_peak'): 108,
    ('August', 'WE_offpeak'): 108,

    ('September', 'WD_peak'): 264,
    ('September', 'WD_offpeak'): 264,
    ('September', 'WE_peak'): 96,
    ('September', 'WE_offpeak'): 96,

    ('October', 'WD_peak'): 252,
    ('October', 'WD_offpeak'): 252,
    ('October', 'WE_peak'): 120,
    ('October', 'WE_offpeak'): 120,
  })

  Cap_MW = 1000

  model = gp.Model('purchase')

  # Variables
  x = model.addVars(fuels, months, bands, lb=0, name='x')
  # fgd = model.addVar(vtype=GRB.BINARY, name='invest_fgd')

  energy_fmb = {
    (f, m, b): (0.35 / 3.6) * cv[f] * x[f, m, b]
    for f in fuels for m in months for b in bands
  }

  energy_mb = {
    (m, b): gp.quicksum(energy_fmb[f, m, b] for f in fuels)
    for m in months for b in bands
  }

  so2_reduced = {
    (m, b): (1 - so2_reduced_eff) * gp.quicksum(so2[f] * x[f,m,b] for f in fuels)
    for m in months for b in bands
  }

  # Constraints
  # Stockpile
  model.addConstr(
    gp.quicksum(x['Stockpile', m, b] for m in months for b in bands) <= 600_000,
    name='Stockpile_Inventory'
  )

  # Biomass
  model.addConstrs(
    (energy_fmb['Biomass', m, b] <= biomass_limit * energy_mb[m, b]
      for m in months for b in bands),
    name="Biomass_Limit"
  )

  # Sulphur Bubble
  model.addConstr(
    gp.quicksum(so2_reduced[m,b] for m in months for b in bands) <= so2_bubble_limit,
    name='Sulphur_Bubble_Limit'
  )

  # Capacity Limit
  model.addConstrs(
    (energy_mb[m, b] <= Cap_MW * Hours[m,b] for m in months for b in bands),
    name="CapacityLimit"
  )

  # No Coal Summer
  model.addConstrs(
    (x[f, m, b] == 0
    for f in mixes_3
    for m in jun_aug
    for b in bands),
    name="No_Coal_Summer"
  )

  # Objectives
  model.setObjective(
    gp.quicksum(
      (price[m,b] - 0.65) * energy_mb[m,b] + roc * energy_fmb['Biomass', m, b]
      - gp.quicksum(fuel_cost[f] * x[f,m,b] for f in fuels)
      - co2_price * exchange_rate * 0.8 * energy_mb[m,b]
      - so2_reduced[m,b]*so2_price
      for m in months for b in bands
    )
    - fgd_cost,
    GRB.MAXIMIZE
  )

  model.optimize()
  model.update()

  # 𝑃𝑟𝑜𝑓𝑖𝑡 = 𝑅𝑒𝑣𝑒𝑛𝑢𝑒 − (𝑇𝑟𝑎𝑛𝑠𝑚𝑖𝑠𝑠𝑖𝑜𝑛 𝐶𝑜𝑠𝑡 + 𝐶𝑂2 𝐶𝑜𝑠𝑡 + 𝐹𝑢𝑒𝑙 𝐶𝑜𝑠𝑡) + 𝑅𝑂𝐶 𝐼𝑛𝑐𝑒𝑛𝑡𝑖𝑣𝑒
  rev_minus_tx = gp.quicksum((price[m,b] - 0.65) * energy_mb[m,b] for m in months for b in bands).getValue()
  co2_cost = gp.quicksum(co2_price * exchange_rate * 0.8 * energy_mb[m,b] for m in months for b in bands).getValue()
  total_fuel_cost = gp.quicksum(fuel_cost[f] * model.getVarByName(f"x[{f},{m},{b}]").X for f in fuels for m in months for b in bands).getValue()
  roc_incentive = 45 * gp.quicksum(energy_fmb['Biomass', m, b] for m in months for b in bands).getValue()
  so2_tonnes = gp.quicksum(so2_reduced[m,b] for m in months for b in bands).getValue()


  # transfer the for loop results into a polars DataFrame:
  # Month Period Stockpile Russian Scottish Biomass Total (tons)
  # sort by Month and Period

  cv_map = {f: cv[f] for f in fuels}
  results = []
  for f in fuels:
    for m in months:
      for b in bands:
        results.append({
          "Fuel": f,
          "Month": m,
          "Band": b,
          "Tons": x[f,m,b].X
        })
  df = (
    pl.DataFrame(results)
    .with_columns(pl.col("Fuel").replace(cv_map).cast(pl.Float32).alias('CV_GJ_per_t'))
    .with_columns(
      Energy_MWh=pl.col("Tons") * pl.col("CV_GJ_per_t")
    )
  )
  # Biomass energy per month
  biomass = (
    df
    .filter(pl.col("Fuel") == "Biomass")
    .group_by("Month")
    .agg(pl.col("Energy_MWh").sum().alias("Biomass_MWh"))
  )
  # Aggregate total energy per month
  biomass_share_df = (
      df.group_by("Month")
      .agg(pl.col("Energy_MWh").sum().alias("Total_MWh"))
      .join(biomass, on="Month", how="left")
      .fill_null(0)
      .sort("Month")
      .select(pl.all().exclude('Month'))
      .sum()
      .with_columns(
          (pl.col("Biomass_MWh") / pl.col("Total_MWh")).round(3).alias("Biomass Share (%)"),
          Other_MWh=pl.col("Total_MWh") - pl.col("Biomass_MWh")
      )
  )

  fuel_strat_df = (
    pl.DataFrame({
      "Month": [m for m in months for b in bands],
      "Period": [b for m in months for b in bands],
      **{f: [x[f,m,b].X for m in months for b in bands] for f in fuels},
      "Total (tons)": [sum(x[f,m,b].X for f in fuels) for m in months for b in bands],
    })
    .with_columns(
      month_index = pl.when(pl.col("Month") == "June").then(6)
      .when(pl.col("Month") == "July").then(7)
      .when(pl.col("Month") == "August").then(8)
      .when(pl.col("Month") == "September").then(9)
      .when(pl.col("Month") == "October").then(10)
    )
    .sort(["month_index", "Period"])
  )

  sensitivity_var = {
    "Variable": [],
    "Final Value": [],
    "Obj": [],
    "RC": [],
    "Allowable Increase": [],
    "Allowable Decrease": [],
    "Binding": [],
    # "SAObjUp": [],
    # "SAObjLow": [],
  }

  sensitivity_constr = {
    "Constraint": [],
    "Slack": [],
    "Final Value": [],
    # "SARHSUp": [],
    # "SARHSLow": [],
    "Pi (Dual Value)": [],
    "Binding": [],
  }

  sensitivity_map = {
    "Constraint": [],
    "Variable": [],
    "Coeff": [],
  }

  for v in model.getVars():
    sensitivity_var["Variable"].append(v.VarName)
    sensitivity_var["Final Value"].append(v.X)
    sensitivity_var["Obj"].append(v.Obj)
    sensitivity_var["RC"].append(v.RC)

    sensitivity_var["Allowable Increase"].append(v.SAObjUp - v.Obj)
    sensitivity_var["Allowable Decrease"].append(v.Obj - v.SAObjLow)
    sensitivity_var["Binding"].append(abs(v.RC) < 1e-6)

  for c in model.getConstrs():
    sensitivity_constr["Constraint"].append(c.ConstrName)
    sensitivity_constr['Slack'].append(c.Slack)
    sensitivity_constr['Final Value'].append(c.RHS - c.Slack)
    # sensitivity_constr["SARHSUp"].append(c.SARHSUp)
    # sensitivity_constr["SARHSLow"].append(c.SARHSLow)
    sensitivity_constr["Pi (Dual Value)"].append(c.Pi)
    sensitivity_constr["Binding"].append(abs(c.Slack) < 1e-6)
    
    row = model.getRow(c)
    for i in range(row.size()):
      sensitivity_map['Constraint'].append(c.ConstrName)
      sensitivity_map['Variable'].append(row.getVar(i).VarName)
      sensitivity_map['Coeff'].append(row.getCoeff(i))

  
  tol = 1e-6
  x_tol   = 1e-6
  rc_tol  = 1e-6
  pi_tol  = 1e-8
  slack_min_step = 0.1  # e.g., 0.1 kt or 0.1 pp, set to your policy granularity

  filter_expr = pl.col("Binding") if summary is True else pl.lit(True)
  sensitivity_constr_lf = (
    pl.LazyFrame(sensitivity_constr)
    .filter(pl.col("Pi (Dual Value)").abs().le(pl.lit(pi_tol)).and_(pl.col("Slack").lt(slack_min_step)).not_())
    .with_columns(
      pl.when((pl.col("Slack").abs() < tol) & (pl.col("Pi (Dual Value)") > tol))
      .then(pl.lit("binding_resource"))
      .when((pl.col("Slack").abs() < tol) & (pl.col("Pi (Dual Value)") < -tol))
      .then(pl.lit("binding_requirement"))
      .otherwise(pl.lit("non_binding"))
      .alias("constraint_status")
    )
    .with_columns(pl.col("*").exclude('Constraint', 'Binding', 'constraint_status').round(5))
    .filter(filter_expr)
    # .sort(by='Pi (Dual Value)', descending=True)
  )

  filter_expr = pl.col("Binding") if summary is True else pl.lit(True)
  sensitivity_var_lf = (
    pl.LazyFrame(sensitivity_var)
    .filter(pl.col("Final Value").abs().le(pl.lit(x_tol)).and_(pl.col("RC").abs().le(pl.lit(rc_tol))).not_())
    .with_columns(
      pl.when((pl.col("Final Value") > 0) & (pl.col("RC").abs() < tol))
      .then(pl.lit("utilised"))
      .when((pl.col("Final Value") == 0) & (pl.col("RC") < 0))
      .then(pl.lit("better_if"))
      .when((pl.col("Final Value") == 0) & (pl.col("RC") > 0))
      .then(pl.lit("worse_if"))
      .otherwise(pl.lit("neutral"))
      .alias("variable_status")
    )
    .with_columns(pl.col("*").exclude('Variable', 'Binding', 'variable_status').round(5))
    .filter(filter_expr)
  )

  sensitivity_map_lf = (
    (sensitivity_map_buffer_lf := pl.LazyFrame(sensitivity_map)
    .with_columns(pl.col("*").exclude('Variable', 'Constraint').round(5))
    .join(sensitivity_constr_lf, on='Constraint', suffix="_const")
    .join(sensitivity_var_lf, on='Variable', suffix="_var")
    .rename(dict(Binding='Binding_const'))
    .with_columns(
      (pl.col("Coeff") * pl.col("Pi (Dual Value)")).alias("margin_profit_gain"),
      Fuel=pl.col("Variable").str.extract("x\[([a-zA-Z]+),([^,]+),([^\]]+)\]",1),
      Months=pl.col("Variable").str.extract("x\[([a-zA-Z]+),([^,]+),([^\]]+)\]",2),
      Bands=pl.col("Variable").str.extract("x\[([a-zA-Z]+),([^,]+),([^\]]+)\]",3),
    ))
    # .filter(pl.col('Constraint').str.contains('CapacityLimit').not_())
    .group_by("Fuel", "Constraint")
    .agg(
      pl.col('margin_profit_gain').sum().alias("total_margin_profit_gain"),
      pl.col('Pi (Dual Value)').mean().alias("avg_pi"),
      pl.col('Months').unique(),
      pl.col('Bands').unique(),
      # sum marginal gains, average π, list months/bands.
    )
    .sort("total_margin_profit_gain", descending=True)
  )

  sensitivity_map_buffer_lf = (
    sensitivity_map_buffer_lf
    .filter(pl.col('Pi (Dual Value)').eq(0))
    .with_columns(profit_change_per_unit_tighten=-1 * pl.col("Obj") / pl.col("Coeff"))
    .group_by("Constraint")
    .agg(pl.sum("profit_change_per_unit_tighten"))
  )
  
  result = {
    "roc": roc,
    "fuel_cost": fuel_cost,
    "co2_price": co2_price,
    "so2_reduced_eff": so2_reduced_eff,
    "fgd_cost": fgd_cost,
    "so2_bubble_limit": so2_bubble_limit,
    "so2_price": so2_price,
    "exchange_rate": exchange_rate,
    "biomass_limit": biomass_limit,
    "total_profit": round(model.ObjVal, 2),
    "revenue_minus_transmission": round(rev_minus_tx, 2),
    "roc_incentive": round(roc_incentive, 2),
    "total_fuel_cost": round(total_fuel_cost, 2),
    "total_co2_cost": round(co2_cost, 2),
    "total_so2_cost": round(so2_tonnes * so2_price, 2),
    "co2_emissions": round(0.8 * sum(energy_mb[m,b].getValue() for m in months for b in bands), 2),
    "so2_emissions": round(so2_tonnes, 2),
    "total_generation": round(sum(energy_mb[m,b].getValue() for m in months for b in bands), 2),
    **{f: sum(x[f,m,b].X for m in months for b in bands) for f in fuels}
  }

  return model, fuel_strat_df, result, biomass_share_df, sensitivity_var_lf, sensitivity_constr_lf, sensitivity_map_lf, sensitivity_map_buffer_lf, #energy_mb_df