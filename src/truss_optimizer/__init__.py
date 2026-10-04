"""
Truss Structural Optimizer
2D Finite Element Method & Direct Stiffness Structural Analysis Toolkit.
"""

from .models import AnalysisResult, Member, MemberResult, Node
from .solver import analyze_truss
from .optimizer import optimize_member_sections

__version__ = "0.1.0"
__all__ = [
    "Node",
    "Member",
    "MemberResult",
    "AnalysisResult",
    "analyze_truss",
    "optimize_member_sections",
]
