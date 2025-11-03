from typing import List, Dict

# Canonical 46-key order (QWERTY-like) used as the reference positions
CANONICAL_47: List[str] = [
	"1","2","3","4","5","6","7","8","9","0","-","=",
	"q","w","e","r","t","y","u","i","o","p","[","]","\\",
	"a","s","d","f","g","h","j","k","l",";","'",
	"z","x","c","v","b","n","m",",",".","/",
]

DEFAULT_QWERTY_47: List[str] = CANONICAL_47.copy()

# Define row sizes explicitly to derive indices reliably
ROW_SIZES: List[int] = [12, 13, 11, 10]

# Build KEY_ROWS from ROW_SIZES
KEY_ROWS: List[List[int]] = []
_start = 0
for _size in ROW_SIZES:
	KEY_ROWS.append(list(range(_start, _start + _size)))
	_start += _size


def layout_to_mapping(layout: List[str]) -> Dict[str, str]:
	"""Map logical symbol -> physical key symbol used for timings.

	The mapping is defined by the position correspondence with CANONICAL_47.
	At index i, the candidate's symbol is assigned to the physical key symbol CANONICAL_47[i].
	Thus, to get the timing for a logical symbol L, look up physical = mapping[L].
	"""
	mapping: Dict[str, str] = {}
	for idx, logical_symbol in enumerate(layout):
		physical_key_symbol = CANONICAL_47[idx]
		mapping[logical_symbol] = physical_key_symbol
	return mapping


def format_layout_ascii(layout: List[str]) -> str:
	"""Return a staggered ASCII layout string for presentation."""
	lines: List[str] = []
	row_indents = [0, 1, 2, 3]
	for r, indices in enumerate(KEY_ROWS):
		indent = " " * row_indents[r]
		row_chars = [layout[i] for i in indices if i < len(layout)]
		lines.append(indent + " ".join(row_chars))
	return "\n".join(lines)


def layout_string(layout: List[str]) -> str:
	"""Compact layout string."""
	return "".join(layout)
