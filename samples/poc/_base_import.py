# AUTH:DEVNEUROSIM:7A3F9E2B | samples/poc/_base_import.py
"""
Import helper for `BaseAlgorithm`.

The repo doesn't ship a Python package installer for `NeuroSim.Engine`, so the sample
scripts add `NeuroSim.Engine/src` to `sys.path`.

Sample Use Only Need Reimplementation with BaseAlgorithm Clearly Explored
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def import_base_algorithm() -> Any:
    # samples/poc/_base_import.py -> NeuroSim/
    poc_dir = Path(__file__).resolve().parent
    neuro_sim_root = poc_dir.parents[1]  # .../NeuroSim
    engine_src = neuro_sim_root / "NeuroSim.Engine" / "src"
    if not (engine_src / "neurosim_engine").exists():
        raise RuntimeError(f"NeuroSim.Engine python package not found at: {engine_src}")
    sys.path.insert(0, str(engine_src))
    from neurosim_engine.core.base_algorithm import BaseAlgorithm  # type: ignore

    return BaseAlgorithm

