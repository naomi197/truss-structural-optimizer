"""
Data structures for 2D truss finite element analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Node:
    id: int
    x: float
    y: float
    restrain_x: bool = False
    restrain_y: bool = False
    force_x: float = 0.0
    force_y: float = 0.0

    @property
    def fix_x(self) -> bool:
        return self.restrain_x

    @property
    def fix_y(self) -> bool:
        return self.restrain_y

    @property
    def load_x(self) -> float:
        return self.force_x

    @property
    def load_y(self) -> float:
        return self.force_y


@dataclass
class Member:
    id: int
    start_node: int
    end_node: int
    e_modulus: float      # GPa
    area: float           # cm^2
    yield_stress: float   # MPa
    density: float = 7850.0  # kg/m^3


@dataclass
class MemberResult:
    member_id: int
    length: float
    axial_force: float       # kN
    stress: float            # MPa
    safety_factor: float
    is_safe: bool
    weight_kg: float

    def __init__(self, **kwargs):
        # Required
        self.member_id = kwargs["member_id"]
        self.length = kwargs.get("length", kwargs.get("length_m"))

        # Force (accept multiple names)
        if "axial_force" in kwargs:
            self.axial_force = kwargs["axial_force"]
        elif "axial_force_kn" in kwargs:
            self.axial_force = kwargs["axial_force_kn"]
        else:
            raise TypeError("MemberResult missing axial_force / axial_force_kn")

        # Stress (accept multiple names)
        if "stress" in kwargs:
            self.stress = kwargs["stress"]
        elif "axial_stress" in kwargs:
            self.stress = kwargs["axial_stress"]
        elif "axial_stress_mpa" in kwargs:
            self.stress = kwargs["axial_stress_mpa"]
        else:
            raise TypeError("MemberResult missing stress / axial_stress / axial_stress_mpa")

        # Others
        self.safety_factor = kwargs["safety_factor"]
        self.is_safe = kwargs["is_safe"]
        self.weight_kg = kwargs.get("weight_kg", kwargs.get("weight", kwargs.get("mass_kg", 0.0)))

    # Aliases for other modules / outputs
    @property
    def length_m(self) -> float:
        return self.length

    @property
    def axial_force_kn(self) -> float:
        return self.axial_force

    @property
    def axial_stress(self) -> float:
        return self.stress

    @property
    def axial_stress_mpa(self) -> float:
        return self.stress


@dataclass
class AnalysisResult:
    member_results: List[MemberResult]
    displacements: dict[int, tuple[float, float]]  # node_id -> (u_x_mm, u_y_mm)

    # solver.py currently may not provide reactions; keep optional for compatibility
    reactions: Optional[dict[int, tuple[float, float]]] = None  # node_id -> (R_x_kn, R_y_kn)

    total_weight_kg: float = 0.0
    max_deflection_mm: float = 0.0
    max_stress_mpa: float = 0.0
