from __future__ import annotations
from typing import Dict, List, Tuple
import os
import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from .layout import CANONICAL_47, KEY_ROWS, format_layout_ascii

TimingDicts = Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]


def per_key_cost_approx(
	layout: List[str],
	freq_uni: Dict[str, int],
	freq_bi: Dict[str, int],
	freq_tri: Dict[str, int],
	timings: TimingDicts,
	use_trigrams: bool,
) -> Dict[str, float]:
	"""Approximate per-physical-key cost by distributing n-gram costs equally among involved keys."""
	avg_uni, avg_bi, avg_tri = timings
	logical_to_physical = {layout[i]: CANONICAL_47[i] for i in range(len(layout))}
	key_cost: Dict[str, float] = {k: 0.0 for k in CANONICAL_47}

	for l, cnt in freq_uni.items():
		p = logical_to_physical.get(l)
		t = avg_uni.get(p, 0.0)
		key_cost[p] = key_cost.get(p, 0.0) + cnt * t

	for bg, cnt in freq_bi.items():
		if len(bg) != 2:
			continue
		p1 = logical_to_physical.get(bg[0])
		p2 = logical_to_physical.get(bg[1])
		t = avg_bi.get(f"{p1}{p2}")
		if t is None:
			# fallback equally
			t = (avg_uni.get(p1, 0.0) + avg_uni.get(p2, 0.0))
		share = cnt * t / 2.0
		key_cost[p1] = key_cost.get(p1, 0.0) + share
		key_cost[p2] = key_cost.get(p2, 0.0) + share

	if use_trigrams:
		for tg, cnt in freq_tri.items():
			if len(tg) != 3:
				continue
			p = [logical_to_physical.get(tg[i]) for i in range(3)]
			t = avg_tri.get(f"{p[0]}{p[1]}{p[2]}")
			if t is None:
				t = sum(avg_uni.get(x, 0.0) for x in p)
			share = cnt * t / 3.0
			for x in p:
				key_cost[x] = key_cost.get(x, 0.0) + share

	return key_cost


def plot_heatmap(layout: List[str], key_cost: Dict[str, float], out_path: str) -> None:
	# Build ragged grid per row, then pad with NaNs to rectangular shape
	grid: List[List[float]] = []
	for indices in KEY_ROWS:
		row_vals = []
		for idx in indices:
			k = CANONICAL_47[idx]
			row_vals.append(key_cost.get(k, 0.0))
		grid.append(row_vals)
	# Pad rows to max length
	max_len = max(len(r) for r in grid) if grid else 0
	padded = [r + [float('nan')] * (max_len - len(r)) for r in grid]
	arr = np.array(padded, dtype=float)
	plt.figure(figsize=(10, 4))
	sns.heatmap(arr, annot=False, cmap="viridis")
	plt.title("Per-key cost (approx)")
	plt.tight_layout()
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	plt.savefig(out_path)
	plt.close()


def plot_fitness(fitnesses: List[float], out_path: str) -> None:
	plt.figure(figsize=(8, 4))
	plt.plot(fitnesses)
	plt.xlabel("Generation")
	plt.ylabel("Fitness")
	plt.title("Evolution of Fitness")
	plt.tight_layout()
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	plt.savefig(out_path)
	plt.close()


def ascii_sparkline(values: List[float], width: int = 60) -> str:
	if not values:
		return ""
	vals = values
	mn, mx = min(vals), max(vals)
	if mx - mn < 1e-12:
		return "▁" * min(width, len(vals))
	step = max(1, len(vals) // width)
	chars = "▁▂▃▄▅▆▇█"
	out = []
	for i in range(0, len(vals), step):
		v = vals[i]
		norm = (v - mn) / (mx - mn)
		idx = min(len(chars) - 1, int(round(norm * (len(chars) - 1))))
		out.append(chars[idx])
	return ''.join(out)


def ascii_layout(layout: List[str]) -> str:
	return format_layout_ascii(layout)



