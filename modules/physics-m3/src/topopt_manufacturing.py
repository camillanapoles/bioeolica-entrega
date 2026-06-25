"""
Topology Optimization Module — Manufacturing Constraints
=========================================================

Extends SIMP-based topology optimization with additive manufacturing (AM)
constraints: minimum overhang angle, minimum feature size, support volume
estimation, and anisotropy compensation.

The class wraps a ``TopOpt`` (2D) or ``TopOpt3D`` instance and intercepts
the density update to enforce printability constraints at each iteration.
Constraint application is modular — each constraint can be enabled or
disabled independently.

Constraint Reference
--------------------
**Overhang angle**
    In powder-bed fusion and directed energy deposition, unsupported
    downward-facing surfaces exceeding a critical angle (typically 30--50
    degrees from vertical) require sacrificial support structures. The
    constraint detects elements whose density exceeds a threshold but whose
    supporting neighbourhood (cone defined by the overhang angle) contains
    no solid material.

**Minimum feature size**
    Processes such as laser powder bed fusion have a minimum printable
    feature diameter (typically 0.2--0.5 mm for metals). The constraint
    enforces this via morphological closing (dilation followed by erosion)
    on the binarised density field.

**Anisotropy factor**
    AM parts exhibit direction-dependent strength: Z-direction (build)
    strength is typically 70--90 % of XY strength. The anisotropy factor
    scales the effective stiffness in the build direction, allowing the
    optimiser to penalise columns that rely on full Z-strength.

References
----------
- Gaynor, A. T., & Guest, J. K. (2016). Topology optimization considering
  overhang constraints: Eliminating sacrificial support material in
  additive manufacturing through design. *Structural and Multidisciplinary
  Optimization*, 54(5), 1157--1172.
- Langelaar, M. (2017). An additive manufacturing filter for topology
  optimization of print-ready designs. *Structural and Multidisciplinary
  Optimization*, 55(3), 871--883.
- Sigmund, O. (2007). Morphology-based black and white filters for
  topology optimization. *Structural and Multidisciplinary Optimization*,
  33(4--5), 401--424.
- Liu, J., & To, A. C. (2017). Deposition path planning-integrated
  structural topology optimization for 3D additive manufacturing subject
  to self-support constraint. *Structural and Multidisciplinary
  Optimization*, 55(5), 1585--1603.

Classes
-------
TopOptManufacturing
    Manufacturing-constrained topology optimization wrapper.
"""

from __future__ import annotations

from typing import Any, Optional, Union

import numpy as np
from scipy import ndimage
from scipy.ndimage import (
    binary_closing,
    generate_binary_structure,
    iterate_structure,
)


# ---------------------------------------------------------------------------
#  Type alias
# ---------------------------------------------------------------------------
_BaseOptimizer = Union["TopOpt", "TopOpt3D"]


# ---------------------------------------------------------------------------
#  Main class
# ---------------------------------------------------------------------------

class TopOptManufacturing:
    """Manufacturing constraints for SIMP-based topology optimization.

    Wraps a ``TopOpt`` or ``TopOpt3D`` instance and applies additive
    manufacturing constraints — overhang, minimum feature size, and
    anisotropy — at each optimisation iteration.

    Parameters
    ----------
    base_optimizer : TopOpt or TopOpt3D
        Base topology optimisation instance.
    overhang_angle : float, optional
        Minimum overhang angle in degrees measured from the vertical
        (default 45). Elements whose unsupported downward projection
        exceeds this angle are penalised. Set to 90 to disable overhang
        enforcement.
    min_feature_size : int, optional
        Minimum feature size in elements (default 2). Features smaller
        than this are removed via morphological closing. Set to 1 to
        disable minimum feature enforcement.
    anisotropy_factor : float, optional
        Ratio of Z-direction (build direction) strength to XY-plane
        strength (default 1.0, isotropic). Values below 1.0 reduce the
        effective stiffness of elements whose primary load path aligns
        with the build direction. Set to 1.0 to disable anisotropy
        scaling.
    density_threshold : float, optional
        Threshold for binarising density in constraint checks
        (default 0.5).

    Attributes
    ----------
    base : TopOpt or TopOpt3D
        The wrapped base optimizer.
    density : np.ndarray
        Current density field (shape matches base optimizer).
    iteration : int
        Current iteration number.
    compliance_history : list[float]
        Compliance values per iteration.
    support_volume_history : list[float]
        Support volume fraction per iteration.
    _is_3d : bool
        Whether the wrapped optimizer is 3D.

    Examples
    --------
    >>> from topology_optimization import TopOpt
    >>> opt = TopOpt(nelx=60, nely=20, volfrac=0.5)
    >>> am = TopOptManufacturing(opt, overhang_angle=45, min_feature_size=3)
    >>> x_opt = am.solve(max_iter=100, verbose=True)
    >>> print(am.check_printability(x_opt))
    """

    # ------------------------------------------------------------------
    #  Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        base_optimizer: _BaseOptimizer,
        overhang_angle: float = 45.0,
        min_feature_size: int = 2,
        anisotropy_factor: float = 1.0,
        density_threshold: float = 0.5,
    ) -> None:
        self.base = base_optimizer

        # --- validate overhang angle ---
        if not (0.0 < overhang_angle <= 90.0):
            raise ValueError(
                f"overhang_angle must be in (0, 90], got {overhang_angle}"
            )
        self.overhang_angle = float(overhang_angle)
        self._overhang_rad = np.radians(self.overhang_angle)
        self._tan_angle = np.tan(self._overhang_rad)

        # --- validate minimum feature size ---
        if min_feature_size < 1:
            raise ValueError(
                f"min_feature_size must be >= 1, got {min_feature_size}"
            )
        self.min_feature_size = int(min_feature_size)

        # --- validate anisotropy factor ---
        if anisotropy_factor <= 0.0 or anisotropy_factor > 1.0:
            raise ValueError(
                f"anisotropy_factor must be in (0, 1], got {anisotropy_factor}"
            )
        self.anisotropy_factor = float(anisotropy_factor)

        # --- validate density threshold ---
        if not (0.0 < density_threshold <= 1.0):
            raise ValueError(
                "density_threshold must be in (0, 1], "
                f"got {density_threshold}"
            )
        self.density_threshold = float(density_threshold)

        # Detect dimensionality from the base optimizer
        self._is_3d = hasattr(self.base, "nelz")

        # History tracking
        self.compliance_history: list[float] = []
        self.support_volume_history: list[float] = []
        self.iteration = 0

        # Pre-compute structuring element for morphological operations
        self._struct_elem = self._build_structuring_element()

    # ------------------------------------------------------------------
    #  Structuring element for morphological constraints
    # ------------------------------------------------------------------

    def _build_structuring_element(self) -> np.ndarray:
        """Build the structuring element for morphological constraints.

        The element is a ball (2D) or sphere (3D) with radius equal to
        ``min_feature_size / 2`` (minimum 1), used for morphological
        closing to enforce the minimum feature size.

        Returns
        -------
        se : np.ndarray
            Binary structuring element array.
        """
        radius = max(1, self.min_feature_size // 2)
        if self._is_3d:
            # 3D connectivity: full 26-point neighbourhood
            base = generate_binary_structure(rank=3, connectivity=3)
            return iterate_structure(base, iterations=radius)
        else:
            # 2D connectivity: full 8-point neighbourhood
            base = generate_binary_structure(rank=2, connectivity=2)
            return iterate_structure(base, iterations=radius)

    # ------------------------------------------------------------------
    #  Overhang constraint — core detection
    # ------------------------------------------------------------------

    def _detect_overhang_2d(self, density: np.ndarray) -> np.ndarray:
        """Detect overhang violations in a 2D density field.

        For each solid element, checks whether any solid support exists
        within the downward cone defined by ``overhang_angle``. Elements
        without support are flagged.

        The build direction is +y (array index increasing). Support is
        expected from elements at larger y-indices (below in the array).

        Parameters
        ----------
        density : np.ndarray, shape (nely, nelx)
            Current density field.

        Returns
        -------
        overhang : np.ndarray, shape (nely, nelx), dtype bool
            True where an overhang violation is detected.
        """
        nely, nelx = density.shape
        threshold = self.density_threshold
        tan_a = self._tan_angle
        overhang = np.zeros_like(density, dtype=bool)

        for ely in range(nely - 1):
            for elx in range(nelx):
                if density[ely, elx] < threshold:
                    continue

                supported = False
                # Maximum downward search distance
                max_dy = min(
                    nely - ely - 1,
                    int(np.ceil(nely / max(tan_a, 1e-12))),
                )

                for dy in range(1, max_dy + 1):
                    y_check = ely + dy
                    cone_radius = max(1, int(np.ceil(dy * tan_a)))
                    x_min = max(0, elx - cone_radius)
                    x_max = min(nelx, elx + cone_radius + 1)

                    if np.any(density[y_check, x_min:x_max] >= threshold):
                        supported = True
                        break

                if not supported:
                    overhang[ely, elx] = True

        return overhang

    def _detect_overhang_3d(self, density: np.ndarray) -> np.ndarray:
        """Detect overhang violations in a 3D density field.

        For each solid element, checks whether solid support exists
        within the downward cone defined by ``overhang_angle`` in the
        3D build direction (+z).

        Parameters
        ----------
        density : np.ndarray, shape (nelz, nely, nelx)
            Current density field.

        Returns
        -------
        overhang : np.ndarray, shape (nelz, nely, nelx), dtype bool
            True where an overhang violation is detected.
        """
        nelz, nely, nelx = density.shape
        threshold = self.density_threshold
        tan_a = self._tan_angle
        overhang = np.zeros_like(density, dtype=bool)

        for elz in range(nelz - 1):
            for ely in range(nely):
                for elx in range(nelx):
                    if density[elz, ely, elx] < threshold:
                        continue

                    supported = False
                    max_dz = min(
                        nelz - elz - 1,
                        int(np.ceil(nelz / max(tan_a, 1e-12))),
                    )

                    for dz in range(1, max_dz + 1):
                        z_check = elz + dz
                        cone_r = max(1, int(np.ceil(dz * tan_a)))
                        y_min = max(0, ely - cone_r)
                        y_max = min(nely, ely + cone_r + 1)
                        x_min = max(0, elx - cone_r)
                        x_max = min(nelx, elx + cone_r + 1)

                        if np.any(
                            density[z_check, y_min:y_max, x_min:x_max]
                            >= threshold
                        ):
                            supported = True
                            break

                    if not supported:
                        overhang[elz, ely, elx] = True

        return overhang

    def apply_overhang_constraint(self, density: np.ndarray) -> np.ndarray:
        """Enforce minimum overhang angle on a density field.

        Elements that violate the overhang constraint are penalised by
        setting their density to zero. The constraint is applied
        iteratively: after penalising, the check is repeated because
        penalised elements may themselves create new overhang violations
        for elements above them.

        Parameters
        ----------
        density : np.ndarray
            Density field (2D or 3D depending on the base optimizer).

        Returns
        -------
        density_clean : np.ndarray
            Density field with overhang violations removed.
        """
        if self.overhang_angle >= 90.0:
            return density

        x = density.copy()
        threshold = self.density_threshold

        # Iterative removal: cascading overhang is resolved by re-checking
        # after each removal pass
        for _ in range(max(x.shape)):
            if self._is_3d:
                oh = self._detect_overhang_3d(x)
            else:
                oh = self._detect_overhang_2d(x)

            if not np.any(oh):
                break

            x[oh] = 0.0

            # Smooth the transition at the overhang interface by blending
            interface = self._overhang_interface(x, oh)
            x[interface] = threshold * x[interface]

        return x

    def _overhang_interface(
        self, density: np.ndarray, overhang: np.ndarray
    ) -> np.ndarray:
        """Identify elements at the interface between overhang and support.

        Parameters
        ----------
        density : np.ndarray
            Density field after overhang removal.
        overhang : np.ndarray
            Boolean mask of elements flagged as overhang violations.

        Returns
        -------
        interface : np.ndarray, dtype bool
            True for elements adjacent to the overhang boundary.
        """
        if self._is_3d:
            return self._overhang_interface_3d(density, overhang)
        return self._overhang_interface_2d(density, overhang)

    @staticmethod
    def _overhang_interface_2d(
        density: np.ndarray, overhang: np.ndarray
    ) -> np.ndarray:
        """2D interface detection between overhang and supported regions.

        Parameters
        ----------
        density : np.ndarray, shape (nely, nelx)
            Density field after overhang removal.
        overhang : np.ndarray, shape (nely, nelx), dtype bool
            Overhang violation mask.

        Returns
        -------
        interface : np.ndarray, shape (nely, nelx), dtype bool
            Interface mask.
        """
        nely, nelx = density.shape
        threshold = 0.5
        interface = np.zeros_like(density, dtype=bool)

        for ely in range(1, nely):
            for elx in range(nelx):
                if density[ely, elx] >= threshold and overhang[ely - 1, elx]:
                    interface[ely, elx] = True
        return interface

    @staticmethod
    def _overhang_interface_3d(
        density: np.ndarray, overhang: np.ndarray
    ) -> np.ndarray:
        """3D interface detection between overhang and supported regions.

        Parameters
        ----------
        density : np.ndarray, shape (nelz, nely, nelx)
            Density field after overhang removal.
        overhang : np.ndarray, shape (nelz, nely, nelx), dtype bool
            Overhang violation mask.

        Returns
        -------
        interface : np.ndarray, shape (nelz, nely, nelx), dtype bool
            Interface mask.
        """
        nelz, nely, nelx = density.shape
        threshold = 0.5
        interface = np.zeros_like(density, dtype=bool)

        for elz in range(1, nelz):
            for ely in range(nely):
                for elx in range(nelx):
                    if (
                        density[elz, ely, elx] >= threshold
                        and overhang[elz - 1, ely, elx]
                    ):
                        interface[elz, ely, elx] = True
        return interface

    # ------------------------------------------------------------------
    #  Minimum feature size constraint
    # ------------------------------------------------------------------

    def apply_min_feature(self, density: np.ndarray) -> np.ndarray:
        """Enforce minimum feature size via morphological closing.

        The density field is binarised at ``density_threshold``, then
        morphological closing (dilation followed by erosion) is applied
        using a spherical structuring element with radius equal to
        ``min_feature_size / 2``. The result is blended with the original
        density to preserve grayscale information where features are
        already large enough.

        Parameters
        ----------
        density : np.ndarray
            Density field (2D or 3D depending on the base optimizer).

        Returns
        -------
        density_clean : np.ndarray
            Density field with minimum feature size enforced.
        """
        if self.min_feature_size <= 1:
            return density

        se = self._struct_elem
        threshold = self.density_threshold

        # Binarise
        binary = density >= threshold

        # Morphological closing: fill small gaps, connect thin features
        closed = binary_closing(binary, structure=se, iterations=1)

        # Identify regions changed by closing
        changed = binary != closed
        result = density.copy()

        # Regions that were filled by closing (gaps filled)
        filled = changed & closed
        result[filled] = np.maximum(result[filled], threshold * 0.9)

        # Regions that were eroded by closing (thin features removed)
        eroded = changed & ~closed
        result[eroded] = np.minimum(result[eroded], threshold * 0.5)

        return result

    # ------------------------------------------------------------------
    #  Anisotropy scaling
    # ------------------------------------------------------------------

    def _anisotropy_penalty(self, density: np.ndarray) -> np.ndarray:
        """Compute an anisotropy penalty field.

        For each element, the penalty is proportional to the density
        gradient magnitude in the build direction relative to the
        in-plane magnitude. Elements whose load path is primarily in
        the build direction are penalised according to the
        ``anisotropy_factor``.

        Parameters
        ----------
        density : np.ndarray
            Density field (2D or 3D).

        Returns
        -------
        penalty : np.ndarray, same shape as density
            Anisotropy penalty factor in [0, 1].
        """
        if self.anisotropy_factor >= 1.0:
            return np.ones_like(density)

        if self._is_3d:
            return self._anisotropy_penalty_3d(density)
        return self._anisotropy_penalty_2d(density)

    def _anisotropy_penalty_2d(self, density: np.ndarray) -> np.ndarray:
        """2D anisotropy penalty.

        Build direction is +y (downward in array).

        Parameters
        ----------
        density : np.ndarray, shape (nely, nelx)

        Returns
        -------
        penalty : np.ndarray, shape (nely, nelx)
        """
        nely, nelx = density.shape
        penalty = np.ones_like(density)

        # Central differences for gradient in x and y
        grad_x = np.zeros_like(density)
        grad_y = np.zeros_like(density)

        grad_x[:, 1:-1] = 0.5 * (density[:, 2:] - density[:, :-2])
        grad_y[1:-1, :] = 0.5 * (density[2:, :] - density[:-2, :])

        # Gradient magnitude in build direction (y) vs total
        grad_total = np.sqrt(grad_x ** 2 + grad_y ** 2) + 1e-12
        grad_build = np.abs(grad_y)

        # Ratio of build-direction gradient to total gradient
        build_ratio = grad_build / grad_total

        # Apply anisotropy: high build-ratio elements are penalised
        penalty = 1.0 - (1.0 - self.anisotropy_factor) * build_ratio * density

        return penalty

    def _anisotropy_penalty_3d(self, density: np.ndarray) -> np.ndarray:
        """3D anisotropy penalty.

        Build direction is +z.

        Parameters
        ----------
        density : np.ndarray, shape (nelz, nely, nelx)

        Returns
        -------
        penalty : np.ndarray, shape (nelz, nely, nelx)
        """
        nelz, nely, nelx = density.shape
        penalty = np.ones_like(density)

        # Central differences for gradient in each direction
        grad_x = np.zeros_like(density)
        grad_y = np.zeros_like(density)
        grad_z = np.zeros_like(density)

        grad_x[:, :, 1:-1] = 0.5 * (density[:, :, 2:] - density[:, :, :-2])
        grad_y[:, 1:-1, :] = 0.5 * (density[:, 2:, :] - density[:-2, :, :])
        grad_z[1:-1, :, :] = 0.5 * (density[2:, :, :] - density[:-2, :, :])

        # Gradient magnitude in build direction (z) vs total
        grad_total = (
            np.sqrt(grad_x ** 2 + grad_y ** 2 + grad_z ** 2) + 1e-12
        )
        grad_build = np.abs(grad_z)

        build_ratio = grad_build / grad_total
        penalty = (
            1.0 - (1.0 - self.anisotropy_factor) * build_ratio * density
        )

        return penalty

    # ------------------------------------------------------------------
    #  Support volume estimation
    # ------------------------------------------------------------------

    def estimate_support_volume(self, density: np.ndarray) -> float:
        """Estimate the support material volume fraction.

        Returns the fraction of elements that violate the overhang
        constraint and would therefore require sacrificial support
        structures in an AM process.

        Parameters
        ----------
        density : np.ndarray
            Density field (2D or 3D).

        Returns
        -------
        support_frac : float
            Support volume as a fraction of total design volume
            (0 = no support, 1 = full support).
        """
        if self.overhang_angle >= 90.0:
            return 0.0

        if self._is_3d:
            overhang = self._detect_overhang_3d(density)
        else:
            overhang = self._detect_overhang_2d(density)

        return float(np.mean(overhang))

    # ------------------------------------------------------------------
    #  Printability analysis
    # ------------------------------------------------------------------

    def check_printability(self, density: Optional[np.ndarray] = None) -> dict[str, Any]:
        """Analyse a density field for additive manufacturing printability.

        Evaluates the design against all active manufacturing constraints
        and returns a dictionary of metrics.

        Parameters
        ----------
        density : np.ndarray, optional
            Density field to evaluate. If None, uses the current density
            from the base optimizer.

        Returns
        -------
        report : dict
            Dictionary with keys:

            - ``"printable"`` : bool — whether all checks pass
            - ``"overhang_ratio"`` : float — fraction of elements
              violating overhang constraint
            - ``"overhang_angle_deg"`` : float — the overhang angle used
            - ``"min_feature_size"`` : int — the feature size used
            - ``"min_feature_pass"`` : bool — whether min feature
              check passes
            - ``"support_volume"`` : float — support volume fraction
            - ``"anisotropy_factor"`` : float — the anisotropy factor
            - ``"anisotropy_mean_penalty"`` : float — mean anisotropy
              penalty across all elements
            - ``"mean_density"`` : float — mean element density
            - ``"solid_fraction"`` : float — fraction of elements above
              the density threshold
        """
        if density is None:
            density = self.density

        threshold = self.density_threshold
        total_elements = density.size

        # --- overhang assessment ---
        if self._is_3d:
            oh_mask = self._detect_overhang_3d(density)
        else:
            oh_mask = self._detect_overhang_2d(density)

        overhang_ratio = float(np.mean(oh_mask))

        # --- minimum feature assessment ---
        if self.min_feature_size > 1:
            filtered = self.apply_min_feature(density)
            binary_orig = density >= threshold
            binary_filt = filtered >= threshold
            n_changed = int(np.sum(binary_orig != binary_filt))
            min_feature_pass = n_changed < 0.01 * total_elements
        else:
            min_feature_pass = True

        # --- anisotropy assessment ---
        aniso_penalty = self._anisotropy_penalty(density)
        mean_penalty = float(np.mean(aniso_penalty))

        # --- overall printability ---
        printable = (
            overhang_ratio < 0.05
            and min_feature_pass
            and mean_penalty > self.anisotropy_factor * 0.95
        )

        return {
            "printable": printable,
            "overhang_ratio": overhang_ratio,
            "overhang_angle_deg": self.overhang_angle,
            "min_feature_size": self.min_feature_size,
            "min_feature_pass": min_feature_pass,
            "support_volume": float(np.mean(oh_mask)),
            "anisotropy_factor": self.anisotropy_factor,
            "anisotropy_mean_penalty": mean_penalty,
            "mean_density": float(np.mean(density)),
            "solid_fraction": float(np.mean(density >= threshold)),
        }

    # ------------------------------------------------------------------
    #  Single iteration
    # ------------------------------------------------------------------

    def step(self) -> float:
        """Perform one optimisation iteration with manufacturing constraints.

        The iteration order is:

        1. Run the base optimiser's ``step()``
        2. Apply overhang constraint (if active)
        3. Apply minimum feature constraint (if active)
        4. Apply anisotropy scaling (if active)

        Returns
        -------
        comp : float
            Compliance value at this iteration.
        """
        # Run the base step (FEM assembly, solve, OC update)
        comp = self.base.step()
        density = self.base.density

        # Apply manufacturing constraints in sequence
        density = self.apply_overhang_constraint(density)
        density = self.apply_min_feature(density)

        # Anisotropy scaling: scale densities in build-critical regions
        aniso = self._anisotropy_penalty(density)
        density = density * aniso

        # Re-project onto [x_min, 1.0] to maintain SIMP stability
        density = np.clip(density, self.base.x_min, 1.0)

        # Update the base optimizer density
        self.base.density = density

        # Track support volume
        sv = self.estimate_support_volume(density)

        self.compliance_history.append(comp)
        self.support_volume_history.append(sv)
        self.iteration += 1

        return comp

    # ------------------------------------------------------------------
    #  Full solve
    # ------------------------------------------------------------------

    def solve(
        self,
        max_iter: int = 200,
        tol: float = 1e-4,
        verbose: bool = False,
    ) -> np.ndarray:
        """Run topology optimisation with manufacturing constraints.

        Parameters
        ----------
        max_iter : int, optional
            Maximum number of iterations (default 200).
        tol : float, optional
            Relative convergence tolerance on compliance change
            (default 1e-4).
        verbose : bool, optional
            If True, print iteration info (default False).

        Returns
        -------
        density : np.ndarray
            Optimised density distribution satisfying manufacturing
            constraints where possible.
        """
        for _ in range(max_iter):
            comp = self.step()
            if verbose:
                print(
                    f"Iteration {self.iteration:3d}: "
                    f"Compliance = {comp:.6e}, "
                    f"Change    = {self._relative_change():.6e}, "
                    f"Support   = {self.support_volume:.4f}"
                )
            if self._relative_change() < tol and self.iteration > 2:
                if verbose:
                    print(
                        f"Converged after {self.iteration} iterations."
                    )
                break

        return self.density

    # ------------------------------------------------------------------
    #  Convergence helpers
    # ------------------------------------------------------------------

    def _relative_change(self) -> float:
        """Return relative change in compliance over last 3 iterations."""
        if len(self.compliance_history) < 3:
            return 1.0
        prev = self.compliance_history[-2]
        curr = self.compliance_history[-1]
        return float(abs((curr - prev) / (prev + 1e-12)))

    # ------------------------------------------------------------------
    #  Properties
    # ------------------------------------------------------------------

    @property
    def density(self) -> np.ndarray:
        """Current density field from the base optimizer."""
        return self.base.density

    @density.setter
    def density(self, value: np.ndarray) -> None:
        self.base.density = value

    @property
    def support_volume(self) -> float:
        """Current support volume fraction.

        Returns the fraction of elements that violate the overhang
        constraint in the current density field.
        """
        if len(self.support_volume_history) > 0:
            return self.support_volume_history[-1]
        return self.estimate_support_volume(self.density)

    @property
    def volume_fraction(self) -> float:
        """Current volume fraction of the design."""
        return self.base.volume_fraction

    @property
    def converged(self) -> bool:
        """Whether the base solver has converged."""
        return self.base.converged

    # ------------------------------------------------------------------
    #  Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset the optimizer to its initial state."""
        self.base.reset()
        self.compliance_history = []
        self.support_volume_history = []
        self.iteration = 0


# ---------------------------------------------------------------------------
#  Usage example (run as script)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # ---- 2D Example: MBB beam with overhang constraint ----
    print("=" * 60)
    print("2D Topology Optimisation with Manufacturing Constraints")
    print("=" * 60)

    from topology_optimization import TopOpt

    opt_2d = TopOpt(nelx=60, nely=20, volfrac=0.5, penal=3.0, rmin=1.5)
    am_2d = TopOptManufacturing(
        opt_2d,
        overhang_angle=45,
        min_feature_size=3,
        anisotropy_factor=0.85,
    )

    print("Solving MBB beam with AM constraints (60x20, volfrac=0.5)...")
    x_am = am_2d.solve(max_iter=80, verbose=True)
    print(f"Final compliance: {am_2d.compliance_history[-1]:.6e}")
    print(f"Support volume:   {am_2d.support_volume:.4f}")
    print(f"Printability:     {am_2d.check_printability(x_am)}")

    fig, axes = plt.subplots(1, 3, figsize=(14, 3.5))

    # AM-constrained topology
    am_2d.base.plot_density(ax=axes[0])
    axes[0].set_title("AM-constrained topology (45 deg overhang)")

    # Compliance history
    axes[1].plot(am_2d.compliance_history, label="Compliance")
    axes[1].set_xlabel("Iteration")
    axes[1].set_ylabel("Compliance")
    axes[1].set_title("Compliance history")
    axes[1].grid(True)

    # Support volume history
    axes[2].plot(
        am_2d.support_volume_history,
        label="Support volume",
        color="C1",
    )
    axes[2].set_xlabel("Iteration")
    axes[2].set_ylabel("Support volume fraction")
    axes[2].set_title("Support volume history")
    axes[2].grid(True)

    plt.tight_layout()
    plt.show()

    # ---- Comparison: unconstrained vs constrained ----
    print("\n" + "=" * 60)
    print("Comparison: Unconstrained vs AM-Constrained")
    print("=" * 60)

    opt_ref = TopOpt(nelx=60, nely=20, volfrac=0.5, penal=3.0, rmin=1.5)
    x_ref = opt_ref.solve(max_iter=80)

    report_am = am_2d.check_printability(x_am)
    report_ref = am_2d.check_printability(x_ref)

    print(f"{'Metric':<30} {'Unconstrained':>16} {'AM-Constrained':>16}")
    print("-" * 62)
    print(
        f"{'Compliance':<30} {opt_ref.compliance_history[-1]:>16.6e} "
        f"{am_2d.compliance_history[-1]:>16.6e}"
    )
    print(
        f"{'Support volume':<30} {report_ref['support_volume']:>16.4f} "
        f"{report_am['support_volume']:>16.4f}"
    )
    print(
        f"{'Printable':<30} {str(report_ref['printable']):>16} "
        f"{str(report_am['printable']):>16}"
    )

    # ---- 3D Example (small) ----
    print("\n" + "=" * 60)
    print("3D Topology Optimisation with Manufacturing Constraints")
    print("=" * 60)

    try:
        from topopt_avancada import TopOpt3D

        opt_3d = TopOpt3D(
            nelx=16, nely=10, nelz=8, volfrac=0.3, penal=3.0, rmin=1.8,
        )
        am_3d = TopOptManufacturing(
            opt_3d,
            overhang_angle=50,
            min_feature_size=2,
            anisotropy_factor=0.9,
        )

        print("Solving 3D cantilever with AM constraints (16x10x8)...")
        x_3d = am_3d.solve(max_iter=40, verbose=True)

        report_3d = am_3d.check_printability(x_3d)
        print(f"\n3D Printability report:")
        for key, val in report_3d.items():
            print(f"  {key}: {val}")

    except ImportError:
        print("TopOpt3D not available; skipping 3D example.")
    except Exception as exc:
        print(f"3D example failed: {exc}")
