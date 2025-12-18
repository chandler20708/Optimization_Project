#%%
import os
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from numpy.random import default_rng

def generate_sudoku():
    rng = default_rng()
    rows = np.r_[rng.permutation([0,1,2]), rng.permutation([3,4,5]), rng.permutation([6,7,8])]
    cols = np.r_[rng.permutation([0,1,2]), rng.permutation([3,4,5]), rng.permutation([6,7,8])]
    nums = rng.permutation(np.arange(1,10))

    R = rows.reshape(9,1)
    C = cols.reshape(1,9)
    return nums[(3*(R % 3) + R//3 + C) % 9]

# --- NEW: top-level wrapper function (picklable) ---
def _generate_sudoku_worker(_):
    return generate_sudoku()

def generate_many(n):
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        # no lambda, use a top-level function instead
        return list(ex.map(_generate_sudoku_worker, range(n), chunksize=500))

def _is_valid(grid):
    # Rows
    for row in grid:
        vals = row[row > 0]
        if len(vals) != len(set(vals)):
            return False

    # Columns
    for col in grid.T:
        vals = col[col > 0]
        if len(vals) != len(set(vals)):
            return False

    # Boxes
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            box = grid[br:br+3, bc:bc+3].flatten()
            vals = box[box > 0]
            if len(vals) != len(set(vals)):
                return False
    return True

if __name__ == "__main__":
    sudokus = generate_many(1_000_000)
    # optional: quick sanity check
    print(len(sudokus), "grids generated")
    
# %%
import time
import os
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

# --- IMPORTANT for Python 3.14 on macOS ---
# Use spawn explicitly to match default behaviour, stable results.
ctx = mp.get_context("spawn")

# Top-level worker (must be picklable)
def noop(_):
    return None

def measure_overhead(chunksize, repeats=5):
    # Exactly 10 chunks
    N = chunksize * 10
    xs = range(N)

    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()

        # Explicit mp_context is REQUIRED for Python 3.14
        with ProcessPoolExecutor(
            max_workers=os.cpu_count(),
            mp_context=ctx
        ) as ex:
            list(ex.map(noop, xs, chunksize=chunksize))

        times.append(time.perf_counter() - t0)

    return sum(times) / len(times)

def estimate_t_o(chunksize=1000):
    T = measure_overhead(chunksize)
    M = 10  # always exactly 10 chunks
    return T / M

if __name__ == "__main__":
    print("Python 3.14 overhead benchmark\n")
    k_list = []
    t_o_list = []
    for k in [10, 12, 50, 52, 70, 100, 120, 150, 500, 800, 1000, 2500, 5000]:
        t_o = estimate_t_o(k)
        k_list.append(k)
        t_o_list.append(t_o*1e6)
        print(f"chunksize={k:5d}:   per-chunk overhead = {t_o*1e6:8.2f} µs")
# %%
import numpy as np

k = np.array(k_list, dtype=float)
t = np.array(t_o_list, dtype=float)

X = np.column_stack([np.ones_like(k), k, k**2])
coeff = np.linalg.lstsq(X, t, rcond=None)[0]

a, b, c = coeff
print("a =", a)
print("b =", b)
print("c =", c)

# %%
