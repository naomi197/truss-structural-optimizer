"""
Input/Output utilities for reading structural definitions and exporting results.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List, Tuple

import numpy as np

from truss_optimizer.models import AnalysisResult, Member, Node


class NumpyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle NumPy scalar types and bools safely."""
    def default(self, obj):
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, (np.integer, int)):
            return int(obj)
        if isinstance(obj, (np.floating, float)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def load_truss_from_json(file_path: str | Path) -> Tuple[List[Node], List[Member]]:
    """Load structural nodes and members from a JSON model file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_members = data.get("members", data.get("elements", []))
    si_schema = "elements" in data or any("node_i" in member for member in raw_members)

    def force_kn(value: float) -> float:
        # The example file stores Newtons. The solver uses kilonewtons.
        if si_schema and abs(value) >= 1000.0:
            return value / 1000.0
        return value

    def area_cm2(value: float) -> float:
        # The example file stores square metres. The solver uses square centimetres.
        if si_schema and value < 1.0:
            return value * 10_000.0
        return value

    def modulus_gpa(member: dict) -> float:
        if "e_modulus" in member:
            return float(member["e_modulus"])
        if "elastic_modulus" in member:
            value = float(member["elastic_modulus"])
            return value / 1.0e9 if value > 1000.0 else value
        return 210.0

    def yield_mpa(member: dict) -> float:
        if "yield_stress" in member:
            return float(member["yield_stress"])
        if "yield_strength" in member:
            value = float(member["yield_strength"])
            return value / 1.0e6 if value > 1000.0 else value
        return 250.0

    nodes = [
        Node(
            id=n["id"],
            x=float(n["x"]),
            y=float(n["y"]),
            restrain_x=bool(n.get("restrain_x", n.get("fix_x", n.get("is_fixed_x", False)))),
            restrain_y=bool(n.get("restrain_y", n.get("fix_y", n.get("is_fixed_y", False)))),
            force_x=force_kn(float(n.get("force_x", n.get("load_x", n.get("fx", 0.0))))),
            force_y=force_kn(float(n.get("force_y", n.get("load_y", n.get("fy", 0.0))))),
        )
        for n in data.get("nodes", [])
    ]

    members = [
        Member(
            id=m["id"],
            start_node=int(m.get("start_node", m.get("node_i"))),
            end_node=int(m.get("end_node", m.get("node_j"))),
            e_modulus=modulus_gpa(m),
            area=area_cm2(float(m["area"])),
            yield_stress=yield_mpa(m),
            density=float(m.get("density", 7850.0)),
        )
        for m in raw_members
    ]

    return nodes, members


def save_results_csv(result: AnalysisResult, file_path: str | Path) -> None:
    """Export member analysis results to a clean CSV file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "member_id",
            "length_m",
            "axial_force_kn",
            "stress_mpa",
            "safety_factor",
            "is_safe",
            "weight_kg",
        ])
        for m in result.member_results:
            writer.writerow([
                m.member_id,
                round(float(m.length), 3),
                round(float(m.axial_force), 3),
                round(float(m.axial_stress), 3),
                round(float(m.safety_factor), 3) if m.safety_factor != float("inf") else "inf",
                bool(m.is_safe),
                round(float(m.weight_kg), 3),
            ])


def save_summary_json(result: AnalysisResult, file_path: str | Path) -> None:
    """Export overall structural behavior metrics to JSON."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        "total_weight_kg": round(float(result.total_weight_kg), 2),
        "max_deflection_mm": round(float(result.max_deflection_mm), 4),
        "max_stress_mpa": round(float(result.max_stress_mpa), 2),
        "is_structure_safe": bool(all(bool(m.is_safe) for m in result.member_results)),
        "displacements": {
            str(node_id): [round(float(disp[0]), 4), round(float(disp[1]), 4)]
            for node_id, disp in result.displacements.items()
        },
        "members": [
            {
                "member_id": int(m.member_id),
                "force_kn": round(float(m.axial_force), 3),
                "stress_mpa": round(float(m.axial_stress), 3),
                "safety_factor": round(float(m.safety_factor), 3) if m.safety_factor != float("inf") else "inf",
                "is_safe": bool(m.is_safe),
            }
            for m in result.member_results
        ],
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, cls=NumpyJSONEncoder)

# Compatibility alias for cli.py
load_truss_model = load_truss_from_json
