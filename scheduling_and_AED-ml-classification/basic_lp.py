#%%
import gurobipy as gp
from gurobipy import GRB
import polars as pl

# Data
student_operators = {"E. Khan", "Y. Chen", "A. Taylor", "R. Zidane", "R. Perez", "C. Santos"}
bachelor_students = {"E. Khan", "Y. Chen", "A. Taylor", "R. Zidane"}
assert bachelor_students.issubset(student_operators)
master_students = {"R. Perez", "C. Santos"}
assert master_students.issubset(student_operators)

DayofWeek = {"Mon", "Tue", "Wed", "Thu", "Fri"}

WageRate = {
  "E. Khan":   25,
  "Y. Chen":   26,
  "A. Taylor": 24,
  "R. Zidane": 23,
  "R. Perez":  28,
  "C. Santos": 30
}

avail_hours = gp.tupledict({
  ("Mon", "E. Khan"):   6,  ("Tue", "E. Khan"): 0,  ("Wed", "E. Khan"): 6,  ("Thu", "E. Khan"): 0,  ("Fri", "E. Khan"): 6,
  ("Mon", "Y. Chen"):   0,  ("Tue", "Y. Chen"): 6,  ("Wed", "Y. Chen"): 0,  ("Thu", "Y. Chen"): 6,  ("Fri", "Y. Chen"): 0,
  ("Mon", "A. Taylor"): 4,  ("Tue", "A. Taylor"): 8,("Wed", "A. Taylor"): 4,("Thu", "A. Taylor"): 0,("Fri", "A. Taylor"): 4,
  ("Mon", "R. Zidane"): 5,  ("Tue", "R. Zidane"): 5,("Wed", "R. Zidane"): 5,("Thu", "R. Zidane"): 0,("Fri", "R. Zidane"): 5,
  ("Mon", "R. Perez"):  3,  ("Tue", "R. Perez"): 0, ("Wed", "R. Perez"): 3, ("Thu", "R. Perez"): 8, ("Fri", "R. Perez"): 0,
  ("Mon", "C. Santos"): 0,  ("Tue", "C. Santos"): 0,("Wed", "C. Santos"): 0,("Thu", "C. Santos"): 6,("Fri", "C. Santos"): 2
})

# Model
model = gp.Model('basic_scheduling')

# Variables
H = model.addVars(DayofWeek, student_operators, lb=0, ub=avail_hours, name='H')

# Constraints
Bachelor_Min_Commitments = model.addConstrs(
  (gp.quicksum(H[d, o] for d in DayofWeek) >= 8 for o in bachelor_students),
  name='Bachelor_Min_Commitment'
)

Master_Min_Commitments = model.addConstrs(
  (gp.quicksum(H[d, o] for d in DayofWeek) >= 7 for o in master_students),
  name='Master_Min_Commitment'
)

Mainframe_Operating_Hours_per_Days = model.addConstrs(
  (gp.quicksum(H[d, o] for o in student_operators) == 14 for d in DayofWeek),
  name='Mainframe_Operating_Hours_per_Day'
)

# Objectives
model.setObjective(
  gp.quicksum(
    H[d, o] * WageRate[o]
    for d in DayofWeek for o in student_operators
  ),
  GRB.MINIMIZE
)

model.optimize()
Z_star = model.objVal
# %%
results = []
for d in DayofWeek:
  for o in student_operators:
    results.append({
      "Student": o,
      "DayofWeek": d,
      "Hour": H[d, o].X,
    })
# %%
mapping = {v: i for i, v in enumerate(["E. Khan", "Y. Chen", "A. Taylor", "R. Zidane", "R. Perez", "C. Santos"])}
print('Schedule:')
(
  pl.DataFrame(results)
  .pivot(on='DayofWeek', index='Student', values='Hour')
  .select(pl.col('Student').replace(mapping).alias("order_idx"), 'Student', "Mon", "Tue", "Wed", "Thu", "Fri")
  .sort("order_idx")
  .drop("order_idx")
)

#%%
# Model
model2 = gp.Model('fair_scheduling')

allowed_cost = (1 + 0.018) * Z_star

# Variables
H_o = {o: gp.quicksum(H[d, o] for d in DayofWeek) for o in student_operators}
H_max = model2.addVar(lb=0, name='H_max')
H_min = model2.addVar(lb=0, name='H_min')

# Objectives
model2.setObjective(
  H_max - H_min,
  GRB.MINIMIZE
)

# Constraints
# lower bound

model2.addConstrs(
  (H_o[o] == gp.quicksum(H[d, o] for d in DayofWeek) for o in student_operators),
  name="Min_Hours"
)

model2.addConstrs(
  (H_o[o] >= H_min for o in student_operators),
  name="Min_Hours"
)

# upper bound
model2.addConstrs(
  (H_o[o] <= H_max for o in student_operators),
  name="Max_Hours"
)

TotalCost2 = gp.quicksum(
  H[d, o] * WageRate[o] 
  for d in DayofWeek 
  for o in student_operators
)

Cost_Cap = model2.addConstr(TotalCost2 <= allowed_cost, name="Cost_Cap")
model2.optimize()
# %%
