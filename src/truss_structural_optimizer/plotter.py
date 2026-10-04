import matplotlib.pyplot as plt
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
