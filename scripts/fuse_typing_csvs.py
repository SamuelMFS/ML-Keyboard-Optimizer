#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import json
import os
import sys
from typing import List, Dict, Any

# Increase field size limit for large JSON payloads
csv.field_size_limit(sys.maxsize)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fuse typing CSVs (concatenate typing_data arrays)")
    p.add_argument("--out", required=True, help="Output CSV path")
    p.add_argument("--json-col", default="typing_data", help="Column name with JSON array")
    p.add_argument("inputs", nargs="+", help="Input CSV files")
    return p.parse_args()


def read_records(path: str, json_col: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_recs: List[Dict[str, Any]] = []
        for row in reader:
            cell = row.get(json_col)
            if not cell:
                continue
            try:
                arr = json.loads(cell)
                if isinstance(arr, list):
                    all_recs.extend(arr)
            except Exception:
                continue
    return all_recs


def main() -> None:
    args = parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fused: List[Dict[str, Any]] = []
    for p in args.inputs:
        fused.extend(read_records(p, args.json_col))
    payload = json.dumps(fused, ensure_ascii=False)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[args.json_col])
        writer.writeheader()
        writer.writerow({args.json_col: payload})
    print(f"Fused {len(fused)} records from {len(args.inputs)} files into {args.out}")


if __name__ == "__main__":
    main()
