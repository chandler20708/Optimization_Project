#%%
import random
import copy
from typing import List, Tuple, Optional
import numpy as np
from numpy.random import default_rng
from sudoku_templates import TEMPLATES

_rng = default_rng()

def shuffled(s):
	return _rng.permutation(s)

def _pattern(r, c):
	return (3*(r % 3) + r//3 + c) % 9

def _generate_sudoku():
	"""Generate full solved sudoku"""
	# Shuffle rows/cols in groups of 3
	rows  = np.r_[shuffled([0,1,2]), shuffled([3,4,5]), shuffled([6,7,8])]
	cols  = np.r_[shuffled([0,1,2]), shuffled([3,4,5]), shuffled([6,7,8])]
	nums  = shuffled(np.arange(1,10))  # permute the digits 1–9

	# Build grid using pattern
	grid = np.zeros((9,9), dtype=int)
	for i, r in enumerate(rows):
		for j, c in enumerate(cols):
			grid[i, j] = nums[_pattern(r, c)]
	return grid

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
