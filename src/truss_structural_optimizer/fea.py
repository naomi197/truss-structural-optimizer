import numpy as np
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
