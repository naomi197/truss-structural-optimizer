"""
Plotting and visual analysis for 2D trusses.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

from .models import AnalysisResult, Member, Node


def plot_truss(
    nodes: List[Node],
    members: List[Member],
    result: AnalysisResult | None = None,
    output_path: str | Path | None = None,
    scale_factor: float = 100.0,
    title: str = "2D Truss Structural Analysis",
) -> None:
    """
    Plot the truss geometry, undeformed state, and deformed shape with axial stresses.
    """
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    node_map = {n.id: n for n in nodes}

    # 1. Plot original undeformed geometry (dashed grey)
    for m in members:
        n1 = node_map[m.start_node]
        n2 = node_map[m.end_node]
        ax.plot(
            [n1.x, n2.x],
            [n1.y, n2.y],
            color="#A0AEC0",
            linestyle="--",
            linewidth=1.2,
            zorder=1,
            label="Undeformed" if m.id == 0 else ""
        )

    # 2. Plot deformed geometry if analysis result is available
    if result is not None:
        # Map stress results by member id
        res_map = {r.member_id: r for r in result.member_results}
        
        # Determine deformed node positions
        # Note: displacements in result are in mm; convert to m for plotting
        def_coords: Dict[int, tuple[float, float]] = {}
        for n in nodes:
            ux, uy = result.displacements.get(n.id, (0.0, 0.0))
            def_coords[n.id] = (
                n.x + (ux / 1000.0) * scale_factor,
                n.y + (uy / 1000.0) * scale_factor
            )

        for m in members:
            p1 = def_coords[m.start_node]
            p2 = def_coords[m.end_node]
            m_res = res_map.get(m.id)
            
            # Tension (blue), Compression (crimson/red), Zero/Safe (green/gray)
            if m_res and m_res.axial_force > 1e-3:
                color = "#3182CE"  # Blue: Tension
                lbl = "Tension"
            elif m_res and m_res.axial_force < -1e-3:
                color = "#E53E3E"  # Red: Compression
                lbl = "Compression"
            else:
                color = "#718096"
                lbl = "Zero Force"

            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linewidth=2.4, zorder=2)

        # Plot deformed nodes
        for nid, (nx, ny) in def_coords.items():
            ax.scatter(nx, ny, color="#2D3748", s=40, zorder=3)
            ax.annotate(
                f"N{nid}",
                (nx, ny),
                textcoords="offset points",
                xytext=(0, 7),
                ha="center",
                fontsize=8,
                weight="bold",
                color="#1A202C"
            )

    # 3. Mark support restraints
    for n in nodes:
        if n.fix_x and n.fix_y:
            ax.scatter(n.x, n.y, marker="^", s=130, color="#DD6B20", zorder=4, label="Pin Support" if n.id == 0 else "")
        elif n.fix_y:
            ax.scatter(n.x, n.y, marker="o", s=90, facecolors="none", edgecolors="#DD6B20", linewidth=2, zorder=4, label="Roller Support" if n.id == 0 else "")

        # Mark applied external forces
        if abs(n.load_x) > 0 or abs(n.load_y) > 0:
            ax.annotate(
                "",
                xy=(n.x, n.y),
                xytext=(n.x - (n.load_x * 0.02 if n.load_x != 0 else 0), n.y - (n.load_y * 0.02 if n.load_y != 0 else 0)),
                arrowprops=dict(facecolor="#805AD5", edgecolor="#805AD5", width=1.5, headwidth=6),
                zorder=5
            )
            ax.text(
                n.x,
                n.y - 0.35,
                f"F=({n.load_x:.0f}, {n.load_y:.0f}) kN",
                ha="center",
                fontsize=8,
                color="#553C9A",
                weight="bold"
            )

    ax.set_aspect("equal", adjustable="datalim")
    ax.set_title(f"{title} (Deformation Scale: {scale_factor}x)", fontsize=13, weight="bold", pad=12)
    ax.set_xlabel("X Coordinate (m)", fontsize=10)
    ax.set_ylabel("Y Coordinate (m)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6)

    # Custom legend for engineering clarity
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    if by_label:
        ax.legend(by_label.values(), by_label.keys(), loc="upper right", framealpha=0.9, fontsize=9)

    plt.tight_layout()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_p, dpi=200)
        plt.close()
    else:
        plt.show()
