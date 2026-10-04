"""
2D truss analysis using the Direct Stiffness Method.

Units:
- Coordinates: m
- Loads and axial forces: kN
- Young's modulus: GPa
- Cross-sectional area: cm^2
- Stress: MPa
- Displacements in the final result: mm
"""

from __future__ import annotations

from math import hypot
from typing import Dict, List, Tuple

import numpy as np

from .models import (
    AnalysisResult,
    Member,
    MemberResult,
    Node,
)


STEEL_DENSITY_KG_M3 = 7850.0


def _dof_index(node_id: int) -> Tuple[int, int]:
    """Return the global x/y degree-of-freedom indexes for a node."""
    base = 2 * node_id
    return base, base + 1


def _area_m2(area_cm2: float) -> float:
    """Convert cross-sectional area from cm^2 to m^2."""
    return area_cm2 * 1.0e-4


def _elastic_modulus_kn_m2(e_gpa: float) -> float:
    """Convert Young's modulus from GPa to kN/m^2."""
    return e_gpa * 1.0e6


def _member_geometry(
    member: Member,
    nodes: Dict[int, Node],
) -> Tuple[float, float, float]:
    """Return member length and direction cosines."""
    start = nodes[member.start_node]
    end = nodes[member.end_node]

    dx = end.x - start.x
    dy = end.y - start.y
    length = hypot(dx, dy)

    if length <= 0.0:
        raise ValueError(
            f"Member {member.id} has zero length. "
            "Start and end nodes must be different."
        )

    cosine = dx / length
    sine = dy / length
    return length, cosine, sine


def _element_stiffness(
    member: Member,
    nodes: Dict[int, Node],
) -> Tuple[float, np.ndarray]:
    """Build the 4x4 global stiffness matrix for one truss member."""
    length, cosine, sine = _member_geometry(member, nodes)

    area_m2 = _area_m2(member.area)
    elastic_modulus = _elastic_modulus_kn_m2(member.e_modulus)

    coefficient = elastic_modulus * area_m2 / length

    c = cosine
    s = sine

    stiffness = coefficient * np.array(
        [
            [c * c, c * s, -c * c, -c * s],
            [c * s, s * s, -c * s, -s * s],
            [-c * c, -c * s, c * c, c * s],
            [-c * s, -s * s, c * s, s * s],
        ],
        dtype=float,
    )

    return length, stiffness


def assemble_global_stiffness(
    nodes: List[Node],
    members: List[Member],
) -> np.ndarray:
    """Assemble the global structural stiffness matrix."""
    if not nodes:
        raise ValueError("At least one node is required.")

    node_map = {node.id: node for node in nodes}
    expected_ids = set(range(len(nodes)))

    if set(node_map) != expected_ids:
        raise ValueError(
            "Node IDs must be consecutive integers starting from 0."
        )

    total_dofs = 2 * len(nodes)
    global_stiffness = np.zeros((total_dofs, total_dofs), dtype=float)

    for member in members:
        if member.start_node not in node_map:
            raise ValueError(
                f"Member {member.id} references unknown start node "
                f"{member.start_node}."
            )

        if member.end_node not in node_map:
            raise ValueError(
                f"Member {member.id} references unknown end node "
                f"{member.end_node}."
            )

        length, local_stiffness = _element_stiffness(member, node_map)

        start_x, start_y = _dof_index(member.start_node)
        end_x, end_y = _dof_index(member.end_node)

        dofs = [start_x, start_y, end_x, end_y]

        for row in range(4):
            for column in range(4):
                global_stiffness[dofs[row], dofs[column]] += (
                    local_stiffness[row, column]
                )

    return global_stiffness


def _load_vector(nodes: List[Node]) -> np.ndarray:
    """Create the global load vector."""
    loads = np.zeros(2 * len(nodes), dtype=float)

    for node in nodes:
        x_dof, y_dof = _dof_index(node.id)
        loads[x_dof] = node.load_x
        loads[y_dof] = node.load_y

    return loads


def _constrained_dofs(nodes: List[Node]) -> List[int]:
    """Return the indexes of restrained degrees of freedom."""
    constrained: List[int] = []

    for node in nodes:
        x_dof, y_dof = _dof_index(node.id)

        if node.fix_x:
            constrained.append(x_dof)

        if node.fix_y:
            constrained.append(y_dof)

    return constrained


def _calculate_member_results(
    nodes: List[Node],
    members: List[Member],
    displacements_m: np.ndarray,
) -> List[MemberResult]:
    """Calculate axial force, stress, safety factor, and status."""
    node_map = {node.id: node for node in nodes}
    results: List[MemberResult] = []

    for member in members:
        length, cosine, sine = _member_geometry(member, node_map)

        start_x, start_y = _dof_index(member.start_node)
        end_x, end_y = _dof_index(member.end_node)

        start_displacement = np.array(
            [displacements_m[start_x], displacements_m[start_y]]
        )
        end_displacement = np.array(
            [displacements_m[end_x], displacements_m[end_y]]
        )

        relative_displacement = end_displacement - start_displacement
        axial_extension = (
            relative_displacement[0] * cosine
            + relative_displacement[1] * sine
        )

        strain = axial_extension / length
        area_m2 = _area_m2(member.area)
        elastic_modulus = _elastic_modulus_kn_m2(member.e_modulus)

        axial_force_kn = elastic_modulus * area_m2 * strain

        # kN / cm^2 converted to MPa:
        # 1 kN / cm^2 = 10 MPa
        stress_mpa = axial_force_kn * 10.0 / member.area

        absolute_stress = abs(stress_mpa)

        if absolute_stress == 0.0:
            safety_factor = float("inf")
        else:
            safety_factor = member.yield_stress / absolute_stress

        is_safe = absolute_stress <= member.yield_stress

        results.append(
            MemberResult(
                member_id=member.id,
                length=length,
                axial_force=axial_force_kn,
                stress=stress_mpa,
                safety_factor=safety_factor,
                is_safe=is_safe,
            )
        )

    return results


def _calculate_total_weight(
    nodes: List[Node],
    members: List[Member],
) -> float:
    """Calculate approximate steel weight in kilograms."""
    node_map = {node.id: node for node in nodes}
    total_volume_m3 = 0.0

    for member in members:
        length, _, _ = _member_geometry(member, node_map)
        total_volume_m3 += length * _area_m2(member.area)

    return total_volume_m3 * STEEL_DENSITY_KG_M3


def analyze_truss(
    nodes: List[Node],
    members: List[Member],
) -> AnalysisResult:
    """
    Analyze a 2D truss using the Direct Stiffness Method.

    Raises:
        ValueError: If the model is invalid or unstable.
    """
    if not nodes:
        raise ValueError("The truss must contain at least one node.")

    if not members:
        raise ValueError("The truss must contain at least one member.")

    global_stiffness = assemble_global_stiffness(nodes, members)
    loads = _load_vector(nodes)
    constrained = _constrained_dofs(nodes)

    if not constrained:
        raise ValueError(
            "No supports were defined. At least one restrained DOF is required."
        )

    total_dofs = len(loads)
    free_dofs = [
        dof for dof in range(total_dofs) if dof not in constrained
    ]

    if not free_dofs:
        raise ValueError("All degrees of freedom are constrained.")

    reduced_stiffness = global_stiffness[
        np.ix_(free_dofs, free_dofs)
    ]
    reduced_loads = loads[free_dofs]

    try:
        reduced_displacements = np.linalg.solve(
            reduced_stiffness,
            reduced_loads,
        )
    except np.linalg.LinAlgError as error:
        raise ValueError(
            "The truss is unstable or insufficiently supported. "
            "Check the geometry, members, and supports."
        ) from error

    displacements_m = np.zeros(total_dofs, dtype=float)
    displacements_m[free_dofs] = reduced_displacements

    node_displacements = {
        node.id: (
            displacements_m[2 * node.id] * 1000.0,
            displacements_m[2 * node.id + 1] * 1000.0,
        )
        for node in nodes
    }

    member_results = _calculate_member_results(
        nodes,
        members,
        displacements_m,
    )

    max_deflection_mm = max(
        hypot(x_displacement, y_displacement)
        for x_displacement, y_displacement in node_displacements.values()
    )

    max_stress_mpa = max(
        (abs(result.stress) for result in member_results),
        default=0.0,
    )

    return AnalysisResult(
        displacements=node_displacements,
        member_results=member_results,
        total_weight_kg=_calculate_total_weight(nodes, members),
        max_deflection_mm=max_deflection_mm,
        max_stress_mpa=max_stress_mpa,
    )

# Compatibility alias
solve_truss = analyze_truss
