#%%
import numpy as np

# ----------------------------------------------------
# Fast Sudoku Solver with MRV + Forward Checking
# ----------------------------------------------------

def find_empty_mrv(grid):
    """Return the empty cell with the fewest candidates."""
    best = None
    best_count = 10
    for r in range(9):
        for c in range(9):
            if grid[r, c] == 0:
                candidates = get_candidates(grid, r, c)
                if len(candidates) < best_count:
                    best_count = len(candidates)
                    best = (r, c, candidates)
                if best_count == 1:
                    return best
    return best  # may be None if no empty cells


def get_candidates(grid, r, c):
    """Return the set of legal candidates for a cell."""
    used = set(grid[r, :]) | set(grid[:, c])
    br = (r // 3) * 3
    bc = (c // 3) * 3
    used |= set(grid[br:br+3, bc:bc+3].flatten())
    used.discard(0)
    return [n for n in range(1, 10) if n not in used]


def sudoku_solver_count(grid, limit=2):
    """
    Count how many solutions the puzzle has.
    limit = 2 means: stop after finding 2 solutions.
    """
    grid = grid.copy()
    count = 0

    def backtrack():
        nonlocal count
        if count >= limit:
            return

        mrv = find_empty_mrv(grid)
        if mrv is None:
            count += 1
            return

        r, c, candidates = mrv
        for val in candidates:
            grid[r, c] = val
            backtrack()
            grid[r, c] = 0
            if count >= limit:
                return

    backtrack()
    return count

def has_unique_solution(grid):
    """Return True if exactly one solution exists."""
    return sudoku_solver_count(grid, limit=10) == 1

def is_solvable(grid):
    """Return True if at least one solution exists."""
    return sudoku_solver_count(grid, limit=1) >= 1

#%%
import numpy as np
from numpy.random import default_rng

_rng = default_rng()

# ============================================================
#               SOLVER (MRV + Forward Checking)
# ============================================================

def get_candidates(grid, r, c):
    used = set(grid[r]) | set(grid[:, c])
    br = (r // 3) * 3
    bc = (c // 3) * 3
    used |= set(grid[br:br+3, bc:bc+3].flatten())
    used.discard(0)
    return [n for n in range(1, 10) if n not in used]


def find_empty_mrv(grid):
    best = None
    best_count = 10
    for r in range(9):
        for c in range(9):
            if grid[r, c] == 0:
                cand = get_candidates(grid, r, c)
                if len(cand) < best_count:
                    best = (r, c, cand)
                    best_count = len(cand)
                if best_count == 1:
                    return best
    return best


def sudoku_solver_count(grid, limit=2):
    grid = grid.copy()
    count = 0

    def backtrack():
        nonlocal count
        if count >= limit:
            return

        cell = find_empty_mrv(grid)
        if cell is None:
            count += 1
            return
        
        r, c, candidates = cell
        for v in candidates:
            grid[r, c] = v
            backtrack()
            grid[r, c] = 0
            if count >= limit:
                return

    backtrack()
    return count


def has_unique_solution(grid):
    return sudoku_solver_count(grid, limit=2) == 1


def is_solvable(grid):
    return sudoku_solver_count(grid, limit=1) >= 1


# ============================================================
#              GENERATE A COMPLETE SOLVED GRID
# ============================================================

def generate_solved_grid():
    grid = np.zeros((9, 9), dtype=int)

    def is_valid(grid, r, c, v):
        if v in grid[r]: return False
        if v in grid[:, c]: return False
        br, bc = (r//3)*3, (c//3)*3
        if v in grid[br:br+3, bc:bc+3]: return False
        return True

    def fill(idx=0):
        if idx == 81:
            return True
        r, c = idx // 9, idx % 9

        nums = list(range(1, 10))
        _rng.shuffle(nums)
        for v in nums:
            if is_valid(grid, r, c, v):
                grid[r, c] = v
                if fill(idx + 1):
                    return True
                grid[r, c] = 0
        return False

    fill()
    return grid


# ============================================================
#           PUZZLE GENERATOR WITH UNIQUENESS CHECK
# ============================================================

def generate_puzzle(unique=True, symmetric=False, min_clues=25):
    """
    Generate a Sudoku puzzle with optional symmetry.
    Always ensures unique solution if unique=True.
    """
    solution = generate_solved_grid()
    puzzle = solution.copy()

    # Cells to remove in random order
    cells = [(r, c) for r in range(9) for c in range(9)]
    _rng.shuffle(cells)

    for r, c in cells:
        if puzzle[r, c] == 0:
            continue

        saved = puzzle[r, c]

        # Remove
        puzzle[r, c] = 0

        # If symmetric mode, also remove mirrored cell
        if symmetric:
            r2, c2 = 8-r, 8-c
            saved2 = puzzle[r2, c2]
            puzzle[r2, c2] = 0

        # Check constraints
        if unique and not has_unique_solution(puzzle):
            # Restore if uniqueness is broken
            puzzle[r, c] = saved
            if symmetric:
                puzzle[r2, c2] = saved2
            continue

        # Ensure minimum clues
        if np.count_nonzero(puzzle) < min_clues:
            break

    return puzzle, solution


# ============================================================
#               FULL COMMON GENERATOR MODES
# ============================================================

def generate_easy():
    return generate_puzzle(unique=True, symmetric=True, min_clues=36)

def generate_medium():
    return generate_puzzle(unique=True, symmetric=True, min_clues=30)

def generate_hard():
    return generate_puzzle(unique=True, symmetric=False, min_clues=26)

def generate_minimal():
    return generate_puzzle(unique=True, symmetric=False, min_clues=17)


# ============================================================
#                             DEMO
# ============================================================

if __name__ == "__main__":
    puzzle, solution = generate_hard()  # choose desired difficulty

    print("\nPuzzle (0 = blank):")
    print(puzzle)
    print("\nSolution:")
    print(solution)
    print("\nUnique:", has_unique_solution(puzzle))
# %%
has_unique_solution(puzzle)
# %%
sudoku_solver_count(puzzle, 10000)
# %%
import random

# --- Helper functions ---

def build_base(n=3):
    """Construct an n^2 x n^2 Sudoku base grid via modular arithmetic."""
    N = n * n
    return [[(r * n + r // n + c) % N + 1 for c in range(N)] for r in range(N)]

# Symmetry operations

def shuffle_rows(board, n=3):
    N = n * n
    # shuffle rows within bands
    bands = [list(range(i*n, (i+1)*n)) for i in range(n)]
    for band in bands:
        random.shuffle(band)
    row_order = sum(bands, [])
    # shuffle row bands
    band_order = list(range(n))
    random.shuffle(band_order)
    row_order = sum([row_order[i*n:(i+1)*n] for i in band_order], [])
    return [board[r] for r in row_order]

def shuffle_cols(board, n=3):
    N = n * n
    # transpose operations for columns
    transposed = list(zip(*board))
    shuffled = shuffle_rows(transposed, n)
    return [list(row) for row in zip(*shuffled)]

def permute_digits(board):
    digits = list(range(1, len(board) + 1))
    mapping = dict(zip(digits, random.sample(digits, len(digits))))
    return [[mapping[val] for val in row] for row in board]

def randomize(board, n=3):
    board = permute_digits(board)
    board = shuffle_rows(board, n)
    board = shuffle_cols(board, n)
    # optional transpose with 50% chance
    if random.choice([True, False]):
        board = [list(row) for row in zip(*board)]
    return board

# --- Solver for uniqueness check ---

def find_empty(grid):
    for i in range(len(grid)):
        for j in range(len(grid)):
            if grid[i][j] == 0:
                return i, j
    return None

def is_valid(grid, row, col, num, n=3):
    N = n * n
    # row and column
    if any(grid[row][x] == num for x in range(N)): return False
    if any(grid[x][col] == num for x in range(N)): return False
    # block
    br, bc = (row // n) * n, (col // n) * n
    for r in range(br, br + n):
        for c in range(bc, bc + n):
            if grid[r][c] == num:
                return False
    return True

# Backtracking solver that counts solutions (stop after >1)

def solve(grid, count=0, n=3):
    empty = find_empty(grid)
    if not empty:
        return count + 1  # found a solution
    row, col = empty
    for num in range(1, n*n + 1):
        if is_valid(grid, row, col, num, n):
            grid[row][col] = num
            count = solve(grid, count, n)
            if count > 1:
                break  # more than one solution
            grid[row][col] = 0
    grid[row][col] = 0
    return count

# --- Generator ---

def generate_sudoku(n=3, removals=40):
    """Generate a Sudoku puzzle with a unique solution."""
    base = build_base(n)
    full = randomize(base, n)
    puzzle = [row[:] for row in full]
    N = n * n
    positions = [(r, c) for r in range(N) for c in range(N)]
    random.shuffle(positions)
    removed = 0
    for r, c in positions:
        if removed >= removals:
            break
        temp = puzzle[r][c]
        puzzle[r][c] = 0
        # check uniqueness
        if solve([row[:] for row in puzzle], n=n) != 1:
            puzzle[r][c] = temp
        else:
            removed += 1
    return puzzle, full

# Example: generate a 9×9 puzzle
puzzle, solution = generate_sudoku(n=3, removals=45)
print("Puzzle:\n")
for row in puzzle:
    print(row)
print("\nSolution:\n")
for row in solution:
    print(row)

# %%
has_unique_solution(np.array(puzzle))
# %%
