import json
from typing import List, Tuple
from .models import Node, Element

def load_truss_from_json(path: str) -> Tuple[List[Node], List[Element]]:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    nodes = [Node(id=n["id"], x=float(n["x"]), y=float(n["y"]), fx=float(n.get("fx", 0.0)), fy=float(n.get("fy", 0.0)), is_fixed_x=bool(n.get("is_fixed_x", False)), is_fixed_y=bool(n.get("is_fixed_y", False))) for n in d["nodes"]]
    elements = [Element(id=e["id"], node_i=int(e["node_i"]), node_j=int(e["node_j"]), area=float(e.get("area", 0.001)), elastic_modulus=float(e.get("elastic_modulus", 2.1e11)), yield_strength=float(e.get("yield_strength", 250e6)), density=float(e.get("density", 7850.0))) for e in d["elements"]]
    return nodes, elements
