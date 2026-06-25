"""GPU acceleration with graceful CPU fallback.

Uses CuPy when available, falls back to NumPy/SciPy with warning.
"""
from .fallback import GPUAccelerator

__all__ = ["GPUAccelerator"]
