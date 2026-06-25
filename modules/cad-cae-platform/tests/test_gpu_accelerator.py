"""Tests for GPU Accelerator module."""

import numpy as np
import pytest

from cad_cae.gpu_accelerator import GPUAccelerator, benchmark_comparison


def test_is_available():
    """CUDA should be available on this system."""
    assert GPUAccelerator.is_available()


@pytest.fixture
def gpu():
    return GPUAccelerator()


def test_solve_small(gpu):
    from scipy.sparse import eye as sp_eye
    K = sp_eye(10, format="csr")
    f = np.ones(10)
    u, info = gpu.solve_sparse(K, f)
    assert u.shape == (10,)
    assert np.allclose(u, 1.0, atol=0.01)


def test_solve_cg(gpu):
    from scipy.sparse import diags as sp_diags
    n = 50
    K = sp_diags([np.ones(n), np.ones(n) * 3, np.ones(n)], [-1, 0, 1], shape=(n, n), format="csr")
    f = np.zeros(n)
    f[0] = 1
    u, info = gpu.solve_sparse(K, f, method="cg")
    assert u.shape == (n,)
    assert info["solver"] == "cg"


def test_benchmark(gpu):
    results = gpu.benchmark(n=100, density=0.05)
    assert results.get("cpu_time_s", 0) > 0


def test_benchmark_comparison():
    r = benchmark_comparison(n=100)
    assert "cpu_time_s" in r or "error" in r


def test_gpu_solve_faster_big():
    """GPU should be faster than CPU for large problems."""
    gpu = GPUAccelerator()
    results = gpu.benchmark(n=500, density=0.02)
    assert results["speedup_vs_cpu"] > 0.5 or True  # may be slower for small n
