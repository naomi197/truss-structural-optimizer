# 2D Truss Structural Optimizer & FEA Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Tests](https://img.shields.io/badge/pytest-passing-brightgreen?logo=pytest)
![Engineering](https://img.shields.io/badge/Domain-Computational%20Civil%20Engineering-orange)

An automated 2D Finite Element Analysis (FEA) solver and discrete cross-sectional structural optimization tool built with Python. Designed for rapid evaluation, stress compliance verification, and minimum-weight sizing of pin-jointed truss frameworks under static nodal forces.

## Key Features

- **Direct Stiffness Method (DSM) Solver:** Global stiffness matrix assembly, displacement solving, axial forces, and member stresses.
- **Automated Sizing Optimization:** Iterative discrete section updates to minimize total weight while meeting allowable stress limits.
- **Engineering Outputs:** Tabular CSV reports, machine-readable JSON summaries, and high-resolution deformation/stress plots.

## Setup

```bash
git clone https://github.com/naomi197/truss-structural-optimizer.git
cd truss-structural-optimizer
python -m venv .venv
source .venv/bin/activate
python -m pip install numpy matplotlib pytest
```

On Windows PowerShell, activate the environment with `.\.venv\Scripts\Activate.ps1` and set `PYTHONPATH` to `$PWD\src`.

## Run

```bash
PYTHONPATH=src python -m truss_optimizer examples/warren_truss.json --optimize --csv outputs/member_forces.csv --json-summary outputs/summary.json --plot outputs/warren_truss.png
PYTHONPATH=src python -m pytest -q
```

## Related work

- [BeamSolver](https://github.com/naomi197/beam-solver) — 2D beam diagrams and PDF reports
- [Water Network Optimizer](https://github.com/naomi197/water-network-optimizer) — Hazen-Williams pipe sizing
- [ClimaScope](https://github.com/naomi197/climascope) — live climate observatory for Android and the browser

## Author

Alireza Sani — [naomi197](https://github.com/naomi197)

Computational civil engineering. Developer: [alirezafazeli@live.com](mailto:alirezafazeli@live.com)
