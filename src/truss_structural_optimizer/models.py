from dataclasses import dataclass
from typing import Optional

@dataclass
class Node:
    id: int
    x: float
    y: float
    fx: float = 0.0
    fy: float = 0.0
    is_fixed_x: bool = False
    is_fixed_y: bool = False

@dataclass
class Element:
    id: int
    node_i: int
    node_j: int
    area: float
    elastic_modulus: float = 2.1e11
    yield_strength: float = 250e6
    density: float = 7850.0
    axial_force: float = 0.0
    stress: float = 0.0
    strain: float = 0.0
