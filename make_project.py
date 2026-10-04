import os, json

pkg = os.path.join("src", "truss_structural_optimizer")
os.makedirs(pkg, exist_ok=True)
os.makedirs("tests", exist_ok=True)
os.makedirs("examples", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

with open(os.path.join(pkg, "__init__.py"), "w", encoding="utf-8") as f:
    f.write('__version__ = "0.1.0"\n')

with open(os.path.join(pkg, "models.py"), "w", encoding="utf-8") as f:
    f.write("""from dataclasses import dataclass
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
""")

with open(os.path.join(pkg, "fea.py"), "w", encoding="utf-8") as f:
    f.write("""import numpy as np
from typing import List, Tuple
from .models import Node, Element

class TrussSolver:
    def __init__(self, nodes: List[Node], elements: List[Element]):
        self.nodes = {n.id: n for n in nodes}
        self.elements = elements
        self.node_id_to_dof = {nid: (2 * i, 2 * i + 1) for i, nid in enumerate(sorted(self.nodes.keys()))}
        self.num_dofs = 2 * len(self.nodes)

    def element_length_and_angles(self, elem: Element) -> Tuple[float, float, float]:
        ni, nj = self.nodes[elem.node_i], self.nodes[elem.node_j]
        dx, dy = nj.x - ni.x, nj.y - ni.y
        L = float(np.hypot(dx, dy))
        return L, dx / L, dy / L

    def solve(self):
        K = np.zeros((self.num_dofs, self.num_dofs), dtype=float)
        for elem in self.elements:
            L, c, s = self.element_length_and_angles(elem)
            k_val = (elem.elastic_modulus * elem.area) / L
            k_elem = k_val * np.array([
                [ c*c,  c*s, -c*c, -c*s],
                [ c*s,  s*s, -c*s, -s*s],
                [-c*c, -c*s,  c*c,  c*s],
                [-c*s, -s*s,  c*s,  s*s]
            ])
            dofs = [*self.node_id_to_dof[elem.node_i], *self.node_id_to_dof[elem.node_j]]
            for i in range(4):
                for j in range(4):
                    K[dofs[i], dofs[j]] += k_elem[i, j]

        F = np.zeros(self.num_dofs, dtype=float)
        free_dofs = []
        for nid, node in sorted(self.nodes.items()):
            dx, dy = self.node_id_to_dof[nid]
            F[dx], F[dy] = node.fx, node.fy
            if not node.is_fixed_x: free_dofs.append(dx)
            if not node.is_fixed_y: free_dofs.append(dy)

        U = np.zeros(self.num_dofs, dtype=float)
        if free_dofs:
            U[free_dofs] = np.linalg.solve(K[np.ix_(free_dofs, free_dofs)], F[free_dofs])

        for elem in self.elements:
            L, c, s = self.element_length_and_angles(elem)
            di, dj = self.node_id_to_dof[elem.node_i], self.node_id_to_dof[elem.node_j]
            elem.strain = ((U[dj[0]] - U[di[0]]) * c + (U[dj[1]] - U[di[1]]) * s) / L
            elem.stress = elem.elastic_modulus * elem.strain
            elem.axial_force = elem.stress * elem.area
        return U
""")

with open(os.path.join(pkg, "optimizer.py"), "w", encoding="utf-8") as f:
    f.write("""import numpy as np
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
""")

with open(os.path.join(pkg, "io.py"), "w", encoding="utf-8") as f:
    f.write("""import json
from typing import List, Tuple
from .models import Node, Element

def load_truss_from_json(path: str) -> Tuple[List[Node], List[Element]]:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    nodes = [Node(id=n["id"], x=float(n["x"]), y=float(n["y"]), fx=float(n.get("fx", 0.0)), fy=float(n.get("fy", 0.0)), is_fixed_x=bool(n.get("is_fixed_x", False)), is_fixed_y=bool(n.get("is_fixed_y", False))) for n in d["nodes"]]
    elements = [Element(id=e["id"], node_i=int(e["node_i"]), node_j=int(e["node_j"]), area=float(e.get("area", 0.001)), elastic_modulus=float(e.get("elastic_modulus", 2.1e11)), yield_strength=float(e.get("yield_strength", 250e6)), density=float(e.get("density", 7850.0))) for e in d["elements"]]
    return nodes, elements
""")

with open(os.path.join(pkg, "plotter.py"), "w", encoding="utf-8") as f:
    f.write("""import matplotlib.pyplot as plt
from typing import List
from .models import Node, Element
from .fea import TrussSolver

def plot_truss(nodes: List[Node], elements: List[Element], displacements, out_path: str, scale=100.0):
    solver = TrussSolver(nodes, elements)
    plt.figure(figsize=(9, 5), dpi=300)
    for elem in elements:
        ni, nj = solver.nodes[elem.node_i], solver.nodes[elem.node_j]
        plt.plot([ni.x, nj.x], [ni.y, nj.y], "k--", alpha=0.3)
        di, dj = solver.node_id_to_dof[elem.node_i], solver.node_id_to_dof[elem.node_j]
        plt.plot([ni.x + displacements[di[0]]*scale, nj.x + displacements[dj[0]]*scale],
                 [ni.y + displacements[di[1]]*scale, nj.y + displacements[dj[1]]*scale], "b-", linewidth=2.5)
    plt.title(f"Truss Deformation (Scale x{scale})")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
""")

with open(os.path.join(pkg, "cli.py"), "w", encoding="utf-8") as f:
    f.write("""import argparse, os, csv
from .io import load_truss_from_json
from .fea import TrussSolver
from .optimizer import optimize_truss, compute_total_mass
from .plotter import plot_truss

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--optimize", action="store_true")
    p.add_argument("--outdir", default="outputs")
    args = p.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    nodes, elements = load_truss_from_json(args.input)
    init_m = compute_total_mass(nodes, elements)
    if args.optimize:
        elements = optimize_truss(nodes, elements)
        fin_m = compute_total_mass(nodes, elements)
        print(f"Initial Mass: {init_m:.2f} kg -> Optimized Mass: {fin_m:.2f} kg")
    solver = TrussSolver(nodes, elements)
    U = solver.solve()
    plot_truss(nodes, elements, U, os.path.join(args.outdir, "truss_deformation.png"))
    with open(os.path.join(args.outdir, "results.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Element_ID", "Area_m2", "Force_N", "Stress_MPa"])
        for e in elements:
            w.writerow([e.id, f"{e.area:.6f}", f"{e.axial_force:.2f}", f"{e.stress/1e6:.2f}"])
    print("Analysis & Plot completed successfully!")

if __name__ == "__main__":
    main()
""")

with open(os.path.join(pkg, "__main__.py"), "w", encoding="utf-8") as f:
    f.write('from .cli import main\nif __name__ == "__main__":\n    main()\n')

with open("tests/test_solver.py", "w", encoding="utf-8") as f:
    f.write("""from truss_structural_optimizer.models import Node, Element
from truss_structural_optimizer.fea import TrussSolver

def test_single_bar_tension():
    nodes = [Node(1, 0.0, 0.0, is_fixed_x=True, is_fixed_y=True), Node(2, 1.0, 0.0, fx=10000.0, is_fixed_y=True)]
    elements = [Element(1, 1, 2, area=0.001, elastic_modulus=2e11)]
    solver = TrussSolver(nodes, elements)
    U = solver.solve()
    assert abs(elements[0].stress - 1e7) < 1e-3
""")

warren = {
    "nodes": [
        {"id": 1, "x": 0.0, "y": 0.0, "is_fixed_x": True, "is_fixed_y": True},
        {"id": 2, "x": 2.0, "y": 0.0},
        {"id": 3, "x": 4.0, "y": 0.0, "is_fixed_y": True},
        {"id": 4, "x": 1.0, "y": 1.732, "fy": -50000.0},
        {"id": 5, "x": 3.0, "y": 1.732, "fy": -50000.0}
    ],
    "elements": [
        {"id": 1, "node_i": 1, "node_j": 2, "area": 0.002},
        {"id": 2, "node_i": 2, "node_j": 3, "area": 0.002},
        {"id": 3, "node_i": 4, "node_j": 5, "area": 0.002},
        {"id": 4, "node_i": 1, "node_j": 4, "area": 0.002},
        {"id": 5, "node_i": 2, "node_j": 4, "area": 0.002},
        {"id": 6, "node_i": 2, "node_j": 5, "area": 0.002},
        {"id": 7, "node_i": 3, "node_j": 5, "area": 0.002}
    ]
}
with open("examples/warren_truss.json", "w", encoding="utf-8") as f:
    json.dump(warren, f, indent=2)

print("PROJECT_MODULES_CREATED_SUCCESSFULLY")
