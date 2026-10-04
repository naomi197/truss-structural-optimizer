import numpy as np
from typing import List
from .models import Node, Element
from .fea import TrussSolver

def compute_total_mass(nodes: List[Node], elements: List[Element]) -> float:
    solver = TrussSolver(nodes, elements)
    return sum(e.area * solver.element_length_and_angles(e)[0] * e.density for e in elements)

def optimize_truss(nodes: List[Node], elements: List[Element], max_stress_ratio=0.9, max_iter=15):
    allowed_areas = sorted([0.0001, 0.0002, 0.0004, 0.0008, 0.0016, 0.0032])
    for _ in range(max_iter):
        TrussSolver(nodes, elements).solve()
        changed = False
        for elem in elements:
            limit = elem.yield_strength * max_stress_ratio
            idx = int(np.searchsorted(allowed_areas, elem.area))
            if abs(elem.stress) > limit and idx < len(allowed_areas) - 1:
                elem.area = allowed_areas[idx + 1]
                changed = True
            elif abs(elem.stress) < limit * 0.4 and idx > 0:
                elem.area = allowed_areas[idx - 1]
                changed = True
        if not changed: break
    TrussSolver(nodes, elements).solve()
    return elements
