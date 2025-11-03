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


def parse_typing_csv(csv_path: str, json_column: str = "typing_data") -> Tuple[Dict[str, float], Dict[str, float]]:
	"""Parse CSV and extract unigram and bigram timings."""
	df = pd.read_csv(csv_path)
	unigram_times: Dict[str, List[float]] = defaultdict(list)
	bigram_times: Dict[str, List[float]] = defaultdict(list)

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

			if total is None:
				lts = rec.get("letterTimings", [])
				try:
					total = sum(float(x.get("reactionTime", 0.0)) for x in lts)
				except Exception:
					total = 0.0

			if len(seq) == 1:
				unigram_times[seq].append(float(total))
			elif len(seq) == 2:
				bigram_times[seq].append(float(total))

	avg_uni = {k: _safe_mean(v) for k, v in unigram_times.items()}
	avg_bi = {k: _safe_mean(v) for k, v in bigram_times.items()}
	return avg_uni, avg_bi


def collect_key_combinations(key: str, avg_uni: Dict[str, float], avg_bi: Dict[str, float]) -> List[Tuple[str, float, str]]:
	"""
	Collect all timing data for a specific key.
	Returns list of (label, time, type) tuples where type is 'uni' or 'bi'.
	"""
	results: List[Tuple[str, float, str]] = []
	
	# Unigram: the key by itself
	if key in avg_uni:
		results.append((f"{key} (unigrama)", avg_uni[key], "uni"))
	
	# Bigrams: all combinations involving this key
	# Format: "key_other" and "other_key"
	for other in CANONICAL_47:
		# Combination: key + other
		combo1 = f"{key}{other}"
		if combo1 in avg_bi:
			results.append((f"{key}+{other}", avg_bi[combo1], "bi"))
		
		# Combination: other + key
		combo2 = f"{other}{key}"
		if combo2 in avg_bi:
			results.append((f"{other}+{key}", avg_bi[combo2], "bi"))
	
	# Sort by time (ascending)
	results.sort(key=lambda x: x[1])
	return results


def plot_key_cost_analysis(key: str, data: List[Tuple[str, float, str]], out_path: str) -> None:
	"""Generate bar chart showing key costs."""
	if not data:
		print(f"Warning: No data found for key '{key}'")
		return
	
	labels = [d[0] for d in data]
	times = [d[1] for d in data]
	types = [d[2] for d in data]
	
	# Color coding: unigram in one color, bigrams in another
	colors = ['#1f77b4' if t == 'uni' else '#ff7f0e' for t in types]
	
	# Create figure
	fig, ax = plt.subplots(figsize=(14, max(8, len(data) * 0.15)))
	
	# Horizontal bar chart for better readability with many items
	y_pos = np.arange(len(labels))
	bars = ax.barh(y_pos, times, color=colors, alpha=0.7)
	
	# Labels
	ax.set_yticks(y_pos)
	ax.set_yticklabels(labels, fontsize=8)
	ax.set_xlabel('Tempo (ms)', fontsize=12, fontweight='bold')
	ax.set_title(f'Análise de Custo: Tecla "{key}"\nUnigrama vs. Todas as Combinações Bigrâmicas', 
	             fontsize=14, fontweight='bold', pad=20)
	
	# Add value labels on bars
	for i, (bar, time) in enumerate(zip(bars, times)):
		width = bar.get_width()
		ax.text(width + max(times) * 0.01, bar.get_y() + bar.get_height()/2,
		        f'{time:.1f} ms', ha='left', va='center', fontsize=7)
	
	# Legend
	from matplotlib.patches import Patch
	legend_elements = [
		Patch(facecolor='#1f77b4', alpha=0.7, label='Unigrama'),
		Patch(facecolor='#ff7f0e', alpha=0.7, label='Bigramas')
	]
	ax.legend(handles=legend_elements, loc='lower right')
	
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
	avg_uni, avg_bi = parse_typing_csv(csv_to_use, args.csv_json_col)
	print(f"Timings encontrados: {len(avg_uni)} unigramas, {len(avg_bi)} bigramas")
	
	print(f"Coletando combinações envolvendo a tecla '{args.key}'...")
	data = collect_key_combinations(args.key, avg_uni, avg_bi)
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

