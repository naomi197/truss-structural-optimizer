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

## Quickstart


`powershell
pip install numpy matplotlib pytest
$env:PYTHONPATH = "$PWD\src"
python -m truss_optimizer examples\warren_truss.json --optimize --csv outputs\member_forces.csv --json-summary outputs\summary.json --plot outputs\warren_truss.png
pytest -v

``n
## Author

Developed by **Alireza Fazeli**
*Automation & Software Engineer | Computational Civil Engineering*
