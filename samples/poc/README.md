<!-- AUTH:DEVNEUROSIM:7A3F9E2B | samples/poc/README.md -->
# POC (pure-Python, no machine dependencies)

These are lightweight toy problems demonstrating the "Stable Baselines" evolution loop:

1. Initialize population
2. Evaluate fitness
3. Select parents
4. Breed (variation: crossover + mutation)
5. Replace (form next generation)
6. Best solution extraction

Implemented as `BaseAlgorithm` subclasses:
- `onemax.py`: binary genome maximizing number of ones
- `regression_linear.py`: toy linear regression via GA on an 8-bit encoded parameter

