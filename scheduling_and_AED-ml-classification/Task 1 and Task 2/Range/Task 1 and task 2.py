
import gurobipy as gp
from gurobipy import GRB
import polars as pl
import matplotlib.pyplot as plt

# Fix Polars display for wide tables
pl.Config.set_tbl_width_chars(1000)
pl.Config.set_tbl_cols(-1)

# Data
student_operators = {"E. Khan", "Y. Chen", "A. Taylor", "R. Zidane", "R. Perez", "C. Santos"}
bachelor_students = {"E. Khan", "Y. Chen", "A. Taylor", "R. Zidane"}
# The assert statements check that bachelor/master students are valid operators
assert bachelor_students.issubset(student_operators)
master_students = {"R. Perez", "C. Santos"}
assert master_students.issubset(student_operators)

DAYS_OF_WEEK = {"Mon", "Tue", "Wed", "Thu", "Fri"}

WAGE_RATES = {
  "E. Khan":   25,
  "Y. Chen":   26,
  "A. Taylor": 24,
  "R. Zidane": 23,
  "R. Perez":  28,
  "C. Santos": 30
}

# (Day, Operator)-> Hours available
avail_hours = gp.tupledict({
  ("Mon", "E. Khan"):   6,  ("Tue", "E. Khan"): 0,  ("Wed", "E. Khan"): 6,  ("Thu", "E. Khan"): 0,  ("Fri", "E. Khan"): 6,
  ("Mon", "Y. Chen"):   0,  ("Tue", "Y. Chen"): 6,  ("Wed", "Y. Chen"): 0,  ("Thu", "Y. Chen"): 6,  ("Fri", "Y. Chen"): 0,
  ("Mon", "A. Taylor"): 4,  ("Tue", "A. Taylor"): 8,("Wed", "A. Taylor"): 4,("Thu", "A. Taylor"): 0,("Fri", "A. Taylor"): 4,
  ("Mon", "R. Zidane"): 5,  ("Tue", "R. Zidane"): 5,("Wed", "R. Zidane"): 5,("Thu", "R. Zidane"): 0,("Fri", "R. Zidane"): 5,
  ("Mon", "R. Perez"):  3,  ("Tue", "R. Perez"): 0, ("Wed", "R. Perez"): 3, ("Thu", "R. Perez"): 8, ("Fri", "R. Perez"): 0,
  ("Mon", "C. Santos"): 0,  ("Tue", "C. Santos"): 0,("Wed", "C. Santos"): 0,("Thu", "C. Santos"): 6,("Fri", "C. Santos"): 2
})

def plot_weekly_workload(weekly_hours, title, scenario_name):
    """
    Create a bar chart showing the total weekly workload distribution per student
    """
    students = list(weekly_hours.keys())
    hours = list(weekly_hours.values())
    
    # Create the bar plot
    plt.figure(figsize=(10, 6))
    bars = plt.bar(students, hours, color='darkgreen')
    
    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f'{height:.2f}',
            ha='center',
            va='bottom',
            fontsize=10
        )
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Student Name', fontsize=12)
    plt.ylabel('Total Hours Scheduled', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.show()

def solve_task1_baseline():
    """
    Solve Task 1 to get baseline cost and schedule
    """

    print("\nTASK 1: BASELINE COST MINIMIZATION")
    print("="*80)

    model = gp.Model('task1_baseline')
    
    # Creates a variable for every combination of (day, operator)
    # H[d, o] = hours assigned to operator 'o' on day 'd'
    # variables will be named H[Mon,E. Khan], H[Tue,Y. Chen] 
    # => H["Mon", "E. Khan"] -> [0, 6],  H["Tue", "E. Khan"] -> [0, 0] 
    H = model.addVars(DAYS_OF_WEEK, student_operators, lb=0, ub=avail_hours, name='H')
    
    # Constraints: Minimum weekly commitments for bachelor students
    # H[Mon,E. Khan] + H[Tue,E. Khan] + ... + H[Fri,E. Khan] >= 8
    model.addConstrs(
        (gp.quicksum(H[d, o] for d in DAYS_OF_WEEK) >= 8 for o in bachelor_students),
        name='Bachelor_Min'
    )
    
    # Constraints: Minimum weekly commitments for master students
    # H[Mon,R. Perez] + H[Tue,R. Perez] + ... + H[Fri,R. Perez] >= 7
    model.addConstrs(
        (gp.quicksum(H[d, o] for d in DAYS_OF_WEEK) >= 7 for o in master_students),
        name='Master_Min'
    )
    
    # Constraints: Mainframe operating hours per day
    # For each day, Sum hours from all operators on that day
    # H[Mon,E. Khan] + H[Mon,Y. Chen] + ... + H[Mon,C. Santos] == 14
    model.addConstrs(
        (gp.quicksum(H[d, o] for o in student_operators) == 14 for d in DAYS_OF_WEEK),
        name='Daily_Coverage'
    )
    
    # Objective: Minimize cost
    model.setObjective(
        gp.quicksum(H[d, o] * WAGE_RATES[o] 
        for d in DAYS_OF_WEEK for o in student_operators),
        GRB.MINIMIZE
    )
    
    model.optimize()

    if model.status == GRB.OPTIMAL:
        optimal_cost = model.objVal
        
        # Calculate weekly hours for each operator
        weekly_hours = {}
        for o in student_operators:
            weekly_hours[o] = sum(H[d, o].X for d in DAYS_OF_WEEK)
        
        # max, min, range of weekly hours across all operators
        max_hours = max(weekly_hours.values())
        min_hours = min(weekly_hours.values())
        range_hours = max_hours - min_hours
        
        print(f"\nOptimal Cost: £{optimal_cost:.2f}")
        print(f"\nFairness Metrics:")
        print(f"  Max hours: {max_hours:.2f}")
        print(f"  Min hours: {min_hours:.2f}")
        print(f"  Range (max - min): {range_hours:.2f} hours")
           
        # Display full schedule
        display_schedule(H, "TASK 1: BASELINE SCHEDULE")

        # Create visualization plot
        plot_weekly_workload(weekly_hours, 
                           'Task 1: Baseline Weekly Workload Distribution', 
                           'task1_baseline')

        print("\n" + "="*80)
        
        return optimal_cost, H, weekly_hours, range_hours
    
    return None, None, None, None

def solve_scenario_i(baseline_cost, baseline_range):
    """
    Scenario i: Achieve fairer distribution while allowing up to 1.8% cost increase
    
    To do: Minimize the range (max_hours - min_hours) subject to cost constraint
    """
    print("\nTASK 2: SCENARIO i - FAIRNESS WITH MAX 1.8% COST INCREASE")
  
    # Calculate maximum allowed cost
    max_cost = baseline_cost * 1.018  # 1.8% increase
    print(f"\nBaseline cost: £{baseline_cost:.2f}")
    print(f"Maximum allowed cost (1.8% increase): £{max_cost:.2f}")
    
    model = gp.Model('scenario_i')
    
    # Variables: Hours assigned to each operator on each day
    H = model.addVars(DAYS_OF_WEEK, student_operators, lb=0, ub=avail_hours, name='H')
    
    # Variables: max and min weekly hours across all operators
    max_weekly = model.addVar(lb=0, name='max_weekly')
    min_weekly = model.addVar(lb=0, name='min_weekly')
    
    # Variable: Range (what we want to minimize)
    range_var = model.addVar(lb=0, name='range')
   
    # Constraints: Minimum weekly commitments for bachelor students
    model.addConstrs(
        (gp.quicksum(H[d, o] for d in DAYS_OF_WEEK) >= 8 for o in bachelor_students),
        name='Bachelor_Min'
    )
    
    # Constraints: Minimum weekly commitments for master students
    model.addConstrs(
        (gp.quicksum(H[d, o] for d in DAYS_OF_WEEK) >= 7 for o in master_students),
        name='Master_Min'
    )
    
    # Constraints: Mainframe operating hours per day
    model.addConstrs(
        (gp.quicksum(H[d, o] for o in student_operators) == 14 for d in DAYS_OF_WEEK),
        name='Daily_Coverage'
    )
    
    # Constraints: Track max and min weekly hours across all operators
    for o in student_operators:
        weekly_hours_o = gp.quicksum(H[d, o] for d in DAYS_OF_WEEK)
        model.addConstr(max_weekly >= weekly_hours_o, f'max_track_{o}')
        model.addConstr(min_weekly <= weekly_hours_o, f'min_track_{o}')
    
    # Constraint: Range definition 
    model.addConstr(range_var == max_weekly - min_weekly, 'range_def')
    
    # Constraint: Cost cannot exceed 1.8% increase
    total_cost = gp.quicksum(H[d, o] * WAGE_RATES[o] for d in DAYS_OF_WEEK for o in student_operators)
    model.addConstr(total_cost <= max_cost, 'cost_limit')
   
    # Objective: Minimize the range (for fairness)
    model.setObjective(range_var, GRB.MINIMIZE)
    
    model.optimize()
    
    if model.status == GRB.OPTIMAL:
        actual_cost = sum(H[d, o].X * WAGE_RATES[o] for d in DAYS_OF_WEEK for o in student_operators)
        cost_increase = actual_cost - baseline_cost
        cost_increase_pct = (cost_increase / baseline_cost) * 100
        within_budget = round(cost_increase_pct, 2) <= 1.8

        weekly_hours = {}
        for o in student_operators:
            weekly_hours[o] = sum(H[d, o].X for d in DAYS_OF_WEEK)
        
        print(f"\nSOLUTION FOUND")
        print(f"\nCost Analysis:")
        print(f"  Actual cost: £{actual_cost:.2f}")
        print(f"  Cost increase: £{cost_increase:.2f} ({cost_increase_pct:.2f}%)")
        print(f"  Within budget: {'Yes' if within_budget else 'No'}")
        
        print(f"\nFairness Metrics:")
        print(f"  Max hours: {max_weekly.X:.2f}")
        print(f"  Min hours: {min_weekly.X:.2f}")
        print(f"  Range: {range_var.X:.2f} hours")
        print(f"  Improvement from Task 1: {baseline_range - range_var.X:.2f} hours reduction in range")
        
        # Display full schedule
        display_schedule(H, "TASK 2: SCENARIO i SCHEDULE")
        
        # Create visualization plot
        plot_weekly_workload(weekly_hours, 
                           'Task 2 Scenario i: Fairer Workload Distribution (≤1.8% Cost Increase)', 
                           'task2_scenario_i')

        return model, H, weekly_hours
    else:
        print(f"\nNo solution found. Status: {model.status}")
        return None, None, None

def solve_scenario_ii(baseline_range):
    """
    Scenario ii: Find the fairest possible distribution
    
    To do: Minimize range without cost constraint, then report the cost
    """
    print("\nTASK 2: SCENARIO ii - MAXIMUM FAIRNESS")
  
    model = gp.Model('scenario_ii')
    
    # Variables : Hours assigned to each operator on each day
    H = model.addVars(DAYS_OF_WEEK, student_operators, lb=0, ub=avail_hours, name='H')

    # Variables: Max and min weekly hours across all operators
    max_weekly = model.addVar(lb=0, name='max_weekly')
    min_weekly = model.addVar(lb=0, name='min_weekly')

    # Variable: Range (what we want to minimize)
    range_var = model.addVar(lb=0, name='range')
    
    # Constraints: Minimum weekly commitments for bachelor students
    model.addConstrs(
        (gp.quicksum(H[d, o] for d in DAYS_OF_WEEK) >= 8 for o in bachelor_students),
        name='Bachelor_Min'
    )
    
    # Constraints: Minimum weekly commitments for master students
    model.addConstrs(
        (gp.quicksum(H[d, o] for d in DAYS_OF_WEEK) >= 7 for o in master_students),
        name='Master_Min'
    )
    
    # Constraints: Mainframe operating hours per day
    model.addConstrs(
        (gp.quicksum(H[d, o] for o in student_operators) == 14 for d in DAYS_OF_WEEK),
        name='Daily_Coverage'
    )
  
    # Constraints: Track max and min weekly hours across all operators
    for o in student_operators:
        weekly_hours_o = gp.quicksum(H[d, o] for d in DAYS_OF_WEEK)
        model.addConstr(max_weekly >= weekly_hours_o, f'max_track_{o}')
        model.addConstr(min_weekly <= weekly_hours_o, f'min_track_{o}')
    
    # Constraint: Range definition
    model.addConstr(range_var == max_weekly - min_weekly, 'range_def')
  
    # Objective: Minimize range (NO cost constraint)
    model.setObjective(range_var, GRB.MINIMIZE)
    
    model.optimize()
    
    if model.status == GRB.OPTIMAL:
        actual_cost = sum(H[d, o].X * WAGE_RATES[o] for d in DAYS_OF_WEEK for o in student_operators)
        
        weekly_hours = {}
        for o in student_operators:
            weekly_hours[o] = sum(H[d, o].X for d in DAYS_OF_WEEK)
        
        print(f"\nFAIREST POSSIBLE SOLUTION FOUND")
        print(f"\nFairness Metrics:")
        print(f"  Max hours: {max_weekly.X:.2f}")
        print(f"  Min hours: {min_weekly.X:.2f}")
        print(f"  Range: {range_var.X:.2f} hours (MINIMUM POSSIBLE)")
        print(f"  Improvement from Task 1: {baseline_range - range_var.X:.2f} hours reduction in range")
        
        print(f"\nCost Analysis:")
        print(f"  Total cost for fairness: £{actual_cost:.2f}")
        
        # Display full schedule
        display_schedule(H, "TASK 2: SCENARIO ii SCHEDULE (MAXIMUM FAIRNESS)")
        
        # Create visualization plot
        plot_weekly_workload(weekly_hours, 
                           'Task 2 Scenario ii: Maximum Fairness Workload Distribution', 
                           'task2_scenario_ii')

        return model, H, weekly_hours
    else:
        print(f"\nNo solution found. Status: {model.status}")
        return None, None, None


def display_schedule(H, title):

    print("\n" + "="*80)
    print(title)
    print("="*80)
    
    results = []
    for d in DAYS_OF_WEEK:
        for o in student_operators:
            results.append({
                "Student": o,
                "DAYS_OF_WEEK": d,
                "Hour": H[d, o].X,
            })
    
    # Create order mapping for consistent display
    mapping = {v: i for i, v in enumerate(student_operators)}
    
    schedule_df = (
        pl.DataFrame(results)
        .pivot(on='DAYS_OF_WEEK', index='Student', values='Hour')
        # Adds a temporary ordering column to sort students in the right order
        .select(
            pl.col('Student').replace(mapping).alias("order_idx"), 
            'Student', 
            "Mon", "Tue", "Wed", "Thu", "Fri"
        )
        .sort("order_idx")
        # Drops the temporary ordering column
        .drop("order_idx")
        # weekly total hours for each operator
        # FIRST: Create Total Hours and Wage Rate columns
        .with_columns([
            pl.sum_horizontal("Mon", "Tue", "Wed", "Thu", "Fri").alias("Total Hours"),
            pl.col("Student").replace(WAGE_RATES).cast(pl.Float64).alias("Wage Rate (£/hr)"), 
        ])
        # THEN: Create Total Cost column using the columns we just created
        .with_columns([
            (pl.col("Total Hours") * pl.col("Wage Rate (£/hr)")).alias("Total Cost (£)")
        ])
    )
    
    print(schedule_df)

# Solve Task 1 - LP model to determine the optimal allocation of hours 
# for each operator per day, minimising total labour costs.
baseline_cost, baseline_H, baseline_hours, baseline_range = solve_task1_baseline()
    
if baseline_cost is None:
    print("ERROR: Could not solve Task 1 : Cost could not be determined.")
    exit()

# Solve Task 2 - Scenario i - Fairness with max 1.8% cost increase
scenario_i_model, scenario_i_H, scenario_i_hours = solve_scenario_i(baseline_cost, baseline_range)

# Solve Task 2 - Scenario ii - Maximum fairness and determine the minimum overall cost increase required
scenario_ii_model, scenario_ii_H, scenario_ii_hours = solve_scenario_ii(baseline_range)