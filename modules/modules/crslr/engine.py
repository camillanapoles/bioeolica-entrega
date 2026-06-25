"""
CRSLR Engine — generates structured engineering reports from analysis results.

Usage:
    python -m src.crslr.engine --input results.json --output report.md
    python -m src.crslr.engine --input results.json --output report.pdf --format pdf
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jinja2

from .schema import load_and_validate, VALID_SECTIONS
from .templates import TEMPLATES_DIR


def create_report(data: dict, format: str = "markdown") -> str:
    """
    Generate CRSLR report from validated data dict.

    Parameters
    ----------
    data : dict
        Validated AnalysisResult as dict.
    format : str
        "markdown" or "html".

    Returns
    -------
    str
        Rendered report content.
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
    )

    if format == "html":
        template_name = "report.html.j2"
    else:
        template_name = "report.md.j2"

    template = env.get_template(template_name)
    return template.render(**data)


def add_uncertainty(data: dict) -> dict:
    """Enhance metrics with uncertainty notation (nominal ± IC 95%)."""
    sections = data.get("sections", {})
    results = sections.get("results", {})
    metrics = results.get("metrics", {})
    for key, val in metrics.items():
        u = val.get("uncertainty", 0)
        v = val.get("value", 0)
        val["display"] = f"{v} ± {u}"
    return data


def add_m9_compliance(data: dict) -> dict:
    """Add M9 compliance metadata to the report data."""
    data.setdefault("m9_compliance", {
        "map_index": f"MAPA-{data.get('analysis_id', 'UNKNOWN')}",
        "log_uuid": f"LOG-{data.get('analysis_id', 'UNKNOWN')}",
        "last_review": data.get("date", ""),
    })
    return data


def render_report(input_path: str, output_path: str, fmt: str = "markdown") -> str:
    """
    Full pipeline: load → validate → enrich → render → write.

    Returns path to generated report.
    """
    result = load_and_validate(input_path)
    data = result.__dict__.copy()
    data = add_uncertainty(data)
    data = add_m9_compliance(data)
    content = create_report(data, format=fmt)

    out = Path(output_path)
    out.write_text(content)
    return str(out.resolve())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate CRSLR engineering reports from analysis results."
    )
    parser.add_argument("--input", required=True, help="Path to input JSON")
    parser.add_argument("--output", required=True, help="Path to output report")
    parser.add_argument(
        "--format", choices=["markdown", "html", "pdf"], default="markdown",
        help="Output format (default: markdown; pdf requires weasyprint)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.format == "pdf":
        try:
            from .render import render_pdf
            result = load_and_validate(args.input)
            data = result.__dict__.copy()
            data = add_uncertainty(data)
            data = add_m9_compliance(data)
            html = create_report(data, format="html")
            render_pdf(html, args.output)
            print(f"PDF report generated: {args.output}")
        except ImportError:
            print("PDF format requires weasyprint. Install: pip install weasyprint")
            return 1
    else:
        path = render_report(args.input, args.output, fmt=args.format)
        print(f"Report generated: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
