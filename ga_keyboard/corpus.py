from __future__ import annotations
from typing import Dict, Tuple
from collections import Counter


def _normalize_text(text: str) -> str:
	# Lowercase; leave symbols as-is (we expect only the 47-key set to be used)
	return text.lower()


def count_ngrams(corpus_path: str, allowed_chars: str) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int]]:
	"""Count uni/bi/tri-gram frequencies filtered to allowed characters only."""
	with open(corpus_path, "r", encoding="utf-8", errors="ignore") as f:
		text = _normalize_text(f.read())

	allowed = set(allowed_chars)
	filtered = [ch for ch in text if ch in allowed]

	uni = Counter(filtered)
	bi = Counter(''.join(filtered[i:i+2]) for i in range(len(filtered)-1))
	tri = Counter(''.join(filtered[i:i+3]) for i in range(len(filtered)-2))

	return dict(uni), dict(bi), dict(tri)



