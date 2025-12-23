# %%
import gurobipy as gp
from gurobipy import GRB
import polars as pl
import matplotlib.pyplot as plt
import itertools

# Data
student_operators = {"E. Khan", "Y. Chen", "A. Taylor", "R. Zidane", "R. Perez", "C. Santos"}
bachelor_students = {"E. Khan", "Y. Chen", "A. Taylor", "R. Zidane"}
assert bachelor_students.issubset(student_operators)
master_students = {"R. Perez", "C. Santos"}
assert master_students.issubset(student_operators)

DayofWeek = {"Mon", "Tue", "Wed", "Thu", "Fri"}

WageRate = {
    "E. Khan": 25,
    "Y. Chen": 26,
    "A. Taylor": 24,
    "R. Zidane": 23,
    "R. Perez": 28,
    "C. Santos": 30
}

avail_hours = gp.tupledict({
    ("Mon", "E. Khan"): 6, ("Tue", "E. Khan"): 0, ("Wed", "E. Khan"): 6, ("Thu", "E. Khan"): 0, ("Fri", "E. Khan"): 6,
    ("Mon", "Y. Chen"): 0, ("Tue", "Y. Chen"): 6, ("Wed", "Y. Chen"): 0, ("Thu", "Y. Chen"): 6, ("Fri", "Y. Chen"): 0,
    ("Mon", "A. Taylor"): 4, ("Tue", "A. Taylor"): 8, ("Wed", "A. Taylor"): 4, ("Thu", "A. Taylor"): 0,
    ("Fri", "A. Taylor"): 4,
    ("Mon", "R. Zidane"): 5, ("Tue", "R. Zidane"): 5, ("Wed", "R. Zidane"): 5, ("Thu", "R. Zidane"): 0,
    ("Fri", "R. Zidane"): 5,
    ("Mon", "R. Perez"): 3, ("Tue", "R. Perez"): 0, ("Wed", "R. Perez"): 3, ("Thu", "R. Perez"): 8,
    ("Fri", "R. Perez"): 0,
    ("Mon", "C. Santos"): 0, ("Tue", "C. Santos"): 0, ("Wed", "C. Santos"): 0, ("Thu", "C. Santos"): 6,
    ("Fri", "C. Santos"): 2
})

model = gp.Model('lexicographic_optimization_3stage_allpairs')
model.setParam('OutputFlag', 0)  # Suppress output for cleaner print

# Variables
H = model.addVars(DayofWeek, student_operators, lb=0, ub=avail_hours, vtype=GRB.INTEGER, name='H')
Z_max = model.addVar(vtype=GRB.INTEGER, name="Max_Workload")
Z_min = model.addVar(vtype=GRB.INTEGER, name="Min_Workload")

# Constraints
model.addConstrs(
    (gp.quicksum(H[d, o] for d in DayofWeek) >= 8 for o in bachelor_students),
    name='Bachelor_Min_Commitment'
)

model.addConstrs(
    (gp.quicksum(H[d, o] for d in DayofWeek) >= 7 for o in master_students),
    name='Master_Min_Commitment'
)

model.addConstrs(
    (gp.quicksum(H[d, o] for o in student_operators) == 14 for d in DayofWeek),
    name='Mainframe_Operating_Hours_per_Day'
)

# Initial Minimum Cost
total_wage = gp.quicksum(H[d, o] * WageRate[o] for d in DayofWeek for o in student_operators)
model.setObjective(total_wage, GRB.MINIMIZE)
model.optimize()
min_cost = model.ObjVal


# Link Variables to Hours
weekly_hours = {o: gp.quicksum(H[d, o] for d in DayofWeek) for o in student_operators}
model.addConstrs((Z_max >= weekly_hours[o] for o in student_operators), name="Link_Max")
model.addConstrs((Z_min <= weekly_hours[o] for o in student_operators), name="Link_Min")

# All-Pairs Minimization)
# Minimize the absolute difference between every possible pair of students.

diff_vars = []
# Create a list from the set to iterate reliably
student_list = list(student_operators)

for s1, s2 in itertools.combinations(student_list, 2):
    # Helper variable for |Hours_1 - Hours_2|
    d_var = model.addVar(lb=0, name=f"Diff_{s1}_{s2}")

    # Linearize Absolute Value: D >= A - B and D >= B - A
    model.addConstr(d_var >= weekly_hours[s1] - weekly_hours[s2])
    model.addConstr(d_var >= weekly_hours[s2] - weekly_hours[s1])
    diff_vars.append(d_var)

# Objective: Minimize the sum of all pair differences
model.setObjective(gp.quicksum(diff_vars), GRB.MINIMIZE)
model.optimize()

# --- RESULTS ---
if model.Status == GRB.OPTIMAL:
    final_cost = total_wage.getValue()
    final_hours = {o: sum(H[d, o].X for d in DayofWeek) for o in student_operators}
    max_h = max(final_hours.values())
    min_h = min(final_hours.values())
    gap = max_h - min_h
    print(f"Initial Min Cost: £{min_cost:.2f}")
    print(f"Final Cost: £{final_cost:.2f}")
    print(f"Workload Gap: {gap:.2f} hours (Max: {max_h}, Min: {min_h})")

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
print(
    pl.DataFrame(results)
    .pivot(on='DayofWeek', index='Student', values='Hour')
    .select(pl.col('Student').replace(mapping).alias("order_idx"), 'Student', "Mon", "Tue", "Wed", "Thu", "Fri")
    .sort("order_idx")
    .drop("order_idx")
)

# Aggregate total hours per student
summary = (
    pl.DataFrame(results)
    .group_by("Student")
    .agg(pl.col("Hour").sum())
    .sort("Hour", descending=True)
)

# Extract data for plotting
students = summary["Student"].to_list()
hours = summary["Hour"].to_list()

# Create the bar plot
plt.figure(figsize=(10, 6))
bars = plt.bar(students, hours, color='darkgreen')

for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f'{height:.2f}',
        ha='center',
        va='bottom'
    )

plt.title('Total Weekly Workload Distribution per Student', fontsize=14)
plt.xlabel('Student Name', fontsize=12)
plt.ylabel('Total Hours Scheduled', fontsize=12)
plt.show()