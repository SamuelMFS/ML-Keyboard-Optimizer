from __future__ import annotations
from typing import Dict, List, Tuple
from .layout import CANONICAL_47, layout_to_mapping

TimingDicts = Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]


def _pair(a: str, b: str) -> str:
	return f"{a}{b}"


def _triple(a: str, b: str, c: str) -> str:
	return f"{a}{b}{c}"


def compute_cost(
	layout: List[str],
	freq_uni: Dict[str, int],
	freq_bi: Dict[str, int],
	freq_tri: Dict[str, int],
	timings: TimingDicts,
	use_trigrams: bool = False,
	fallback_to_unigrams: bool = True,
	cost_order: str = "bi",  # one of: "uni", "bi", "tri"
) -> float:
	"""Compute total typing time for the corpus given a candidate layout.

	cost_order selects which n-gram order to use exclusively to avoid double counting.
	If entries are missing at the chosen order and fallback_to_unigrams is True, back off additively to unigrams.
	"""
	avg_uni, avg_bi, avg_tri = timings
	logical_to_physical = layout_to_mapping(layout)

	cost = 0.0

	if cost_order == "uni":
		for logical_char, count in freq_uni.items():
			physical = logical_to_physical.get(logical_char)
			if physical is None:
				continue
			time = avg_uni.get(physical)
			if time is None:
				continue
			cost += count * time
		return float(cost)

	if cost_order == "bi":
		for bigram, count in freq_bi.items():
			if len(bigram) != 2:
				continue
			l1, l2 = bigram[0], bigram[1]
			p1, p2 = logical_to_physical.get(l1), logical_to_physical.get(l2)
			if p1 is None or p2 is None:
				continue
			key = _pair(p1, p2)
			time = avg_bi.get(key)
			if time is None and fallback_to_unigrams:
				time = (avg_uni.get(p1, 0.0) + avg_uni.get(p2, 0.0))
			if time is None:
				continue
			cost += count * time
		return float(cost)

	# cost_order == "tri"
	use_tri_here = use_trigrams or cost_order == "tri"
	if use_tri_here:
		for trigram, count in freq_tri.items():
			if len(trigram) != 3:
				continue
			l1, l2, l3 = trigram[0], trigram[1], trigram[2]
			p1 = logical_to_physical.get(l1)
			p2 = logical_to_physical.get(l2)
			p3 = logical_to_physical.get(l3)
			if p1 is None or p2 is None or p3 is None:
				continue
			key = _triple(p1, p2, p3)
			time = avg_tri.get(key)
			if time is None and fallback_to_unigrams:
				time = (avg_uni.get(p1, 0.0) + avg_uni.get(p2, 0.0) + avg_uni.get(p3, 0.0))
			if time is None:
				continue
			cost += count * time
	return float(cost)


def fitness_from_cost(cost: float) -> float:
	return 1.0 / cost if cost > 0.0 else 0.0



