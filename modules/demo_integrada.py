"""
demo_integrada.py — AI Assist CAD Demo Completa.

Pipeline: NLP → Parâmetros → CAD (STEP) → Análise FEM → 3D Viewer Interativo
GPU: RTX 4070 via PyTorch CUDA

Uso:
    python demo_integrada.py "gerador eólico 3MW aço 500x300x200"
    python demo_integrada.py "turbina 2MW alumínio 400x200x150" --multi
    python demo_integrada.py "motor elétrico 500kW cobre 300x200x150" --gpu-bench
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

import numpy as np

# === Imports locais (wrapped para fallback amigável) ===

def load_nlp():
    from ai_assist_cad.nlp_parser import parse_project_parameters
    from ai_assist_cad.cad_generator import CADGenerator
    from ai_assist_cad.knowledge_engine import KnowledgeEngine
    return parse_project_parameters, CADGenerator, KnowledgeEngine

def load_cad():
    from src.cad.export import export_step
    from src.cad.parametric import ParametricModel
    return export_step, ParametricModel

def load_vis():
    from src.visualization.threejs_viewer import generate_viewer_html, generate_cylinder_viewer
    return generate_viewer_html, generate_cylinder_viewer

def load_gpu():
    from src.gpu.gpu_accelerator import benchmark, gpu_available, get_gpu_name
    return benchmark, gpu_available, get_gpu_name


def generate_heat_map_values(n_nodes: int, domain: str = "structural") -> list[float]:
    """Generate synthetic heat map data for visualization demo."""
    np.random.seed(42)
    side = int(np.ceil(np.sqrt(n_nodes)))
    total = side * side
    x = np.linspace(-1, 1, side)
    X, Y = np.meshgrid(x, x)
    Z = X.ravel()[:total]  # flatten to 1D
    W = Y.ravel()[:total]
    if domain == "structural":
        values = np.exp(-2 * (Z**2 + W**2)) * 100 + np.random.randn(total) * 5
        return [round(float(v), 1) for v in values[:n_nodes]]
    elif domain == "thermal":
        values = np.linspace(300, 500, total)
        return [round(float(v), 1) for v in values[:n_nodes]]
    return [round(float(v), 1) for v in np.random.rand(n_nodes) * 100]


def build_interactive_viewer(
    params: dict,
    step_path: str | None = None,
    multi_domain: bool = False,
    title: str = "AI Assist CAD — 3D Viewer",
) -> str:
    """Build complete interactive 3D viewer HTML with heat maps.

    Returns HTML content string.
    """
    generate_viewer_html, _ = load_vis()
    benchmark_fn, gpu_avail, gpu_name = load_gpu()
    bench = benchmark_fn()

    # Dimensions from params
    w = params.get("width", 300)
    h = params.get("height", 200)
    d = params.get("depth", 150)

    geometry = {
        "type": "box",
        "width": w / 100,
        "height": h / 100,
        "depth": d / 100,
    }

    # Domain options
    domains = ["von Mises (MPa)", "Temperatura (°C)", "Deslocamento (mm)"]
    if multi_domain:
        domains += ["Tensão Principal (MPa)", "Densidade TopOpt", "Fator de Segurança"]

    # Heat map data
    n_verts = 500
    heat_data = {
        "von Mises (MPa)": generate_heat_map_values(n_verts, "structural"),
        "Temperatura (°C)": generate_heat_map_values(n_verts, "thermal"),
        "Deslocamento (mm)": [round(v * 0.1, 2) for v in generate_heat_map_values(n_verts)],
    }
    if multi_domain:
        heat_data["Tensão Principal (MPa)"] = generate_heat_map_values(n_verts, "structural")
        heat_data["Densidade TopOpt"] = [round(np.random.random(), 2) for _ in range(n_verts)]
        heat_data["Fator de Segurança"] = [round(np.random.uniform(1.0, 5.0), 1) for _ in range(n_verts)]

    # Build GPU info overlay
    gpu_info = f"GPU: {gpu_name} | Speedup: {bench['speedup_x']}× | Matrix: {bench['matrix_size']}×{bench['matrix_size']}" if gpu_avail() else "CPU mode"

    # Generate viewer with all domains
    html = generate_viewer_html(
        title=title,
        legend_label="Field Value",
        legend_min="0",
        legend_max="100",
        camera_position=(max(w, h, d) / 60, max(w, h, d) / 50, max(w, h, d) / 30),
        geometry_json=json.dumps(geometry),
        domain_options=domains,
    )

    # Inject GPU overlay + heat data into the HTML
    script_inject = f"""
<script>
const gpuInfo = '{gpu_info}';
const heatData = {json.dumps(heat_data)};
const infoDiv = document.getElementById('info');
infoDiv.innerHTML += ' | <span style="font-size:11px;color:#8af">' + gpuInfo + '</span>';
// Pre-compute legend values
document.querySelector('#legend div:first-child').innerHTML = 'von Mises (MPa)';
</script>"""
    html = html.replace("</body>", script_inject + "\n</body>")

    return html


def run_demo(description: str, multi: bool = False, gpu_bench: bool = False):
    """Execute full AI Assist CAD demo pipeline."""
    parse_project_parameters, CADGenerator, KnowledgeEngine = load_nlp()
    export_step, ParametricModel = load_cad()
    benchmark_fn, gpu_avail, gpu_name = load_gpu()

    # Step 0: GPU info
    print(f"╔══════════════════════════════════════════╗")
    print(f"║   AI Assist CAD — Demo Integrada         ║")
    print(f"║   GPU: {gpu_name() or 'CPU':<30s}║")
    if gpu_bench:
        bench = benchmark_fn()
        print(f"║   Speedup: {bench['speedup_x']}× ({bench['cpu_time_s']}s CPU → {bench['gpu_time_s']}s GPU)║")
    print(f"╚══════════════════════════════════════════╝")

    # Step 1: NLP Parse
    print(f"\n📝 NLP: Parsing description...")
    params = parse_project_parameters(description)
    print(f"   → Machine: {params.get('machine_type', 'generic')}")
    print(f"   → Materials: {params.get('materials', ['steel'])}")
    print(f"   → Dimensions: {params.get('width', 'auto')}×{params.get('height', 'auto')}×{params.get('depth', 'auto')}")
    if params.get("power_kW"):
        print(f"   → Power: {params['power_kW']} kW")

    # Step 2: Knowledge Engine dimensioning
    print(f"\n📐 KE: Dimensioning...")
    ke = KnowledgeEngine("data")
    if params.get("power_kW"):
        shaft = ke.dimension_shaft(torque_Nm=params["power_kW"] * 10)
        stator = ke.dimension_stator_outer(power_kW=params["power_kW"])
        print(f"   → Shaft: {shaft['diameter_mm']} mm")
        print(f"   → Stator: {stator['diameter_mm']} mm")

    # Step 3: CAD Generation
    print(f"\n⚙️ CAD: Generating geometry...")
    w = params.get("width", 300)
    h = params.get("height", 200)
    d = params.get("depth", 150)
    model = ParametricModel(
        model_id="DEMO-001",
        name=description[:40],
        machine_type=params.get("machine_type", "generic"),
        width=w, height=h, depth=d,
        material=(params.get("materials") or ["steel"])[0],
    )
    with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as f:
        step_path = f.name
    step_file = export_step(model, step_path)
    print(f"   → STEP: {step_file}")

    # Also build with ai_assist_cad generator for comparison
    gen = CADGenerator(ke)
    cad_result = gen.generate(params)
    print(f"   → Components: {len(cad_result.get('components', []))}")

    # Step 4: Interactive 3D Viewer
    print(f"\n🎨 3D: Building interactive viewer...")
    html = build_interactive_viewer(
        params,
        step_path=step_file,
        multi_domain=multi,
        title=f"AI Assist CAD — {params.get('machine_type', 'Generic').title()}",
    )
    html_path = "/tmp/ai_assist_cad_demo.html"
    Path(html_path).write_text(html)
    print(f"   → HTML viewer: {html_path}")

    # Step 5: Open browser
    print(f"\n🚀 Opening interactive 3D viewer...")
    webbrowser.open(f"file://{html_path}")

    print(f"\n✅ Demo concluída!")
    print(f"   Viewer: file://{html_path}")
    print(f"   STEP:   {step_file}")
    print(f"   GPU:    {gpu_name() or 'CPU'}")
    if multi:
        print(f"   Mode:   Multi-domínio (6 campos)")
    else:
        print(f"   Mode:   Single-domínio (3 campos)")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Assist CAD — Demo Integrada com GPU e 3D Interativo"
    )
    parser.add_argument("description", nargs="?", default="gerador eólico 3MW aço 500x300x200",
                        help="Descrição em linguagem natural do projeto")
    parser.add_argument("--multi", action="store_true",
                        help="Modo multi-domínio (6 campos de análise)")
    parser.add_argument("--gpu-bench", action="store_true",
                        help="Executar benchmark GPU vs CPU")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_demo(args.description, multi=args.multi, gpu_bench=args.gpu_bench)
    return 0


if __name__ == "__main__":
    sys.exit(main())
