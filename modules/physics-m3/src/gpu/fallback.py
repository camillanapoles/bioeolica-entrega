"""CuPy CPU fallback — tenta CUDA, fallback para NumPy com warning.

Uso:
    from physics_m3.gpu import GPUAccelerator
    acc = GPUAccelerator()
    if acc.is_available():
        arr = acc.to_gpu(np_array)
        result = acc.solve_cg(A, b)
    else:
        # CPU fallback automático
        result = acc.solve_cg(A_cpu, b_cpu)
"""
from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import cg as scipy_cg

try:
    import cupy as cp  # type: ignore
    from cupyx.scipy.sparse import csr_matrix as cp_csr_matrix  # type: ignore
    from cupyx.scipy.sparse.linalg import cg as cp_cg  # type: ignore
    _HAS_CUDA = True
except ImportError:
    _HAS_CUDA = False


class GPUAccelerator:
    """GPU accelerator with automatic CPU fallback."""

    def __init__(self, device_id: int = 0):
        self._device_id = device_id
        self._cp = None
        if _HAS_CUDA:
            try:
                self._cp = cp
                self._cp.cuda.Device(device_id).use()
            except Exception:
                self._cp = None

    @staticmethod
    def is_available() -> bool:
        return _HAS_CUDA

    @staticmethod
    def get_warning() -> str:
        return "CuPy not available. Install with: pip install cupy-cuda12x. Using CPU fallback (slower)."

    def to_gpu(self, array: np.ndarray):
        if self._cp is not None:
            return self._cp.asarray(array)
        warnings.warn(self.get_warning())
        return array

    def to_cpu(self, array):
        if self._cp is not None and hasattr(array, 'get'):
            return self._cp.asnumpy(array)
        return np.asarray(array)

    def solve_cg(self, A, b, x0=None, tol=1e-6, maxiter=1000):
        """Conjugate gradient solver with GPU/CPU fallback."""
        if self._cp is not None and not isinstance(A, np.ndarray) and not isinstance(A, csr_matrix):
            try:
                result = cp_cg(A, b, x0=x0, tol=tol, maxiter=maxiter)
                return result
            except Exception:
                pass

        # CPU fallback
        if isinstance(A, np.ndarray) or isinstance(A, csr_matrix):
            b_np = np.asarray(b).flatten()
            x, info = scipy_cg(A, b_np, x0=x0, rtol=tol, maxiter=maxiter)
            return x, info

        raise TypeError(f"Unsupported matrix type: {type(A)}")
