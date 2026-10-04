import argparse, os, csv
from .io import load_truss_from_json
from .fea import TrussSolver
from .optimizer import optimize_truss, compute_total_mass
from .plotter import plot_truss

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--optimize", action="store_true")
    p.add_argument("--outdir", default="outputs")
    args = p.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    nodes, elements = load_truss_from_json(args.input)
    init_m = compute_total_mass(nodes, elements)
    if args.optimize:
        elements = optimize_truss(nodes, elements)
        fin_m = compute_total_mass(nodes, elements)
        print(f"Initial Mass: {init_m:.2f} kg -> Optimized Mass: {fin_m:.2f} kg")
    solver = TrussSolver(nodes, elements)
    U = solver.solve()
    plot_truss(nodes, elements, U, os.path.join(args.outdir, "truss_deformation.png"))
    with open(os.path.join(args.outdir, "results.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Element_ID", "Area_m2", "Force_N", "Stress_MPa"])
        for e in elements:
            w.writerow([e.id, f"{e.area:.6f}", f"{e.axial_force:.2f}", f"{e.stress/1e6:.2f}"])
    print("Analysis & Plot completed successfully!")

if __name__ == "__main__":
    main()
