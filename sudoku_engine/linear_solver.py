#%%
import gurobipy as gp
from gurobipy import GRB

def solve_sudoku_gurobi(grid):
    # grid is 9×9 list of lists with 0 for empty cells
    
    m = gp.Model("sudoku")
    m.Params.OutputFlag = 0  # quiet mode

    digits = range(1, 10)
    rows   = range(9)
    cols   = range(9)

    # Decision variables
    x = m.addVars(rows, cols, digits, vtype=GRB.BINARY, name="x")

    # 1. Each cell has exactly one digit
    for r in rows:
        for c in cols:
            m.addConstr(gp.quicksum(x[r,c,d] for d in digits) == 1)

    # 2. Row constraints
    for r in rows:
        for d in digits:
            m.addConstr(gp.quicksum(x[r,c,d] for c in cols) == 1)

    # 3. Column constraints
    for c in cols:
        for d in digits:
            m.addConstr(gp.quicksum(x[r,c,d] for r in rows) == 1)

    # 4. Block constraints
    for br in range(3):
        for bc in range(3):
            for d in digits:
                m.addConstr(
                    gp.quicksum(
                        x[r, c, d]
                        for r in range(3*br, 3*br + 3)
                        for c in range(3*bc, 3*bc + 3)
                    ) == 1
                )

    # 5. Fix given clues
    for r in rows:
        for c in cols:
            if grid[r][c] != 0:
                d = grid[r][c]
                m.addConstr(x[r,c,d] == 1)

    # Optimize (feasibility)
    m.optimize()

    # Extract solution
    sol = [[0]*9 for _ in range(9)]
    for r in rows:
        for c in cols:
            for d in digits:
                if x[r,c,d].X > 0.5:
                    sol[r][c] = d
    return sol


solution = solve_sudoku_gurobi(puzzle)
for row in solution:
    print(row)