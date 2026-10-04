import pytest
from truss_optimizer.models import Node, Member
from truss_optimizer.solver import analyze_truss
from truss_optimizer.optimizer import optimize_member_sections

def test_simple_triangle_truss():
    nodes = [
        Node(id=0, x=0.0, y=0.0, restrain_x=True, restrain_y=True),
        Node(id=1, x=4.0, y=0.0, restrain_x=False, restrain_y=True),
        Node(id=2, x=2.0, y=3.0, restrain_x=False, restrain_y=False, force_y=-10000.0),
    ]
    members = [
        Member(id=0, start_node=0, end_node=1, e_modulus=200.0, area=10.0, yield_stress=250.0),
        Member(id=1, start_node=0, end_node=2, e_modulus=200.0, area=10.0, yield_stress=250.0),
        Member(id=2, start_node=1, end_node=2, e_modulus=200.0, area=10.0, yield_stress=250.0),
    ]

    result = analyze_truss(nodes, members)
    assert len(result.member_results) == 3
    assert result.max_deflection_mm > 0.0

def test_cross_section_optimizer():
    nodes = [
        Node(id=0, x=0.0, y=0.0, restrain_x=True, restrain_y=True),
        Node(id=1, x=3.0, y=0.0, restrain_x=False, restrain_y=True),
        Node(id=2, x=1.5, y=2.0, restrain_x=False, restrain_y=False, force_y=-5000.0),
    ]
    members = [
        Member(id=0, start_node=0, end_node=1, e_modulus=200.0, area=1.0, yield_stress=250.0),
        Member(id=1, start_node=0, end_node=2, e_modulus=200.0, area=1.0, yield_stress=250.0),
        Member(id=2, start_node=1, end_node=2, e_modulus=200.0, area=1.0, yield_stress=250.0),
    ]

    opt_members, result = optimize_member_sections(nodes, members)
    assert len(opt_members) == 3
    assert result.total_weight_kg > 0.0
