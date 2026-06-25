#!/usr/bin/env python3
"""
scripts/run_full_pipeline.py — Orquestra a Otimização Topológica (TopOpt),
Extração de Limites e Geração de Geometria 3D (CAD STEP) num fluxo contínuo.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Garantia de importação dos pacotes do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.topopt.run_optimization import run_topopt


def extract_solid_boxes(density_field: list[float], nelx: int, nely: int, threshold: float = 0.5) -> list[tuple[float, float, float, float]]:
    """
    Extrai as coordenadas das caixas (elementos) que excedem o limiar de densidade do TopOpt.
    Retorna uma lista de tuplas normalizadas: (x_norm, y_norm, dx_norm, dy_norm)
    """
    boxes = []
    dx_norm = 1.0 / nelx
    dy_norm = 1.0 / nely
    
    # A densidade retornada pela OpenMDAO tem shape (nelx * nely,)
    # Mapeamento índice -> grid 2D baseado na lógica do fem_component
    for ey in range(nely):
        for ex in range(nelx):
            # Cálculo do índice na malha achatada (nely, nelx) -> (nely * nelx)
            idx = ey * nelx + ex 
            if density_field[idx] >= threshold:
                x_norm = ex * dx_norm
                y_norm = ey * dy_norm
                boxes.append((x_norm, y_norm, dx_norm, dy_norm))
                
    return boxes


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Orquestrador E2E: TopOpt -> Extração -> Geração CAD STEP."
    )
    parser.add_argument("--nelx", type=int, default=40, help="Número de elementos em x")
    parser.add_argument("--nely", type=int, default=20, help="Número de elementos em y")
    parser.add_argument("--vol-frac", type=float, default=0.4, help="Fração de volume alvo")
    parser.add_argument("--output-dir", type=str, default="outputs/cad_run", help="Diretório de saída")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Iniciando Pipeline TopOpt ➞ CAD no diretório: {output_dir.resolve()}")

    # 1. Run Topology Optimization
    print("\n[1/4] Running Topology Optimization...")
    result = run_topopt(
        nelx=args.nelx,
        nely=args.nely,
        vol_frac=args.vol_frac,
        penal=3.0,
        max_iter=50,
        verbose=False
    )
    density_field = result["density_field"]
    print(f"   ➞ Otimização concluída. Compliência final: {result['compliance']:.4e}")

    # 2. Extract Topology Features (Solid Boxes)
    print("\n[2/4] Extracting Topology Features...")
    solid_boxes = extract_solid_boxes(density_field, args.nelx, args.nely, threshold=0.5)
    is_continuous = len(solid_boxes) > 0
    print(f"   ➞ Extração concluída. {len(solid_boxes)} caixas sólidas identificadas.")

    # 3. Generate 3D CAD Model (STEP File)
    print("\n[3/4] Generating 3D CAD Model (STEP)...")
    try:
        from src.cad.assembly import TopologyToCAD
        
        # Instantiate generator (e.g., 100mm x 50mm plate, 10mm thick)
        cad_generator = TopologyToCAD(physical_width_mm=100.0, physical_height_mm=50.0, extrude_depth_mm=10.0)
        step_path = output_dir / "topopt_part.step"
        
        # Generate physical file
        cad_generator.generate_step(solid_boxes=solid_boxes, output_path=str(step_path))
        print(f"   ➞ 3D Model exported successfully to: {step_path}")
        
        # Update metadata to point to the real file
        cad_metadata = {
            "project_name": "TopOpt Generated Bracket",
            "topopt_continuous": is_continuous,
            "step_file": str(step_path),
            "material": "Composite PVA-Graphite"
        }
    except ImportError:
        print("   ⚠️ CadQuery not installed. Skipping STEP generation.")
        cad_metadata = {"error": "CadQuery missing"}
        
    params_path = output_dir / "params_generated.json"
    with open(params_path, "w") as f:
        json.dump(cad_metadata, f, indent=2)

    # 4. Finalization
    print("\n[4/4] Pipeline Complete!")
    print(f"   ➞ Metadata salvo em: {params_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
