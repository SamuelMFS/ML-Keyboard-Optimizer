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
    distance_penalty: float,
    same_row_penalty: float,
    diff_row_penalty: float,
    repeat_same_key_penalty: float,
    noise_std: float,
    seed: int | None,
) -> List[Dict]:
    if seed is not None:
        random.seed(seed)

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
        
        # Base times by row (home row is fastest)
        # Row 0 (numbers): worst
        # Row 1 (top alpha): second worst
        # Row 2 (home row): best
        # Row 3 (bottom): second worst (worse than top)
        if r == 2:  # Home row
            base = row_base_ms_home
        elif r == 1:  # Top row (above home)
            base = row_base_ms_top
        elif r == 3:  # Bottom row (below home)
            base = row_base_ms_bottom
        else:  # Row 0 (numbers)
            base = row_base_ms_numbers
        
        # Penalty based on distance from F and J (home row center keys)
        # F is at index 28 (row 2, col 3 within home row)
        # J is at index 31 (row 2, col 6 within home row)
        home_row = 2
        f_col_in_home = 3  # Position of F within home row (0-indexed: a=0, s=1, d=2, f=3)
        j_col_in_home = 6  # Position of J within home row (h=5, j=6, k=7)
        
        # Calculate current key's column within its row
        col_in_row = col_index_within_row(idx)
        
        # Account for row staggering: home row is offset by ~1.5 keys
        # Top row (row 1) starts ~1.5 keys to the left
        # Bottom row (row 3) starts ~2.5 keys to the left
        row_offset = {0: 0.0, 1: -1.5, 2: 0.0, 3: -2.5}.get(r, 0.0)
        adjusted_col = col_in_row + row_offset
        
        # Calculate 2D Euclidean distance from F and J
        # Vertical distance: difference in rows (each row = 1 unit)
        # Horizontal distance: difference in adjusted columns
        vertical_dist_f = abs(r - home_row)
        horizontal_dist_f = abs(adjusted_col - f_col_in_home)
        dist_to_f = (vertical_dist_f ** 2 + horizontal_dist_f ** 2) ** 0.5
        
        vertical_dist_j = abs(r - home_row)
        horizontal_dist_j = abs(adjusted_col - j_col_in_home)
        dist_to_j = (vertical_dist_j ** 2 + horizontal_dist_j ** 2) ** 0.5
        
        # Use minimum distance (closest to either F or J)
        min_dist = min(dist_to_f, dist_to_j)
        
        # Penalty per unit distance (more distance = slower)
        # Use quadratic penalty for distances > 2.0 to model pinky finger difficulty
        if min_dist > 2.0:
            # Quadratic penalty for distant keys (pinky finger territory)
            distance_penalty_value = (2.0 * distance_penalty) + ((min_dist - 2.0) ** 2) * distance_penalty * 1.5
        else:
            # Linear penalty for closer keys
            distance_penalty_value = min_dist * distance_penalty
        
        # Additional penalty for extreme edges (pinky finger positions)
        # Keys at the very edges (first or last 2 positions in a row) are harder
        row_size = ROW_SIZES[r]
        if col_in_row < 2 or col_in_row >= row_size - 2:
            edge_penalty = 15.0  # Extra penalty for edge keys where pinky is used
            distance_penalty_value += edge_penalty
        
        val = base + distance_penalty_value
        return max(60.0, val)  # clamp to sensible minimum

    def bigram_time_ms(i1: int, i2: int) -> float:
        t = unigram_time_ms(i1) + unigram_time_ms(i2)
        if i1 == i2:
            t += repeat_same_key_penalty
        else:
            r1, r2 = ROW_OF_INDEX[i1], ROW_OF_INDEX[i2]
            t += same_row_penalty if r1 == r2 else diff_row_penalty
            
            # Calculate positions of both keys
            col1 = col_index_within_row(i1)
            col2 = col_index_within_row(i2)
            
            # Account for row staggering
            row_offset1 = {0: 0.0, 1: -1.5, 2: 0.0, 3: -2.5}.get(r1, 0.0)
            row_offset2 = {0: 0.0, 1: -1.5, 2: 0.0, 3: -2.5}.get(r2, 0.0)
            
            adjusted_col1 = col1 + row_offset1
            adjusted_col2 = col2 + row_offset2
            
            # Calculate 2D Euclidean distance between keys
            vertical_dist = abs(r1 - r2)
            horizontal_dist = abs(adjusted_col1 - adjusted_col2)
            key_distance = (vertical_dist ** 2 + horizontal_dist ** 2) ** 0.5
            
            # Apply distance penalty (keys farther apart are slower)
            distance_penalty_between_keys = key_distance * distance_penalty
            t += distance_penalty_between_keys
            
            # Additional realistic patterns for bigrams
            
            # 1. Same-hand vs cross-hand penalty
            # Approximate: left hand is roughly cols 0-5, right hand is roughly cols 6+
            # But this varies by row, so use a rough center point
            home_row_center = 5.5  # Rough center of home row (between f and j)
            is_left_hand1 = adjusted_col1 < home_row_center
            is_left_hand2 = adjusted_col2 < home_row_center
            
            if is_left_hand1 == is_left_hand2:
                # Same hand - add penalty for awkward same-hand transitions
                same_hand_penalty = 30.0 * (key_distance / 3.0)  # More penalty for distant same-hand
                t += same_hand_penalty
            else:
                # Cross-hand - generally faster, but add small base penalty
                cross_hand_penalty = 4.0
                t += cross_hand_penalty
            
            # 2. Direction-based penalties (vertical movement)
            if r1 != r2:
                # Moving up (lower row number) can be slightly different
                if r2 < r1:  # Moving up
                    vertical_penalty = abs(r1 - r2) * 6.0
                else:  # Moving down
                    vertical_penalty = abs(r1 - r2) * 7.5  # Slightly worse
                t += vertical_penalty
            
            # 3. Lateral movement penalty (horizontal distance)
            if abs(adjusted_col1 - adjusted_col2) > 2.5:
                # Large lateral movement is awkward
                lateral_penalty = (abs(adjusted_col1 - adjusted_col2) - 2.5) * 4.5
                t += lateral_penalty
            
            # 4. Complex diagonal movements (both vertical and horizontal)
            if vertical_dist > 0 and horizontal_dist > 1.5:
                diagonal_penalty = (vertical_dist * horizontal_dist) / 1.5
                t += diagonal_penalty
            
            # 5. Add some non-linear variation to break flatness
            # Use a pseudo-random hash based on key indices for consistent variation
            hash_val = ((i1 * 17 + i2 * 23) % 100) / 100.0
            variation = (hash_val - 0.5) * 22.0  # ±11ms variation
            t += variation
        
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
    p.add_argument("--row-base-numbers", type=float, default=220.0, help="Base time for numbers row (worst)")
    p.add_argument("--row-base-top", type=float, default=170.0, help="Base time for top alpha row (above home)")
    p.add_argument("--row-base-home", type=float, default=140.0, help="Base time for home row (best)")
    p.add_argument("--row-base-bottom", type=float, default=200.0, help="Base time for bottom row (worse than top)")
    p.add_argument("--distance-penalty", type=float, default=4.0, help="Penalty per unit distance from F/J keys (higher = more penalty for distance, default 4.0 for better pinky modeling)")
    p.add_argument("--col-penalty", type=float, default=None, help="[Deprecated] Use --distance-penalty instead")
    p.add_argument("--same-row-penalty", type=float, default=12.0)
    p.add_argument("--diff-row-penalty", type=float, default=6.0)
    p.add_argument("--repeat-penalty", type=float, default=35.0)
    p.add_argument("--noise-std", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=1234)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    
    # Handle compatibility: if col_penalty is provided, use it; otherwise use distance_penalty
    distance_penalty = args.distance_penalty if args.col_penalty is None else args.col_penalty
    if args.col_penalty is not None:
        print("Aviso: --col-penalty está deprecated. Use --distance-penalty em vez disso.")
    
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    records = build_records(
        args.row_base_numbers,
        args.row_base_top,
        args.row_base_home,
        args.row_base_bottom,
        distance_penalty,  # col_penalty_per_step parameter (not used anymore, kept for compatibility)
        distance_penalty,  # distance_penalty parameter
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
