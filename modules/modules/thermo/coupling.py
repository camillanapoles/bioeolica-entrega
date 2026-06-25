"""
src/thermo/coupling.py — Acoplamento Termo-Estrutural (M³ Multifísica).
Degrada o Módulo de Young (E) baseado na temperatura operacional do fluido.
"""

class ThermalStructuralCoupler:
    """
    Caso de uso M³: O acoplamento entre o domínio térmico/fluido e o estrutural.
    """
    def __init__(self, E0_Pa: float = 1.0e9, T_ref_K: float = 293.15):
        self.E0_Pa = E0_Pa
        self.T_ref_K = T_ref_K
        # Coeficiente de degradação térmica linear aproximado para polímeros/compósitos
        self.degradation_factor = 1e-3 

    def get_degraded_E(self, T_K: float) -> float:
        """
        Calcula o Módulo de Young degradado pela temperatura.
        
        Fórmula simplificada para演示: E(T) = E0 * [1 - alpha * (T - T_ref)]
        onde 'alpha' é o coeficiente de degradação térmica.
        """
        # Prevenir degradação total negativa
        degradation = 1.0 - self.degradation_factor * (T_K - self.T_ref_K)
        degraded_E = self.E0_Pa * max(degradation, 0.1) # Mínimo de 10% da rigidez original
        
        return degraded_E
