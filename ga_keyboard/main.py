from __future__ import annotations
import argparse
import os
from typing import List
from tqdm import tqdm

from .layout import CANONICAL_47, DEFAULT_QWERTY_47, format_layout_ascii, layout_string
from .typing_data import parse_typing_csv
from .corpus import count_ngrams
from .fitness import compute_cost, fitness_from_cost
from .ga import init_population, evolve
from .viz import per_key_cost_approx, plot_heatmap, plot_fitness, ascii_sparkline, ascii_layout


def parse_args() -> argparse.Namespace:
	p = argparse.ArgumentParser(description="GA Keyboard Layout Optimizer")
	p.add_argument("--csv", required=True, help="Path to typing CSV file")
	p.add_argument("--csv-json-col", default="typing_data", help="Column name with JSON timing array")
	p.add_argument("--corpus", required=True, help="Path to text corpus file")
	p.add_argument("--generations", type=int, default=300)
	p.add_argument("--population", type=int, default=200)
	p.add_argument("--mutation-rate", type=float, default=0.1)
	p.add_argument("--crossover-rate", type=float, default=0.7)
	p.add_argument("--elitism", type=int, default=5)
	p.add_argument("--use-trigrams", type=str, default="false", help="true/false")
	p.add_argument("--cost-order", type=str, default="bi", choices=["uni","bi","tri"], help="Which n-gram order to use exclusively for cost")
	p.add_argument("--fallback-to-unigrams", type=str, default="false", help="true/false: back off missing higher-order timings to unigrams")
	p.add_argument("--seed", type=int, default=42)
	p.add_argument("--outdir", default="/home/xamu/dev/ML/outputs")
	return p.parse_args()


def main() -> None:
	args = parse_args()
	use_trigrams = str(args.use_trigrams).lower() in {"1","true","yes","y"}
	fallback_to_unigrams = str(args.fallback_to_unigrams).lower() in {"1","true","yes","y"}
	os.makedirs(args.outdir, exist_ok=True)

	print("Loading typing data…")
	avg_uni, avg_bi, avg_tri = parse_typing_csv(args.csv, args.csv_json_col)
	print(f"Timings: uni={len(avg_uni)} bi={len(avg_bi)} tri={len(avg_tri)}")

	print("Counting corpus n-grams…")
	allowed = ''.join(CANONICAL_47)
	freq_uni, freq_bi, freq_tri = count_ngrams(args.corpus, allowed)
	print(f"Frequencies: uni={len(freq_uni)} bi={len(freq_bi)} tri={len(freq_tri)}")

	print("Initializing population…")
	population = init_population(args.population, seed=args.seed)

	def fitness_fn(ind: List[str]) -> float:
		cost = compute_cost(
			ind, freq_uni, freq_bi, freq_tri, (avg_uni, avg_bi, avg_tri),
			use_trigrams=use_trigrams, cost_order=args.cost_order, fallback_to_unigrams=fallback_to_unigrams
		)
		return fitness_from_cost(cost)

	print("Evolving…")
	best, fitnesses = evolve(
		population,
		fitness_fn,
		generations=args.generations,
		mutation_rate=args.mutation_rate,
		crossover_rate=args.crossover_rate,
		elitism=args.elitism,
	)

	# Evaluate best
	best_cost = compute_cost(
		best, freq_uni, freq_bi, freq_tri, (avg_uni, avg_bi, avg_tri),
		use_trigrams=use_trigrams, cost_order=args.cost_order, fallback_to_unigrams=fallback_to_unigrams
	)
	best_fit = fitness_from_cost(best_cost)

	# Baseline: QWERTY
	baseline_cost = compute_cost(
		DEFAULT_QWERTY_47, freq_uni, freq_bi, freq_tri, (avg_uni, avg_bi, avg_tri),
		use_trigrams=use_trigrams, cost_order=args.cost_order, fallback_to_unigrams=fallback_to_unigrams
	)
	improvement = 100.0 * (baseline_cost - best_cost) / baseline_cost if baseline_cost > 0 else 0.0

	print("\nBest layout (string):")
	print(layout_string(best))
	print("\nBest layout (ASCII):")
	print(format_layout_ascii(best))
	print(f"\nBest cost: {best_cost:.2f} ms, fitness: {best_fit:.6f}")
	print(f"Baseline (QWERTY) cost: {baseline_cost:.2f} ms")
	print(f"Improvement over QWERTY: {improvement:.2f}%")

	# Outputs
	with open(os.path.join(args.outdir, "best_layout.txt"), "w", encoding="utf-8") as f:
		f.write(layout_string(best) + "\n\n")
		f.write(format_layout_ascii(best) + "\n")

	plot_fitness(fitnesses, os.path.join(args.outdir, "fitness.png"))
	print("\nFitness (ASCII sparkline):")
	print(ascii_sparkline(fitnesses))

	key_cost = per_key_cost_approx(best, freq_uni, freq_bi, freq_tri, (avg_uni, avg_bi, avg_tri), use_trigrams)
	plot_heatmap(best, key_cost, os.path.join(args.outdir, "heatmap.png"))
	print(f"\nSaved outputs to {args.outdir}")


if __name__ == "__main__":
	main()



