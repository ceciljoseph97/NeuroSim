<!-- AUTH:DEVNEUROSIM:7A3F9E2B | NaturalCompute/docs/BIT_GA_PLAYGROUNDS_CONTRACT.md -->

# Bit-encoded GA playgrounds — Engine / UI contract (co-owned)

**Person 1 & Person 2** fill and freeze this document in **week 1**. It covers **two** problems: **linear regression (bits → w)** and **one simple combinatorial objective** (default **OneMax**) on the same `BinaryGenome` + `GeneticAlgorithm` stack.

### Role rotation (equal load)

| Phase | Problem | Person 1 leads | Person 2 leads |
|-------|---------|------------------|----------------|
| A | `regression_linear` | **API / modularity / tests** | **UI / design / wiring** |
| B | `onemax` | **UI / design / wiring** | **API / modularity / tests** |

Both review each other’s MRs and co-maintain this file.

---

## 1. Problem IDs

| `problem_id`          | Idea | Typical fitness (maximize) |
|-----------------------|------|----------------------------|
| `regression_linear`   | `y ≈ w·x`; bits decode to `w` in `[w_min, w_max]` | `1 / (1 + MSE)` |
| `onemax` *(default 2nd)* | Count of 1-bits (or sum of bits) | `sum(bits)` or agreed variant |

*Alternative second problem (only if both agree and update this table):* **target pattern** — fixed hidden bitstring `t`; fitness = Hamming matches with `t`.

---

## 2. Shared config (all problems)

Fields the UI exposes and the engine accepts (names are normative):

| Field | Type | Notes |
|-------|------|--------|
| `problem_id` | string | `regression_linear` \| `onemax` |
| `population_size` | int | ≥ 2 |
| `genome_length` | int | bits |
| `max_generations` | int | |
| `seed` | int | RNG for reproducibility |
| `parent_selection` | string | `tournament` \| `roulette` |
| `parent_tournament_size` | int | if tournament |
| `crossover_rate` | float | GA |
| `elite_count` | int | GA |

---

## 3. Problem-specific config

### `regression_linear`

| Field | Type |
|-------|------|
| `w_min`, `w_max` | float |
| `data_seed` | int *(optional; synthetic `(x,y)`)* |
| `n_points` | int *(optional)* |

### `onemax`

| Field | Type |
|-------|------|
| *(none required)* | — |

*(Add rows here if you switch to target-pattern: `target_bits`, etc.)*

---

## 4. Run result (producer → consumer)

Normative shape (dict or dataclass — pick one in code and mirror here):

- `problem_id`
- `seed`, `genome_length`, `population_size`, `generations_completed`
- `trace`: ordered list of `{ "generation": int, "best_fitness": float }`
- `best`: `{ "bitstring": str, "fitness": float, ... }`

**Problem-specific extensions under `best`:**

- `regression_linear`: `w` (float), `mse` (float), optional `w_true` for demo label
- `onemax`: `ones_count` (int) *(or equivalent)*

**Errors:** validation failures → structured message / exception type agreed here.

---

## 5. Callable surface

Document the **exact** import path and function signature after implementation, e.g.

`natural_compute....run_bit_ga_playground(config: dict) -> RunResult`

---

## 6. Parity checks

| Problem | Fixed config (seed, length, pop, …) | Compared metrics |
|---------|--------------------------------------|------------------|
| `regression_linear` | *(fill)* | `best.fitness`, `best.w`, `best.mse` |
| `onemax` | *(fill)* | `best.fitness`, `best.ones_count` |

CLI vs UI must match within agreed float tolerance.
