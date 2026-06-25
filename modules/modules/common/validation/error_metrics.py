# =============================================================================
# Error Metrics Validation Module
# Part of T012 — Phase 2 Foundational
# Re-exports validation functions from validation package
# =============================================================================
from src.common.validation import (
    validate_correlation,
    validate_relative_error,
    ValidationResult,
)

__all__ = [
    "validate_correlation",
    "validate_relative_error",
    "ValidationResult",
]
