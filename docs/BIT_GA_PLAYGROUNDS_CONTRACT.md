<!-- AUTH:DEVNEUROSIM:7A3F9E2B | NaturalCompute/docs/BIT_GA_PLAYGROUNDS_CONTRACT.md -->

# Bit-encoded GA playgrounds — Engine / UI contract (co-owned)

This contract is the “current implementation template” for the bit-encoded GA playgrounds.

It covers **two** problems on the same `BinaryGenome` + `BaseAlgorithm` stack:
- `regression_linear`: **bits -> w** then `fitness = 1/(1+MSE)`
- `onemax`: **bits -> ones_count** then `fitness = ones_count`

Both the **Concept Diagram phase flow** and the **config/operator semantics** must stay intact for the GA path.

## Phase Flow (Concept Diagram is required to remain intact)

![ConceptDiagram](../ConceptDiagram.png)

Milestone scope right now: implement the **GA** path in the phase flow:
- Initialize population
- Evaluate fitness (Warm up)
- Select parents/Individuals|Continue
- Breed (Variation = Selection + Crossover + Mutation)
- Replace (generational replacement with elitism)
- Stop by `max_generations` (and optionally `target_fitness`)
- out: Best Genome representation + Analysis on convergence, fitness scores.
- Snapshot analysis

Placeholders for ES/EP/GP can exist in UI/CLI selection [*Hold*], but the GA operators/config must be correct [*Current*].

### Role rotation (equal load)

| Phase | Problem | Person 1 leads | Person 2 leads |
|-------|---------|------------------|----------------|
| A | `regression_linear` | **API / modularity / tests** | **UI / design / wiring** |
| B | `onemax` | **UI / design / wiring** | **API / modularity / tests** |

Both review each other’s tasks and co-maintain this file.

---

## Sapmle Req [Can change - Discuss and report within 1 week]: 1. Paradigm Select + Environment (Genome Config)

UI/CLI must expose a single config payload that can be passed to:
- engine runner (pure function or class)
- CLI runner
- UI runner

### 1.1 Paradigm (select)

Required config fields (names are normative):
- `paradigm`: `GA` (required for this milestone; other values can exist but must not break config parsing)

### 1.2 Genome paradigm (select)

Required config fields:
- `genome_paradigm`: `binary` (required for this milestone)
- `genome_length`: `int` (bitstring length, L)

### 1.3 Bit encoding (binary genome)

Binary genome is a fixed-length vector of bits:
- `bit[i]` is either `0` or `1`
- representation is position-based; decode rules below define interpretation

For decode, use **big-endian** bit order unless/until we change it:
- integer value `v = sum(bit[i] * 2^(L-1-i))`
- map `v` to parameter ranges (only needed for `regression_linear`)

---

## 2. Problem IDs (normative)

| `problem_id`          | Idea | Typical fitness (maximize) |
|-----------------------|------|----------------------------|
| `regression_linear`   | `y ≈ w·x`; bits decode to `w` in `[w_min, w_max]` | `1 / (1 + MSE)` |
| `onemax` *(default 2nd)* | Count of 1-bits (or sum of bits) | `sum(bits)` or agreed variant |

*Alternative second problem (only if both agree and update this table):* **target pattern** — fixed hidden bitstring `t`; fitness = Hamming matches with `t`.

---

## 3. Shared Config (all problems; UI <-> Engine contract)

Fields the UI exposes and the engine accepts (names are normative). These match the semantics of the Legacy `EvolutionConfig`:

| Field | Type | Notes |
|-------|------|--------|
| `problem_id` | string | `regression_linear` \| `onemax` |
| `population_size` | int | ≥ 2 |
| `genome_length` | int | bits (L) |
| `max_generations` | int | termination hard stop |
| `seed` | int | RNG for reproducibility |
| `elite_count` | int | number of elites carried to next generation (GA) |
| `target_fitness` | float | optional; if set and best fitness >= this, stop early |
| `parent_selection` | string | `tournament` (required for milestone) \| `roulette` \| `rank` |
| `parent_tournament_size` | int | required if `parent_selection=tournament` (k) |
| `crossover_rate` | float | GA crossover application probability |
| `crossover_type` | string | `single_point` \| `two_point` \| `uniform` |
| `mutation_rate` | float | bit-flip probability per bit |
| `mutation_type` | string | `flip_bit` (required for milestone) |

---

## 4. Problem-specific config

### 4.1 `regression_linear` (bits -> w -> MSE)

Required fields:
- `w_min`: float
- `w_max`: float

Optional fields:
- `data_seed`: int (default deterministic synthetic data)
- `n_points`: int (default fixed small value; keep stable across CLI/UI)
- `noise_std`: float (default 0.0 for determinism)

Decoding and evaluation requirements:
- decode genome -> integer `v in [0..2^L-1]` using big-endian bits
- decode `w = w_min + (v/(2^L-1))*(w_max-w_min)`
- generate (x,y) pairs deterministically from `data_seed` and `n_points`
- compute `mse = mean((y - w*x)^2)`
- `fitness = 1 / (1 + mse)` (maximize)

The run result must include:
- `best.w` (decoded from best bitstring)
- `best.mse`

### 4.2 `onemax` (bits -> ones_count)

Required semantics:
- `ones_count = sum(bits)`
- `fitness = ones_count` (maximize)

The run result must include:
- `best.ones_count`

---

## 5. Engine Operator Modules that must be implemented (NeuroSim.Engine core)

The NeuroSim.Engine Python core currently only has `BaseAlgorithm`.
This milestone requires implementing the **GA operator modules** under:
- `NeuroSim/NeuroSim.Engine/src/neurosim_engine/core/`

Use Legacy C# semantics as the reference design:
- Legacy selection/crossover/mutation are separate interfaces
- GAEngine does: **Selection (2 parents) -> Crossover if random < crossover_rate -> Mutation -> Evaluate offspring -> Replace with elitism**

### 5.1 Selection module

Required operator(s):
- `TournamentSelection(k)` where `k = parent_tournament_size`

Semantics (must match Legacy):
- pick `count` parents by repeating:
  - sample k individuals uniformly from population
  - choose the individual with maximum fitness

### 5.2 Crossover module

Required operator(s) for `binary` genomes:
- `SinglePointCrossover`
- `TwoPointCrossover`
- `UniformCrossover`

Semantics (must match Legacy):
- single-point: swap suffix after a random cut in `[1..L-1]`
- two-point: swap between random cut pair `a < b` where `a in [1..L-2]`, `b in [a+1..L-1]`
- uniform: for each bit position independently, swap with probability 0.5

### 5.3 Mutation module

Required operator:
- `FlipBitMutation`

Semantics (must match Legacy):
- for each bit independently, flip it with probability `mutation_rate`

### 5.4 Recombination / Variation module (Selection + Crossover + Mutation)

Define a variation step that produces offspring pairs:
- draw 2 parents via Selection
- if RNG < `crossover_rate`, produce 2 children via crossover
- else clone both parents into children
- mutate both children via Mutation

This is the **Variation** block in the phase flow diagram.

### 5.5 Replace module (elitism, generational replacement)

Required semantics:
- carry `elite_count` best individuals into next generation
- fill remaining slots by evaluated offspring

Fitness evaluation happens before replace:
- offsprings must have fitness computed before selecting elites/replacements.

---

## 6. CLI contract (must match UI config names)

CLI must be deterministic with `seed`.

Required interface (contract; implement whatever runner name you pick, but keep schema):
- input: config object matching sections `3` and `4`
- output: `RunResult` JSON with run schema from section 7

Required behaviors:
- validate config (missing `w_min/w_max` for regression -> hard error)
- honor `max_generations`
- honor optional `target_fitness`
- print final best solution and trace (trace can be truncated if needed, but keep the schema)

---

## 7. UI contract (Wiring + Results)

UI must:
- let user select `problem_id` (`onemax` or `regression_linear`)
- show binary genome config:
  - `genome_length` (L)
  - seed
- show GA operator config:
  - `parent_selection` + `parent_tournament_size`
  - `crossover_type` + `crossover_rate`
  - `mutation_type` + `mutation_rate`
  - `elite_count`
- run GA and produce the run result:
  - trace ordered by generation
  - `best` includes decoded fields (`w`+`mse` or `ones_count`)

The phase flow visualization should remain consistent with the Concept Diagram:
- GA path must show Selection -> Variation -> Evaluate Offspring -> Selection for Next Generation.

---

## 8. Run result schema (producer -> consumer; normative)

Normative shape (dict or dataclass — pick one in code and mirror here):

- `problem_id`
- `seed`, `genome_length`, `population_size`, `generations_completed`
- `trace`: ordered list of `{ "generation": int, "best_fitness": float, "mean_fitness": float? }`
- `best`: `{ "bitstring": str, "fitness": float, ... }`

Problem-specific extensions under `best`:
- `regression_linear`: `w` (float), `mse` (float)
- `onemax`: `ones_count` (int)

Errors:
- validation failures must return structured message / agreed exception type.

---

## 9. Callable surface (after implementation)

Document the exact import path and function signature:
- engine entrypoint (CLI + UI call this)
- e.g. `NeuroSim...run_bit_ga_playground(config: dict) -> RunResult`

---

## 10. Acceptance / Parity checks

| Problem | Fixed config (seed, length, pop, …) | Compared metrics |
|---------|--------------------------------------|------------------|
| `regression_linear` | *(fill)* | `best.fitness`, `best.w`, `best.mse` |
| `onemax` | *(fill)* | `best.fitness`, `best.ones_count` |

CLI vs UI must match within agreed float tolerance for `regression_linear`.


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

`NeuroSim...run_bit_ga_playground(config: dict) -> RunResult`

---

## 6. Parity checks

| Problem | Fixed config (seed, length, pop, …) | Compared metrics |
|---------|--------------------------------------|------------------|
| `regression_linear` | *(fill)* | `best.fitness`, `best.w`, `best.mse` |
| `onemax` | *(fill)* | `best.fitness`, `best.ones_count` |

CLI vs UI must match within agreed float tolerance.
