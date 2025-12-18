#%%
import random
import copy
from typing import List, Tuple, Optional
import numpy as np
from numpy.random import default_rng
from sudoku_templates import TEMPLATES

_rng = default_rng()

from concurrent.futures import ThreadPoolExecutor
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

def generate_many(n):
    with ThreadPoolExecutor() as ex:
        return list(ex.map(lambda _: generate_sudoku(), range(n)))


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


s = _generate_sudoku()
s
# %%
_is_valid(s)

	
# %%
