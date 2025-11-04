from __future__ import annotations
from typing import List, Tuple, Callable
import random
from copy import deepcopy
from .layout import CANONICAL_47

Individual = List[str]


def init_population(pop_size: int, seed: int | None = None, permutable_indices: List[int] | None = None) -> List[Individual]:
	"""Initialize population.
	
	If permutable_indices is provided, only those indices will be shuffled.
	Other indices will remain fixed at their CANONICAL_47 positions.
	"""
	if seed is not None:
		random.seed(seed)
	base = CANONICAL_47.copy()
	population: List[Individual] = []
	for _ in range(pop_size):
		cand = base.copy()
		if permutable_indices is not None:
			# Only shuffle permutable indices
			permutable_values = [cand[i] for i in permutable_indices]
			random.shuffle(permutable_values)
			for idx, val in zip(permutable_indices, permutable_values):
				cand[idx] = val
		else:
			# Shuffle all
			random.shuffle(cand)
		population.append(cand)
	return population


def tournament_select(pop: List[Individual], fitnesses: List[float], k: int = 3) -> Individual:
	idxs = random.sample(range(len(pop)), k)
	best = max(idxs, key=lambda i: fitnesses[i])
	return deepcopy(pop[best])


def ox_crossover(parent1: Individual, parent2: Individual, permutable_indices: List[int] | None = None) -> Tuple[Individual, Individual]:
	"""Order Crossover (OX) that preserves permutation validity without repair.
	
	If permutable_indices is provided, only those indices will be crossed over.
	Other indices will remain fixed from parent1.
	"""
	n = len(parent1)
	
	if permutable_indices is not None:
		# Only crossover permutable indices
		# Create mapping from permutable indices to their values
		p1_perm = [parent1[i] for i in permutable_indices]
		p2_perm = [parent2[i] for i in permutable_indices]
		
		# Perform OX on permutable values only
		perm_n = len(p1_perm)
		if perm_n < 2:
			return parent1.copy(), parent2.copy()
		c1, c2 = sorted(random.sample(range(perm_n), 2))
		
		def make_child_perm(p_a: List[str], p_b: List[str]) -> List[str]:
			child: List[str] = [None] * perm_n  # type: ignore
			child[c1:c2] = p_a[c1:c2]
			b_idx = c2
			fill_idx = c2
			used = set(child[c1:c2])
			while None in child:  # type: ignore
				gene = p_b[b_idx % perm_n]
				if gene not in used:
					child[fill_idx % perm_n] = gene  # type: ignore
					fill_idx += 1
					used.add(gene)
				b_idx += 1
			return child  # type: ignore
		
		o1_perm = make_child_perm(p1_perm, p2_perm)
		o2_perm = make_child_perm(p2_perm, p1_perm)
		
		# Reconstruct full individuals
		o1 = parent1.copy()
		o2 = parent2.copy()
		for idx, val in zip(permutable_indices, o1_perm):
			o1[idx] = val
		for idx, val in zip(permutable_indices, o2_perm):
			o2[idx] = val
		
		return o1, o2
	else:
		# Original behavior: crossover all indices
		c1, c2 = sorted(random.sample(range(n), 2))

		def make_child(p_a: Individual, p_b: Individual) -> Individual:
			child: List[str] = [None] * n  # type: ignore
			# Copy slice from p_a
			child[c1:c2] = p_a[c1:c2]
			# Fill remaining positions from p_b in order, skipping already present
			b_idx = c2
			fill_idx = c2
			used = set(child[c1:c2])
			while None in child:  # type: ignore
				gene = p_b[b_idx % n]
				if gene not in used:
					child[fill_idx % n] = gene  # type: ignore
					fill_idx += 1
					used.add(gene)
				b_idx += 1
			return child  # type: ignore

		o1 = make_child(parent1, parent2)
		o2 = make_child(parent2, parent1)
		return o1, o2


def swap_mutation(ind: Individual, rate: float, permutable_indices: List[int] | None = None) -> None:
	"""Swap mutation.
	
	If permutable_indices is provided, only swaps between those indices are allowed.
	"""
	if random.random() < rate:
		if permutable_indices is not None and len(permutable_indices) >= 2:
			i, j = random.sample(permutable_indices, 2)
		else:
			i, j = random.sample(range(len(ind)), 2)
		ind[i], ind[j] = ind[j], ind[i]


def evolve(
	population: List[Individual],
	fitness_fn: Callable[[Individual], float],
	generations: int = 300,
	mutation_rate: float = 0.1,
	crossover_rate: float = 0.7,
	elitism: int = 5,
	permutable_indices: List[int] | None = None,
) -> Tuple[Individual, List[float]]:
	best_fitnesses: List[float] = []
	for _ in range(generations):
		fitnesses = [fitness_fn(ind) for ind in population]
		# Elitism
		elite_idx = sorted(range(len(population)), key=lambda i: fitnesses[i], reverse=True)[:elitism]
		elites = [deepcopy(population[i]) for i in elite_idx]
		best_fitnesses.append(max(fitnesses))

		# Reproduction
		new_pop: List[Individual] = elites
		while len(new_pop) < len(population):
			p1 = tournament_select(population, fitnesses)
			p2 = tournament_select(population, fitnesses)
			if random.random() < crossover_rate:
				o1, o2 = ox_crossover(p1, p2, permutable_indices)
			else:
				o1, o2 = p1, p2
			swap_mutation(o1, mutation_rate, permutable_indices)
			swap_mutation(o2, mutation_rate, permutable_indices)
			new_pop.append(o1)
			if len(new_pop) < len(population):
				new_pop.append(o2)

		population = new_pop

	fitnesses = [fitness_fn(ind) for ind in population]
	best_idx = max(range(len(population)), key=lambda i: fitnesses[i])
	return population[best_idx], best_fitnesses
