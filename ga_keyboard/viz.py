from __future__ import annotations
from typing import Dict, List, Tuple
import os
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
from .layout import CANONICAL_47, KEY_ROWS, format_layout_ascii

TimingDicts = Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]


def _create_cyan_cmap():
	"""Create a custom cyan colormap from light to dark."""
	colors = ['#E0F7FA', '#B2EBF2', '#80DEEA', '#4DD0E1', '#26C6DA', '#00BCD4', '#00ACC1', '#0097A7']
	return mcolors.LinearSegmentedColormap.from_list('cyan_gradient', colors, N=256)


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


def plot_unigram_timing_heatmap(timings: TimingDicts, out_path: str) -> None:
	"""Plot heatmap of average unigram timing per physical key."""
	avg_uni, _, _ = timings
	cyan_cmap = _create_cyan_cmap()
	
	# Build grid with unigram times per key
	grid: List[List[float]] = []
	for indices in KEY_ROWS:
		row_vals = []
		for idx in indices:
			k = CANONICAL_47[idx]
			time = avg_uni.get(k, float('nan'))
			row_vals.append(time)
		grid.append(row_vals)
	
	# Pad rows to max length
	max_len = max(len(r) for r in grid) if grid else 0
	padded = [r + [float('nan')] * (max_len - len(r)) for r in grid]
	arr = np.array(padded, dtype=float)
	
	plt.figure(figsize=(10, 4))
	# Format annotations: show values with 1 decimal place, use 'nan' for missing
	annot_arr = np.empty_like(arr, dtype=object)
	for i in range(arr.shape[0]):
		for j in range(arr.shape[1]):
			if np.isnan(arr[i, j]):
				annot_arr[i, j] = ''
			else:
				annot_arr[i, j] = f'{arr[i, j]:.1f}'
	
	sns.heatmap(arr, annot=annot_arr, fmt='', cmap=cyan_cmap, cbar_kws={'label': 'Time (ms)'},
	            annot_kws={'size': 8})
	plt.title("Average Unigram Timing per Key")
	plt.tight_layout()
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	plt.savefig(out_path)
	plt.close()


def plot_bigram_timing_heatmap(timings: TimingDicts, out_path: str) -> None:
	"""Plot heatmap of average bigram timing per physical key.
	
	For each key, computes the average of all bigrams where that key appears
	(either as first or second character).
	"""
	avg_uni, avg_bi, _ = timings
	cyan_cmap = _create_cyan_cmap()
	
	# For each physical key, collect all bigram timings where it appears
	key_bigram_times: Dict[str, List[float]] = {k: [] for k in CANONICAL_47}
	
	for bigram_key, time in avg_bi.items():
		if len(bigram_key) != 2:
			continue
		p1, p2 = bigram_key[0], bigram_key[1]
		if p1 in key_bigram_times:
			key_bigram_times[p1].append(time)
		if p2 in key_bigram_times:
			key_bigram_times[p2].append(time)
	
	# Compute average per key
	key_avg_bigram: Dict[str, float] = {}
	for k, times in key_bigram_times.items():
		if times:
			key_avg_bigram[k] = sum(times) / len(times)
		else:
			key_avg_bigram[k] = float('nan')
	
	# Build grid
	grid: List[List[float]] = []
	for indices in KEY_ROWS:
		row_vals = []
		for idx in indices:
			k = CANONICAL_47[idx]
			time = key_avg_bigram.get(k, float('nan'))
			row_vals.append(time)
		grid.append(row_vals)
	
	# Pad rows to max length
	max_len = max(len(r) for r in grid) if grid else 0
	padded = [r + [float('nan')] * (max_len - len(r)) for r in grid]
	arr = np.array(padded, dtype=float)
	
	plt.figure(figsize=(10, 4))
	# Format annotations: show values with 1 decimal place, use 'nan' for missing
	annot_arr = np.empty_like(arr, dtype=object)
	for i in range(arr.shape[0]):
		for j in range(arr.shape[1]):
			if np.isnan(arr[i, j]):
				annot_arr[i, j] = ''
			else:
				annot_arr[i, j] = f'{arr[i, j]:.1f}'
	
	sns.heatmap(arr, annot=annot_arr, fmt='', cmap=cyan_cmap, cbar_kws={'label': 'Time (ms)'},
	            annot_kws={'size': 8})
	plt.title("Average Bigram Timing per Key")
	plt.tight_layout()
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	plt.savefig(out_path)
	plt.close()



