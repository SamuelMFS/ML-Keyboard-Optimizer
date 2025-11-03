from __future__ import annotations
from typing import Dict, Iterable, Tuple, List, Any
import json
import pandas as pd
import csv
import sys
import os

# Increase field size limit for large JSON payloads
csv.field_size_limit(sys.maxsize)

TimingDicts = Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]


def _safe_mean(values: Iterable[float]) -> float:
	vals = list(values)
	return sum(vals) / len(vals) if vals else 0.0


def parse_typing_csv(csv_path: str, json_column: str = "typing_data") -> TimingDicts:
	"""Parse CSV where each row's `json_column` is a JSON array of timing records.

	Returns (avg_unigram, avg_bigram, avg_trigram) mapping physical key sequences to ms.
	Trigram dict may be empty if not present.
	"""
	df = pd.read_csv(csv_path)
	unigram_times: Dict[str, list] = {}
	bigram_times: Dict[str, list] = {}
	trigram_times: Dict[str, list] = {}

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
			lts = rec.get("letterTimings", [])
			total = rec.get("totalSequenceTime")

			# If total time absent, approximate as sum of letter timings
			if total is None:
				try:
					total = sum(float(x.get("reactionTime", 0.0)) for x in lts)
				except Exception:
					total = 0.0

			if len(seq) == 1:
				unigram_times.setdefault(seq, []).append(float(total))
			elif len(seq) == 2:
				bigram_times.setdefault(seq, []).append(float(total))
			elif len(seq) == 3:
				trigram_times.setdefault(seq, []).append(float(total))

	avg_uni = {k: _safe_mean(v) for k, v in unigram_times.items()}
	avg_bi = {k: _safe_mean(v) for k, v in bigram_times.items()}
	avg_tri = {k: _safe_mean(v) for k, v in trigram_times.items()}
	return avg_uni, avg_bi, avg_tri


def merge_typing_csvs(csv_path1: str, csv_path2: str, json_column: str = "typing_data") -> str:
	"""Merge two typing CSVs by concatenating their JSON arrays.
	
	Returns path to a temporary merged CSV file.
	"""
	records: List[Dict[str, Any]] = []
	
	# Read both CSVs
	for path in [csv_path1, csv_path2]:
		if not os.path.exists(path):
			continue
		try:
			df = pd.read_csv(path)
			for _, row in df.iterrows():
				cell = row.get(json_column)
				if pd.isna(cell):
					continue
				try:
					arr = json.loads(cell)
					if isinstance(arr, list):
						records.extend(arr)
				except Exception:
					continue
		except Exception:
			continue
	
	# Write merged CSV to temp file
	import tempfile
	temp_fd, temp_path = tempfile.mkstemp(suffix='.csv', prefix='merged_typing_', text=True)
	os.close(temp_fd)
	
	payload = json.dumps(records, ensure_ascii=False)
	with open(temp_path, "w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=[json_column])
		writer.writeheader()
		writer.writerow({json_column: payload})
	
	return temp_path



