"""
Command-line interface (CLI) for 2D truss structural analysis and optimization.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .io import load_truss_model, save_results_csv, save_summary_json
from .optimizer import optimize_member_sections
from .solver import analyze_truss
from .visualization import plot_truss


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="truss_optimizer",
        description="2D Truss Finite Element Direct Stiffness Analysis & Weight Optimization.",
    )
    parser.add_argument(
        "model",
        type=str,
        help="Path to JSON file containing truss nodes and members.",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Run discrete cross-section sizing optimization for minimal weight.",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Path to export member forces and stress results in CSV.",
    )
    parser.add_argument(
        "--json-summary",
        type=str,
        default=None,
        help="Path to export structured analysis summary in JSON.",
    )
    parser.add_argument(
        "--plot",
        type=str,
        default=None,
        help="Path to save high-resolution deformation & stress plot (e.g. outputs/truss.png).",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=100.0,
        help="Displacement amplification scale factor for plotting (default: 100x).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        nodes, members = load_truss_model(args.model)
    except Exception as e:
        print(f"Error loading model: {e}", file=sys.stderr)
        return 1

    print(f"Model loaded: {len(nodes)} nodes, {len(members)} structural members.")

    if args.optimize:
        print("Running cross-sectional weight optimization...")
        members, result = optimize_member_sections(nodes, members)
        print("Optimization converged successfully!")
    else:
        print("Running direct stiffness analysis...")
        result = analyze_truss(nodes, members)

    print("\n--- Structural Analysis Summary ---")
    print(f"Total Structural Weight : {result.total_weight_kg:.2f} kg")
    print(f"Max Node Deflection     : {result.max_deflection_mm:.4f} mm")
    print(f"Max Member Stress       : {result.max_stress_mpa:.2f} MPa")
    
    all_safe = all(m.is_safe for m in result.member_results)
    status_str = "PASSED (All members within yield limits)" if all_safe else "FAILED (Stress limits exceeded)"
    print(f"Design Verification     : {status_str}")

    if args.csv:
        save_results_csv(result, args.csv)
        print(f"Member results saved to : {args.csv}")

    if args.json_summary:
        save_summary_json(result, args.json_summary)
        print(f"Summary saved to        : {args.json_summary}")

    if args.plot:
        plot_truss(nodes, members, result=result, output_path=args.plot, scale_factor=args.scale)
        print(f"Plot saved to           : {args.plot}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
