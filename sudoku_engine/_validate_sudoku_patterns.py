#%%
from sudoku_templates import TEMPLATES
from game import _generate_sudoku

def has_unique_solution(grid):
    count = 0

    def solve(g):
        nonlocal count
        if count > 1:
            return  # stop early (we only need to know if >1)
        
        # find empty cell
        for r in range(9):
            for c in range(9):
                if g[r, c] == 0:
                    for num in range(1, 10):
                        if is_valid_move(g, r, c, num):
                            g[r, c] = num
                            solve(g)
                            g[r, c] = 0
                    return
        count += 1

    solve(grid.copy())
    return count == 1

def is_valid_move(grid, r, c, val):
    # row
    if val in grid[r]:
        return False
    
    # col
    if val in grid[:, c]:
        return False
    
    # box
    br = (r//3)*3
    bc = (c//3)*3
    if val in grid[br:br+3, bc:bc+3]:
        return False

    return True

def apply_template(solution, template):
  return solution * template

def test_all_templates(solution):
    results = {}
    for name, template in TEMPLATES.items():
        puzzle = apply_template(solution, template)
        unique = has_unique_solution(puzzle)
        results[name] = unique
        print(f"{name}: {'OK (Unique)' if unique else 'FAIL (Not Unique!)'}")

    print("\nSummary:")
    print(f"Unique templates: {sum(results.values())} / {len(results)}")
    return results

if __name__ == "__main__":
    s = _generate_sudoku()
    results = test_all_templates(s)
# %%
import numpy as np
from gurobipy import Model, GRB, LinExpr
import random

# ============================================================
# Canonical Latin cyclic Sudoku base grid
# ============================================================
def base_grid():
    grid = np.zeros((9,9), dtype=int)
    for r in range(9):
        for c in range(9):
            grid[r,c] = (r*3 + r//3 + c) % 9 + 1
    return grid


# ============================================================
# Group actions: digit permutation, row/col swaps, band/stack swaps,
# transpose. These preserve Sudoku legality.
# ============================================================

def perm_digits(g):
    perm = np.random.permutation(9) + 1
    out = np.zeros_like(g)
    for d in range(1,10):
        out[g==d] = perm[d-1]
    return out

def swap_rows_in_band(g):
    b = random.choice([0,3,6])
    r1, r2 = random.sample([b, b+1, b+2], 2)
    g = g.copy()
    g[[r1, r2]] = g[[r2, r1]]
    return g

def swap_cols_in_stack(g):
    s = random.choice([0,3,6])
    c1, c2 = random.sample([s, s+1, s+2], 2)
    g = g.copy()
    g[:,[c1, c2]] = g[:,[c2, c1]]
    return g

def swap_bands(g):
    b1, b2 = random.sample([0,3,6], 2)
    g = g.copy()
    g[b1:b1+3, :], g[b2:b2+3, :] = g[b2:b2+3, :].copy(), g[b1:b1+3, :].copy()
    return g

def swap_stacks(g):
    s1, s2 = random.sample([0,3,6], 2)
    g = g.copy()
    g[:,s1:s1+3], g[:,s2:s2+3] = g[:,s2:s2+3].copy(), g[:,s1:s1+3].copy()
    return g

def transpose(g):
    return g.T.copy()


# ============================================================
# Create one random group-transformed Sudoku
# ============================================================
def random_transform(g):
    ops = [
        perm_digits, swap_rows_in_band, swap_cols_in_stack,
        swap_bands,  swap_stacks,       transpose
    ]
    g2 = g.copy()
    # Apply 5–10 random operations
    for _ in range(random.randint(5,10)):
        op = random.choice(ops)
        g2 = op(g2)
    return g2


# ============================================================
# Generate MANY solutions from orbit of base grid
# ============================================================
def sample_orbit(n=300):
    B = base_grid()
    sols = []
    for _ in range(n):
        sols.append(random_transform(B))
    return sols


def build_and_solve_template_ILP(
    num_samples = 300,
    min_clues   = 25,    # realistic lower bound
    symmetry    = True   # enforce 180° rotational symmetry
):

    print(f"Generating {num_samples} group-orbit solutions...")
    solutions = sample_orbit(num_samples)

    # Flatten
    sol_flat = np.array([s.reshape(-1) for s in solutions])
    N, M = sol_flat.shape  # N samples, M=81 cells

    # Build distinguishing pairs
    print("Computing pairwise differences...")
    pairs = []
    for a in range(N):
        for b in range(a+1, N):
            diff = np.where(sol_flat[a] != sol_flat[b])[0]
            if diff.size > 0:  # always true for orbit samples
                pairs.append(diff.tolist())

    print(f"Number of uniqueness constraints: {len(pairs)}")

    # Build model
    print("Building ILP...")
    model = Model("group_universal_sudoku_template")
    T = model.addVars(M, vtype=GRB.BINARY, name="T")

    # Uniqueness constraints
    print("Adding constraints...")
    for idx, diff_list in enumerate(pairs):
        expr = LinExpr()
        for c in diff_list:
            expr.addTerms(1.0, T[c])
        model.addConstr(expr >= 1, name=f"pair_{idx}")

    # Optional 180-degree rotational symmetry
    if symmetry:
        for i in range(M):
            j = 80 - i  # rotate index 0<->80, 1<->79, ...
            model.addConstr(T[i] == T[j])

    # Minimum clues constraint
    if min_clues is not None:
        model.addConstr(sum(T[i] for i in range(M)) >= min_clues,
                        name="min_clues")

    # Objective: minimize clues
    model.setObjective(sum(T[i] for i in range(M)), GRB.MINIMIZE)

    print("Optimizing...")
    model.optimize()

    # Extract template
    if model.status == GRB.OPTIMAL:
        vec = np.array([int(T[i].X) for i in range(M)])
        tmpl = vec.reshape(9, 9)
        print("\n========== OPTIMAL GROUP-UNIVERSAL TEMPLATE ==========")
        print(tmpl)
        print("Number of clues:", vec.sum())
        print("=======================================================\n")
        return tmpl
    else:
        print("ILP did not find optimal solution.")
        return None
    


if __name__ == "__main__":
    template = build_and_solve_template_ILP(
        num_samples = 300,     # 300 orbit solutions
        min_clues   = 25,      # avoid trivial templates
        symmetry    = True     # enforce nice symmetric patterns
    )
# %%
for _ in range(30):
    s = random_transform(base_grid())
    puzzle = apply_template(s, template)
    print(has_unique_solution(puzzle))
# %%
