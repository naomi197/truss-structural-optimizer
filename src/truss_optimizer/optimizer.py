"""
Truss cross-section size optimization for minimal structural weight.
"""
from __future__ import annotations

from typing import List, Sequence
from .models import AnalysisResult, Member, Node
from .solver import analyze_truss


def optimize_member_sections(
    nodes: List[Node],
    members: List[Member],
    available_areas_cm2: Sequence[float] | None = None,
    max_iterations: int = 25,
) -> tuple[List[Member], AnalysisResult]:
    """
    Iterative discrete cross-section optimizer to minimize total structural weight
    while ensuring all members satisfy stress limits (is_safe = True).
    """
    if available_areas_cm2 is None:
        # Standard structural steel angle/channel discrete areas (cm^2)
        available_areas_cm2 = [4.0, 6.0, 8.5, 12.0, 16.0, 20.0, 25.0, 32.0, 40.0, 50.0]

    sorted_areas = sorted(available_areas_cm2)
    
    # Initialize members with the middle standard profile
    current_members = [
        Member(
            id=m.id,
            start_node=m.start_node,
            end_node=m.end_node,
            e_modulus=m.e_modulus,
            area=sorted_areas[len(sorted_areas) // 2],
            yield_stress=m.yield_stress,
        )
        for m in members
    ]

    last_result = analyze_truss(nodes, current_members)

    for _ in range(max_iterations):
        converged = True
        new_members: List[Member] = []

        res_dict = {r.member_id: r for r in last_result.member_results}

        for m in current_members:
            m_res = res_dict[m.id]
            curr_idx = sorted_areas.index(m.area) if m.area in sorted_areas else 0

            # If overstressed or safety factor too low, increase section area
            if not m_res.is_safe or m_res.safety_factor < 1.1:
                if curr_idx < len(sorted_areas) - 1:
                    new_area = sorted_areas[curr_idx + 1]
                    converged = False
                else:
                    new_area = sorted_areas[-1]
            # If overly conservative (safety factor > 2.5), try down-sizing to save weight
            elif m_res.safety_factor > 2.5 and curr_idx > 0:
                new_area = sorted_areas[curr_idx - 1]
                converged = False
            else:
                new_area = m.area

            new_members.append(
                Member(
                    id=m.id,
                    start_node=m.start_node,
                    end_node=m.end_node,
                    e_modulus=m.e_modulus,
                    area=new_area,
                    yield_stress=m.yield_stress,
                )
            )

        current_members = new_members
        last_result = analyze_truss(nodes, current_members)

        if converged:
            break

    return current_members, last_result
