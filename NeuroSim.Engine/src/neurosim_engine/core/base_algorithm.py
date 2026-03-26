# AUTH:DEVNEUROSIM:7A3F9E2B | NeuroSim.Engine/src/neurosim_engine/core/base_algorithm.py
"""Abstract evolution cycle: initialize → evaluate → select → vary → replace."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar

P = TypeVar("P")  # population type
I = TypeVar("I")  # individual / genome type


class BaseAlgorithm(ABC):
    """Stable-Baselines–style hook: subclasses implement problem-specific pieces."""

    def __init__(
        self,
        *,
        population_size: int,
        max_generations: int,
        rng: Any | None = None,
    ) -> None:
        self.population_size = population_size
        self.max_generations = max_generations
        self._rng = rng

    # --- lifecycle ---

    def run(self) -> I:
        pop = self.initialize()
        pop = self.evaluate(pop)
        gen = 0
        while gen < self.max_generations and not self._should_stop():
            parents = self.select(pop)
            offspring = self.breed(parents)
            offspring = self.evaluate(offspring)
            pop = self.replace(pop, offspring)
            gen += 1
        return self.best_solution(pop)

    @abstractmethod
    def initialize(self) -> P:
        ...

    @abstractmethod
    def evaluate(self, population: P) -> P:
        ...

    @abstractmethod
    def select(self, population: P) -> P:
        ...

    @abstractmethod
    def breed(self, parents: P) -> P:
        ...

    @abstractmethod
    def replace(self, population: P, offspring: P) -> P:
        ...

    @abstractmethod
    def best_solution(self, population: P) -> I:
        ...

    def _should_stop(self) -> bool:
        return False
