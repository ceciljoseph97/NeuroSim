# AUTH:DEVNEUROSIM:7A3F9E2B | samples/poc/regression_linear.py
"""
POC: Simple linear regression y ~= w * x. Sample Work only , Please update logic, structure implementations as per your observations and requirements.
POC: GA-based simple linear regression y ~= w * x.

Genome:
  - 8-bit binary encoding of an integer [0..255]
  - decoded to w in [w_min, w_max]

Fitness (maximize):
  - fitness = 1 / (1 + MSE)

"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Sequence, Tuple

if __package__ is None or __package__ == "":
    # Allow `python samples/poc/regression_linear.py` execution without installing a package.
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


class RegressionLinearGA(BaseAlgorithm):
    def __init__(
        self,
        *,
        genome_bits: int = 8,
        population_size: int = 80,
        max_generations: int = 250,
        tournament_size: int = 3,
        mutation_prob: float | None = None,
        crossover_prob: float = 0.9,
        elitism: int = 2,
        rng: random.Random | None = None,
        # regression target
        x_points: Sequence[float] | None = None,
        true_w: float = 1.75,
        noise_std: float = 0.0,
        # search space
        w_min: float = -2.0,
        w_max: float = 4.0,
        target_mse: float = 1e-5,
    ) -> None:
        if rng is None:
            rng = random.Random()
        super().__init__(
            population_size=population_size,
            max_generations=max_generations,
            rng=rng,
        )

        self.genome_bits = genome_bits
        self.tournament_size = tournament_size
        self.mutation_prob = mutation_prob if mutation_prob is not None else 1.0 / max(1, genome_bits)
        self.crossover_prob = crossover_prob
        self.elitism = max(0, elitism)

        self.w_min = w_min
        self.w_max = w_max
        self.target_mse = target_mse

        if x_points is None:
            # Deterministic x grid; keep things platform-agnostic.
            self.xs = [(-1.0 + 2.0 * i / 19.0) for i in range(20)]
        else:
            self.xs = list(x_points)

        # Generate y with optional noise.
        r = self._rng
        self.ys = []
        for x in self.xs:
            eps = r.gauss(0.0, noise_std) if noise_std != 0.0 else 0.0
            self.ys.append(true_w * x + eps)

        self._last_best_mse: float = float("inf")

    def _new_random_individual(self) -> Individual:
        genome = tuple(1 if self._rng.random() < 0.5 else 0 for _ in range(self.genome_bits))
        return Individual(genome=genome, fitness=0.0)

    def initialize(self) -> List[Individual]:
        return [self._new_random_individual() for _ in range(self.population_size)]

    def _decode_w(self, genome: Tuple[int, ...]) -> float:
        # Interpret genome as big-endian bitstring.
        v = 0
        for b in genome:
            v = (v << 1) | int(b)
        max_int = (1 << self.genome_bits) - 1
        # Map integer to [w_min, w_max]
        return self.w_min + (v / max_int) * (self.w_max - self.w_min)

    def _mse_for_w(self, w: float) -> float:
        sse = 0.0
        for x, y in zip(self.xs, self.ys):
            err = (y - w * x)
            sse += err * err
        return sse / max(1, len(self.xs))

    def evaluate(self, population: List[Individual]) -> List[Individual]:
        evaluated: List[Individual] = []
        best_mse = float("inf")
        for ind in population:
            w = self._decode_w(ind.genome)
            mse = self._mse_for_w(w)
            fitness = 1.0 / (1.0 + mse)
            evaluated.append(Individual(genome=ind.genome, fitness=fitness))
            if mse < best_mse:
                best_mse = mse
        self._last_best_mse = best_mse
        return evaluated

    def select(self, population: List[Individual]) -> List[Individual]:
        parents: List[Individual] = []
        for _ in range(self.population_size):
            contenders = self._rng.sample(population, k=min(self.tournament_size, len(population)))
            parents.append(max(contenders, key=lambda x: x.fitness))
        return parents

    def breed(self, parents: Sequence[Individual]) -> List[Individual]:
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
        if self.genome_bits <= 1:
            return a, b
        cut = self._rng.randrange(1, self.genome_bits)
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
        combined = population + offspring
        combined_sorted = sorted(combined, key=lambda x: x.fitness, reverse=True)
        return combined_sorted[: self.population_size]

    def best_solution(self, population: List[Individual]) -> Individual:
        return max(population, key=lambda x: x.fitness)

    def _should_stop(self) -> bool:
        return self._last_best_mse <= self.target_mse


def main() -> None:
    rng = random.Random(0)
    ga = RegressionLinearGA(
        genome_bits=8,
        population_size=120,
        max_generations=300,
        rng=rng,
        true_w=1.75,
        noise_std=0.0,
        w_min=-2.0,
        w_max=4.0,
        target_mse=1e-6,
        elitism=2,
    )

    best = ga.run()
    w_hat = ga._decode_w(best.genome)
    mse = ga._mse_for_w(w_hat)
    genome_str = "".join(str(b) for b in best.genome)

    print(f"regression_linear: w_hat={w_hat:.6f}, mse={mse:.6e}, genome={genome_str}")


if __name__ == "__main__":
    main()

