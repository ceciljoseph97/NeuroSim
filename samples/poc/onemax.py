# AUTH:DEVNEUROSIM:7A3F9E2B | samples/poc/onemax.py
"""
POC: OneMax (binary GA) maximizing the number of ones.

Pure-Python, no external deps.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Sequence, Tuple

if __package__ is None or __package__ == "":
    # Allow `python samples/poc/onemax.py` execution without installing a package.
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # .../NeuroSim
    from samples.poc._base_import import import_base_algorithm  # type: ignore
else:
    from ._base_import import import_base_algorithm

BaseAlgorithm = import_base_algorithm()


@dataclass(frozen=True)
class Individual:
    genome: Tuple[int, ...]  # tuple of 0/1
    fitness: float


class OneMaxGA(BaseAlgorithm):
    def __init__(
        self,
        *,
        bit_length: int = 64,
        population_size: int = 50,
        max_generations: int = 200,
        tournament_size: int = 3,
        mutation_prob: float | None = None,
        crossover_prob: float = 0.9,
        elitism: int = 1,
        rng: random.Random | None = None,
        target_fitness: float | None = None,
    ) -> None:
        if rng is None:
            rng = random.Random()
        super().__init__(
            population_size=population_size,
            max_generations=max_generations,
            rng=rng,
        )

        self.bit_length = bit_length
        self.tournament_size = tournament_size
        self.mutation_prob = mutation_prob if mutation_prob is not None else 1.0 / max(1, bit_length)
        self.crossover_prob = crossover_prob
        self.elitism = max(0, elitism)
        self.target_fitness = target_fitness if target_fitness is not None else float(bit_length)
        self._last_best_fitness: float = float("-inf")

    def _rand_bit(self) -> int:
        return 1 if self._rng.random() < 0.5 else 0

    def initialize(self) -> List[Individual]:
        return [self._new_random_individual() for _ in range(self.population_size)]

    def _new_random_individual(self) -> Individual:
        genome = tuple(self._rand_bit() for _ in range(self.bit_length))
        # fitness computed in evaluate()
        return Individual(genome=genome, fitness=0.0)

    def evaluate(self, population: List[Individual]) -> List[Individual]:
        evaluated: List[Individual] = []
        for ind in population:
            fitness = float(sum(ind.genome))
            evaluated.append(Individual(genome=ind.genome, fitness=fitness))
        self._last_best_fitness = max(ind.fitness for ind in evaluated)
        return evaluated

    def select(self, population: List[Individual]) -> List[Individual]:
        # Tournament selection: repeat k times to build a parent pool.
        parents: List[Individual] = []
        for _ in range(self.population_size):
            contenders = self._rng.sample(population, k=min(self.tournament_size, len(population)))
            parents.append(max(contenders, key=lambda x: x.fitness))
        return parents

    def breed(self, parents: Sequence[Individual]) -> List[Individual]:
        # Create offspring population_size using crossover + mutation.
        offspring: List[Individual] = []
        while len(offspring) < self.population_size:
            p1 = parents[self._rng.randrange(len(parents))]
            p2 = parents[self._rng.randrange(len(parents))]

            if self._rng.random() < self.crossover_prob:
                c1, c2 = self._single_point_crossover(p1.genome, p2.genome)
            else:
                c1, c2 = p1.genome, p2.genome

            c1 = self._bit_flip_mutation(c1)
            c2 = self._bit_flip_mutation(c2)

            offspring.append(Individual(genome=c1, fitness=0.0))
            if len(offspring) < self.population_size:
                offspring.append(Individual(genome=c2, fitness=0.0))
        return offspring

    def _single_point_crossover(self, a: Tuple[int, ...], b: Tuple[int, ...]) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
        if self.bit_length <= 1:
            return a, b
        cut = self._rng.randrange(1, self.bit_length)  # [1..n-1]
        c1 = a[:cut] + b[cut:]
        c2 = b[:cut] + a[cut:]
        return c1, c2

    def _bit_flip_mutation(self, genome: Tuple[int, ...]) -> Tuple[int, ...]:
        g = list(genome)
        for i in range(len(g)):
            if self._rng.random() < self.mutation_prob:
                g[i] = 1 - g[i]
        return tuple(g)

    def replace(self, population: List[Individual], offspring: List[Individual]) -> List[Individual]:
        # Elitist replacement: keep top `elitism`, fill rest from best of offspring.
        # Assumes offspring already evaluated by BaseAlgorithm.run().
        if self.elitism == 0:
            return sorted(offspring, key=lambda x: x.fitness, reverse=True)[: self.population_size]

        combined = population + offspring
        combined_sorted = sorted(combined, key=lambda x: x.fitness, reverse=True)
        return combined_sorted[: self.population_size]

    def best_solution(self, population: List[Individual]) -> Individual:
        return max(population, key=lambda x: x.fitness)

    def _should_stop(self) -> bool:
        return self._last_best_fitness >= self.target_fitness


def main() -> None:
    rng = random.Random(0)
    ga = OneMaxGA(bit_length=64, population_size=60, max_generations=250, rng=rng, elitism=2)
    best = ga.run()
    print(f"Onemax: best_fitness={best.fitness} / {ga.bit_length}")
    # Print genome in compact form
    genome_str = "".join(str(b) for b in best.genome)
    print(f"genome={genome_str}")


if __name__ == "__main__":
    main()

