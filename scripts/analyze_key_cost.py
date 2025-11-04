#!/usr/bin/env python3
"""
Script to analyze individual key costs and all bigram combinations involving a specific key.

Usage:
    python scripts/analyze_key_cost.py \
        --csv data/typing_test.csv \
        --csv-json-col typing_data \
        --key a \
        --out outputs/key_cost_analysis_a.png

    # With typing_test.csv merge:
    python scripts/analyze_key_cost.py \
        --csv data/other_data.csv \
        --key e \
        --mix-with-typing-test \
        --out outputs/key_cost_analysis_e.png
"""

from __future__ import annotations
import argparse
import json
import csv
import sys
import os
import pandas as pd
from typing import Dict, List, Tuple
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

# Increase field size limit for large JSON payloads
csv.field_size_limit(sys.maxsize)

# Add parent directory to path to import ga_keyboard
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from ga_keyboard.layout import CANONICAL_47
from ga_keyboard.typing_data import merge_typing_csvs


def _safe_mean(values: List[float]) -> float:
	"""Compute mean of values, returning 0 if empty."""
	if not values:
		return 0.0
	return sum(values) / len(values)


def parse_typing_csv(csv_path: str, json_column: str = "typing_data") -> Tuple[Dict[str, float], Dict[str, float], Dict[str, Tuple[float, float]]]:
	"""Parse CSV and extract unigram and bigram timings.
	
	Returns:
		- avg_uni: dict mapping unigram to average time
		- avg_bi: dict mapping bigram to average total time
		- avg_bi_letter_times: dict mapping bigram to (avg_time_key1, avg_time_key2)
	"""
	df = pd.read_csv(csv_path)
	unigram_times: Dict[str, List[float]] = defaultdict(list)
	bigram_times: Dict[str, List[float]] = defaultdict(list)
	bigram_letter_times: Dict[str, List[Tuple[float, float]]] = defaultdict(list)

	for _, row in df.iterrows():
		cell = row.get(json_column)
		if pd.isna(cell):
			continue
			
		try:
			records = json.loads(cell)
		except Exception:
			continue

		if not isinstance(records, list):
			continue

		for rec in records:
			seq = str(rec.get("sequence", ""))
			total = rec.get("totalSequenceTime")
			lts = rec.get("letterTimings", [])

			if total is None:
				try:
					total = sum(float(x.get("reactionTime", 0.0)) for x in lts)
				except Exception:
					total = 0.0

			if len(seq) == 1:
				unigram_times[seq].append(float(total))
			elif len(seq) == 2:
				bigram_times[seq].append(float(total))
				# Extract individual letter timings
				if len(lts) >= 2:
					try:
						time1 = float(lts[0].get("reactionTime", 0.0))
						time2 = float(lts[1].get("reactionTime", 0.0))
						bigram_letter_times[seq].append((time1, time2))
					except Exception:
						pass

	avg_uni = {k: _safe_mean(v) for k, v in unigram_times.items()}
	avg_bi = {k: _safe_mean(v) for k, v in bigram_times.items()}
	
	# Average letter timings for each bigram
	avg_bi_letter_times: Dict[str, Tuple[float, float]] = {}
	for k, times_list in bigram_letter_times.items():
		if times_list:
			avg_time1 = _safe_mean([t[0] for t in times_list])
			avg_time2 = _safe_mean([t[1] for t in times_list])
			avg_bi_letter_times[k] = (avg_time1, avg_time2)
	
	return avg_uni, avg_bi, avg_bi_letter_times


def collect_key_combinations(key: str, avg_uni: Dict[str, float], avg_bi: Dict[str, float], 
                             avg_bi_letter_times: Dict[str, Tuple[float, float]]) -> List[Tuple[str, float, str, Tuple[float, float] | None]]:
	"""
	Collect all timing data for a specific key.
	Returns list of (label, total_time, type, letter_times) tuples where:
		- label: display label
		- total_time: total time for unigram or bigram
		- type: 'uni' or 'bi'
		- letter_times: for bigrams, (time_key1, time_key2), else None
	"""
	results: List[Tuple[str, float, str, Tuple[float, float] | None]] = []
	
	# Unigram: the key by itself
	if key in avg_uni:
		results.append((f"{key} (unigrama)", avg_uni[key], "uni", None))
	
	# Bigrams: all combinations involving this key
	# Format: "key_other" and "other_key"
	for other in CANONICAL_47:
		# Combination: key + other
		combo1 = f"{key}{other}"
		if combo1 in avg_bi:
			letter_times = avg_bi_letter_times.get(combo1, None)
			results.append((f"{key}+{other}", avg_bi[combo1], "bi", letter_times))
		
		# Combination: other + key
		combo2 = f"{other}{key}"
		if combo2 in avg_bi:
			letter_times = avg_bi_letter_times.get(combo2, None)
			results.append((f"{other}+{key}", avg_bi[combo2], "bi", letter_times))
	
	# Sort by time (ascending)
	results.sort(key=lambda x: x[1])
	return results


def plot_key_cost_analysis(key: str, data: List[Tuple[str, float, str, Tuple[float, float] | None]], out_path: str) -> None:
	"""Generate bar chart showing key costs with individual letter contributions for bigrams."""
	if not data:
		print(f"Warning: No data found for key '{key}'")
		return
	
	# Separate unigrams and bigrams
	unigrams = [d for d in data if d[2] == 'uni']
	bigrams = [d for d in data if d[2] == 'bi']
	
	# Create figure with subplots if we have both types
	# Increase height for better readability: more space per item
	fig_height = max(12, (len(unigrams) + len(bigrams)) * 0.35)
	fig, ax = plt.subplots(figsize=(16, fig_height))
	
	# Prepare data for grouped bars
	all_labels = []
	all_times_total = []
	all_times_key1 = []
	all_times_key2 = []
	all_types = []
	all_has_letter_times = []
	
	# Process unigrams
	for label, total_time, typ, _ in unigrams:
		all_labels.append(label)
		all_times_total.append(total_time)
		all_times_key1.append(None)
		all_times_key2.append(None)
		all_types.append(typ)
		all_has_letter_times.append(False)
	
	# Process bigrams
	for label, total_time, typ, letter_times in bigrams:
		all_labels.append(label)
		all_times_total.append(total_time)
		if letter_times is not None:
			all_times_key1.append(letter_times[0])
			all_times_key2.append(letter_times[1])
			all_has_letter_times.append(True)
		else:
			all_times_key1.append(None)
			all_times_key2.append(None)
			all_has_letter_times.append(False)
		all_types.append(typ)
	
	# Create horizontal bar chart
	y_pos = np.arange(len(all_labels))
	bar_height = 0.28  # Height for each bar group (increased for better spacing)
	
	# Plot bars for each category
	has_first_uni = False
	has_first_bi_total = False
	has_first_bi_key1 = False
	has_first_bi_key2 = False
	
	for i, (label, total, key1_time, key2_time, typ, has_letter_times) in enumerate(
		zip(all_labels, all_times_total, all_times_key1, all_times_key2, all_types, all_has_letter_times)
	):
		if typ == 'uni':
			# Unigram: single centered bar
			bar = ax.barh(i, total, height=bar_height * 2.5, color='#1f77b4', alpha=0.7, 
			              label='Unigrama' if not has_first_uni else '')
			has_first_uni = True
			# Add value label
			ax.text(total + max(all_times_total) * 0.01, i,
			        f'{total:.1f} ms', ha='left', va='center', fontsize=7)
		else:
			# Bigram: three bars stacked vertically
			# Total bar (top)
			bar_total = ax.barh(i - bar_height, total, height=bar_height, 
			                   color='#ff7f0e', alpha=0.7, 
			                   label='Bigrama Total' if not has_first_bi_total else '')
			has_first_bi_total = True
			ax.text(total + max(all_times_total) * 0.01, i - bar_height,
			        f'{total:.1f} ms', ha='left', va='center', fontsize=7, fontweight='bold')
			
			# Individual key bars if available
			if has_letter_times and key1_time is not None and key2_time is not None:
				# Tecla 1 (middle)
				bar_key1 = ax.barh(i, key1_time, height=bar_height, 
				                  color='#2ca02c', alpha=0.6, 
				                  label='Tecla 1 (dentro do bigrama)' if not has_first_bi_key1 else '')
				has_first_bi_key1 = True
				ax.text(key1_time + max(all_times_total) * 0.01, i,
				        f'{key1_time:.1f} ms', ha='left', va='center', fontsize=6, style='italic')
				
				# Tecla 2 (bottom)
				bar_key2 = ax.barh(i + bar_height, key2_time, height=bar_height, 
				                  color='#d62728', alpha=0.6, 
				                  label='Tecla 2 (dentro do bigrama)' if not has_first_bi_key2 else '')
				has_first_bi_key2 = True
				ax.text(key2_time + max(all_times_total) * 0.01, i + bar_height,
				        f'{key2_time:.1f} ms', ha='left', va='center', fontsize=6, style='italic')
	
	# Labels
	ax.set_yticks(y_pos)
	ax.set_yticklabels(all_labels, fontsize=8)
	ax.set_xlabel('Tempo (ms)', fontsize=12, fontweight='bold')
	ax.set_title(f'Análise de Custo: Tecla "{key}"\nUnigrama vs. Todas as Combinações Bigrâmicas (com Contribuições Individuais)', 
	             fontsize=14, fontweight='bold', pad=20)
	
	# Legend
	from matplotlib.patches import Patch
	legend_elements = [
		Patch(facecolor='#1f77b4', alpha=0.7, label='Unigrama'),
		Patch(facecolor='#ff7f0e', alpha=0.7, label='Bigrama Total'),
		Patch(facecolor='#2ca02c', alpha=0.6, label='Tecla 1 (dentro do bigrama)'),
		Patch(facecolor='#d62728', alpha=0.6, label='Tecla 2 (dentro do bigrama)')
	]
	ax.legend(handles=legend_elements, loc='lower right', fontsize=9)
	
	# Grid
	ax.grid(axis='x', alpha=0.3, linestyle='--')
	ax.set_axisbelow(True)
	
	plt.tight_layout()
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	plt.savefig(out_path, dpi=150, bbox_inches='tight')
	plt.close()
	print(f"Gráfico salvo em: {out_path}")


def parse_args() -> argparse.Namespace:
	p = argparse.ArgumentParser(description="Analyze key cost and all bigram combinations for a specific key")
	p.add_argument("--csv", required=True, help="Path to CSV file with typing data")
	p.add_argument("--csv-json-col", default="typing_data", help="Column name with JSON timing array")
	p.add_argument("--key", required=True, help="Key to analyze (must be one of the 46 canonical keys)")
	p.add_argument("--mix-with-typing-test", action="store_true", help="Merge with typing_test.csv before processing")
	p.add_argument("--out", required=True, help="Output path for the bar chart PNG")
	return p.parse_args()


def main() -> None:
	args = parse_args()
	
	# Validate key
	if args.key not in CANONICAL_47:
		print(f"Erro: A tecla '{args.key}' não está entre as 46 teclas canônicas.")
		print(f"Teclas válidas: {', '.join(CANONICAL_47)}")
		sys.exit(1)
	
	# Merge with typing_test.csv if flag is set
	csv_to_use = args.csv
	temp_merged_path = None
	if args.mix_with_typing_test:
		typing_test_path = os.path.join(os.path.dirname(args.csv), "typing_test.csv")
		if not os.path.exists(typing_test_path):
			# Try in data directory
			typing_test_path = os.path.join(parent_dir, "data", "typing_test.csv")
		if os.path.exists(typing_test_path):
			print(f"Misturando com typing_test.csv…")
			temp_merged_path = merge_typing_csvs(args.csv, typing_test_path, args.csv_json_col)
			csv_to_use = temp_merged_path
			print(f"Dados de digitação mesclados prontos")
		else:
			print(f"Aviso: typing_test.csv não encontrado em {typing_test_path}, pulando mesclagem")
	
	print(f"Carregando dados de digitação de {csv_to_use}...")
	avg_uni, avg_bi, avg_bi_letter_times = parse_typing_csv(csv_to_use, args.csv_json_col)
	print(f"Timings encontrados: {len(avg_uni)} unigramas, {len(avg_bi)} bigramas")
	print(f"Timings individuais de teclas dentro de bigramas: {len(avg_bi_letter_times)} bigramas")
	
	print(f"Coletando combinações envolvendo a tecla '{args.key}'...")
	data = collect_key_combinations(args.key, avg_uni, avg_bi, avg_bi_letter_times)
	print(f"Encontradas {len(data)} combinações (1 unigrama + {len(data)-1} bigramas)")
	
	if not data:
		print(f"Erro: Nenhum dado encontrado para a tecla '{args.key}'")
		sys.exit(1)
	
	print(f"Gerando gráfico...")
	plot_key_cost_analysis(args.key, data, args.out)
	
	# Print summary statistics
	uni_times = [d[1] for d in data if d[2] == 'uni']
	bi_times = [d[1] for d in data if d[2] == 'bi']
	
	if uni_times:
		print(f"\nEstatísticas:")
		print(f"  Unigrama: {uni_times[0]:.2f} ms")
	if bi_times:
		print(f"  Bigramas: min={min(bi_times):.2f} ms, max={max(bi_times):.2f} ms, média={sum(bi_times)/len(bi_times):.2f} ms")
	
	# Cleanup temporary merged file if created
	if temp_merged_path and os.path.exists(temp_merged_path):
		try:
			os.remove(temp_merged_path)
		except Exception:
			pass


if __name__ == "__main__":
	main()

