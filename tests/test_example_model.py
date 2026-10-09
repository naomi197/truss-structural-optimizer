from truss_optimizer.io import load_truss_model
from truss_optimizer.optimizer import optimize_member_sections


def test_warren_example_optimizes():
    nodes, members = load_truss_model("examples/warren_truss.json")
    assert len(nodes) == 5
    assert len(members) == 7
    _, result = optimize_member_sections(nodes, members)
    assert result.member_results
    assert result.max_stress_mpa > 0
