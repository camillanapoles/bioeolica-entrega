"""GPU acceleration wrapper — CuPy + CPU fallback + benchmark."""
from typing import Dict, List, Tuple
from physics_m3.gpu import GPUAccelerator as BaseGPU


class GPUAccelerator(BaseGPU):
    """GPU wrapper com benchmark e mesh upload."""

    @property
    def has_cuda(self) -> bool:
        return self.is_available()

    def mesh_to_gpu(self, vertices, faces):
        if self._cp:
            return self._cp.array(vertices), self._cp.array(faces)
        return vertices, faces

    def batch_solve(self, matrices: List, vectors: List) -> List[Tuple]:
        return [self.solve_cg(A, b) for A, b in zip(matrices, vectors)]

    def benchmark_vs_cpu(self, size: int = 100) -> Dict:
        import numpy as np
        from scipy.sparse import csr_matrix
        import time
        A = csr_matrix(np.random.rand(size, size))
        b = np.random.rand(size)
        t0 = time.time()
        x, info = self.solve_cg(A, b)
        cpu_time = time.time() - t0
        return {"matrix_size": size, "cpu_time_s": round(cpu_time, 4), "converged": info == 0}
