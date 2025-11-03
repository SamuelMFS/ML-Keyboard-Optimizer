#!/usr/bin/env python3
from __future__ import annotations
import json
import csv
import os
import argparse
import random
from typing import List, Dict

# Canonical 46-key order from the package (duplicated here to avoid imports during generation)
CANONICAL_46: List[str] = [
    "1","2","3","4","5","6","7","8","9","0","-","=",
    "q","w","e","r","t","y","u","i","o","p","[","]","\\",
    "a","s","d","f","g","h","j","k","l",";","'",
    "z","x","c","v","b","n","m",",",".","/",
]

# Row index mapping based on our layout grid (0..3)
ROW_SIZES = [12, 13, 11, 10]
KEY_ROWS: List[List[int]] = []
_start = 0
for _size in ROW_SIZES:
    KEY_ROWS.append(list(range(_start, _start + _size)))
    _start += _size

ROW_OF_INDEX: Dict[int, int] = {}
for r, idxs in enumerate(KEY_ROWS):
    for i in idxs:
        ROW_OF_INDEX[i] = r


def col_index_within_row(global_index: int) -> int:
    r = ROW_OF_INDEX[global_index]
    row_start = sum(ROW_SIZES[:r])
    return global_index - row_start


def row_center_col(row: int) -> float:
    size = ROW_SIZES[row]
    return (size - 1) / 2.0


def build_records(
    row_base_ms_numbers: float,
    row_base_ms_top: float,
    row_base_ms_home: float,
    row_base_ms_bottom: float,
    col_penalty_per_step: float,
    same_row_penalty: float,
    diff_row_penalty: float,
    repeat_same_key_penalty: float,
    noise_std: float,
    seed: int | None,
) -> List[Dict]:
    if seed is not None:
        random.seed(seed)
    row_base = {
        0: row_base_ms_numbers,
        1: row_base_ms_top,
        2: row_base_ms_home,
        3: row_base_ms_bottom,
    }

    def jitter(x: float) -> float:
        # Always add small uniform random jitter to break step patterns
        small_jitter = random.uniform(-0.15, 0.15)
        val = x + small_jitter
        # Add Gaussian noise if specified
        if noise_std > 0:
            val += random.gauss(0.0, noise_std)
        return val

    def unigram_time_ms(idx: int) -> float:
        r = ROW_OF_INDEX[idx]
        base = row_base[r]
        col = col_index_within_row(idx)
        center = row_center_col(r)
        lateral = abs(col - center) * col_penalty_per_step
        val = base + lateral
        return max(60.0, val)  # clamp to sensible minimum

    def bigram_time_ms(i1: int, i2: int) -> float:
        t = unigram_time_ms(i1) + unigram_time_ms(i2)
        if i1 == i2:
            t += repeat_same_key_penalty
        else:
            r1, r2 = ROW_OF_INDEX[i1], ROW_OF_INDEX[i2]
            t += same_row_penalty if r1 == r2 else diff_row_penalty
        return max(80.0, t)

    records: List[Dict] = []
    # Unigrams
    for i, sym in enumerate(CANONICAL_46):
        t = jitter(unigram_time_ms(i))
        rec = {
            "sequence": sym,
            "letterTimings": [{"letter": sym, "reactionTime": round(t, 2)}],
            "totalSequenceTime": round(t, 2),
        }
        records.append(rec)
    # Bigrams
    for i, a in enumerate(CANONICAL_46):
        for j, b in enumerate(CANONICAL_46):
            seq = f"{a}{b}"
            t = jitter(bigram_time_ms(i, j))
            rec = {
                "sequence": seq,
                "letterTimings": [
                    {"letter": a, "reactionTime": round(jitter(unigram_time_ms(i)), 2)},
                    {"letter": b, "reactionTime": round(jitter(unigram_time_ms(j)), 2)},
                ],
                "totalSequenceTime": round(t, 2),
            }
            records.append(rec)
    return records


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate synthetic typing CSV (full uni+bi)")
    p.add_argument("--out", default="/home/xamu/dev/ML/data/synthetic_typing_full_uni_bi.csv")
    p.add_argument("--row-base-numbers", type=float, default=220.0)
    p.add_argument("--row-base-top", type=float, default=170.0)
    p.add_argument("--row-base-home", type=float, default=140.0)
    p.add_argument("--row-base-bottom", type=float, default=180.0)
    p.add_argument("--col-penalty", type=float, default=1.5)
    p.add_argument("--same-row-penalty", type=float, default=12.0)
    p.add_argument("--diff-row-penalty", type=float, default=6.0)
    p.add_argument("--repeat-penalty", type=float, default=35.0)
    p.add_argument("--noise-std", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=1234)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    records = build_records(
        args.row_base_numbers,
        args.row_base_top,
        args.row_base_home,
        args.row_base_bottom,
        args.col_penalty,
        args.same_row_penalty,
        args.diff_row_penalty,
        args.repeat_penalty,
        args.noise_std,
        args.seed,
    )
    payload = json.dumps(records, ensure_ascii=False)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["typing_data"])
        writer.writeheader()
        writer.writerow({"typing_data": payload})
    print(f"Wrote {len(records)} records to {args.out}")


if __name__ == "__main__":
    main()
