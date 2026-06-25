# =============================================================================
# Mesh Convergence Verification Module
# Part of T012 — Phase 2 Foundational
# Re-exports convergence functions from validation package
# =============================================================================
from src.common.validation import (
    verify_mesh_convergence,
    verify_conservation,
    verify_temporal_stability,
    VerificationResult,
)

__all__ = [
    "verify_mesh_convergence",
    "verify_conservation",
    "verify_temporal_stability",
    "VerificationResult",
]
