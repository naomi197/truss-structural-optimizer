from truss_structural_optimizer.models import Node, Element
from truss_structural_optimizer.fea import TrussSolver

def test_single_bar_tension():
    nodes = [Node(1, 0.0, 0.0, is_fixed_x=True, is_fixed_y=True), Node(2, 1.0, 0.0, fx=10000.0, is_fixed_y=True)]
    elements = [Element(1, 1, 2, area=0.001, elastic_modulus=2e11)]
    solver = TrussSolver(nodes, elements)
    U = solver.solve()
    assert abs(elements[0].stress - 1e7) < 1e-3
