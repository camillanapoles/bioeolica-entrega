# =============================================================================
# Certification Module
# Part of T012 — Phase 2 Foundational
# Re-exports certification functions from validation package
# =============================================================================
from src.common.validation import (
    certify_result,
    CertificationReport,
)

__all__ = [
    "certify_result",
    "CertificationReport",
]
