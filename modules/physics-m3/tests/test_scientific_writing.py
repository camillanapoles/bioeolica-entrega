#!/usr/bin/env python3
"""Tests for scientific_writing.py — Scientific Production Module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

import numpy as np
from scientific_writing import (
    ScientificReport,
    format_results_table,
)


def test_methodology_section():
    """methodology_section should generate text with filled parameters."""
    report = ScientificReport(
        title="Test Report",
        authors=["Silva, A."],
        language="en",
    )
    text = report.methodology_section(
        test_type="3-point bending",
        standard="ASTM D790",
        params={"span_mm": 80, "width_mm": 25, "thickness_mm": 5, "speed_mm_min": 2.0},
    )
    assert "ASTM D790" in text
    assert "80" in text
    assert "25" in text
    assert len(text) > 50
    assert len(report._methodology_sections) == 1


def test_methodology_section_portuguese():
    """methodology_section in Portuguese should use PT templates."""
    report = ScientificReport(title="Teste", authors=["Silva, A."], language="pt")
    text = report.methodology_section(
        test_type="flexao",
        standard="ASTM D790",
        params={"span_mm": 80, "width_mm": 25, "thickness_mm": 5, "speed_mm_min": 2.0},
    )
    assert "flexao" in text.lower() or "flexão" in text.lower() or "ASTM" in text
    assert len(text) > 30


def test_methodology_tensile():
    """methodology_section should detect tensile test type."""
    report = ScientificReport(title="Test", authors=["A. Silva"])
    text = report.methodology_section(
        test_type="tensile", standard="ASTM D3039",
        params={"gauge_length_mm": 50, "width_mm": 25, "thickness_mm": 5,
                "speed_mm_min": 1.0, "extensometer_mm": 50},
    )
    assert "ASTM D3039" in text
    assert "gauge" in text.lower() or "extensometer" in text.lower()


def test_results_table_latex():
    """results_table should produce valid LaTeX table."""
    report = ScientificReport(title="Test", authors=["A. Silva"])
    table = report.results_table(
        headers=["Sample", "E (GPa)", "Strength (MPa)"],
        rows=[["PM-01", 2.45, 28.3], ["PM-02", 2.52, 29.1]],
        caption="Flexural test results.",
        label="tab:flexure",
        fmt="latex",
    )
    assert "\\begin{table}" in table["latex"]
    assert "\\end{table}" in table["latex"]
    assert "PM-01" in table["latex"]
    assert "2.45" in table["latex"]
    assert table["n_rows"] == 2


def test_results_table_markdown():
    """results_table should produce valid markdown table."""
    table = format_results_table(
        headers=["Property", "Value", "Unit"],
        rows=[["Modulus", 2.5, "GPa"], ["Strength", 30.0, "MPa"]],
        caption="Test table.",
        fmt="markdown",
    )
    assert "| Property" in table["markdown"]
    assert "| ---" in table["markdown"]
    assert "2.50" in table["markdown"]


def test_results_table_csv():
    """results_table should produce valid CSV output."""
    table = format_results_table(
        headers=["A", "B"],
        rows=[["x", 1.0], ["y", 2.0]],
        caption="", fmt="csv",
    )
    assert "A,B" in table["csv"]
    assert "x,1.00" in table["csv"]


def test_add_reference():
    """add_reference should store and return a ref_id."""
    report = ScientificReport(title="Test", authors=["A. Silva"])
    ref_id = report.add_reference(
        authors=["ASTM International"],
        title="ASTM D790: Standard Test Methods",
        year=2020,
        publisher="ASTM",
        ref_type="standard",
    )
    assert ref_id in report._references
    assert len(report._references) == 1


def test_citation_format_ieee():
    """citation_format should produce IEEE-style citation."""
    report = ScientificReport(title="Test", authors=["A. Silva"])
    report.add_reference(
        authors=["Silva, A.", "Santos, B."],
        title="Composite Materials for Wind Energy",
        year=2023,
        journal="Journal of Composite Materials",
        volume="57",
        pages="100-115",
        ref_id="silva_composite_2023",
    )
    citation = report.citation_format("silva_composite_2023", style="ieee")
    assert "Silva" in citation
    assert "Composite Materials" in citation
    assert "2023" in citation


def test_citation_format_abnt():
    """citation_format should produce ABNT-style citation."""
    report = ScientificReport(title="Test", authors=["A. Silva"])
    report.add_reference(
        authors=["Silva, A."],
        title="Standard Test Method",
        year=2020,
        publisher="ABNT",
        ref_id="silva_standard_2020",
        ref_type="standard",
    )
    citation = report.citation_format("silva_standard_2020", style="abnt")
    assert "SILVA" in citation  # ABNT uses uppercase last name
    assert "2020" in citation


def test_generate_bibtex():
    """generate_bibtex should produce valid BibTeX entries."""
    report = ScientificReport(title="Test", authors=["A. Silva"])
    report.add_reference(
        authors=["Silva, A.", "Santos, B."],
        title="Composite Materials Research",
        year=2023,
        journal="J. Compos. Mater.",
        volume="57",
        pages="100-115",
        doi="10.1000/test",
        ref_id="silva_2023",
        ref_type="article",
    )
    bibtex = report.generate_bibtex()
    assert "@article{silva_2023," in bibtex
    assert "author" in bibtex
    assert "doi" in bibtex
    assert "Silva, A." in bibtex


def test_full_report():
    """full_report should combine all sections."""
    report = ScientificReport(
        title="Full Test Report",
        authors=["Silva, A.", "Santos, B."],
        abstract="This report evaluates composite materials.",
        keywords=["composite", "wind energy"],
    )
    report.methodology_section(
        test_type="3-point bending", standard="ASTM D790",
        params={"span_mm": 80, "width_mm": 25, "thickness_mm": 5, "speed_mm_min": 2.0},
    )
    report.results_table(
        headers=["Sample", "Value"],
        rows=[["A", 1.0], ["B", 2.0]],
        caption="Results.", fmt="markdown",
    )
    report.add_reference(
        authors=["ASTM"], title="ASTM D790", year=2020,
        ref_id="astm_d790", ref_type="standard",
    )

    full = report.full_report()
    assert "# Full Test Report" in full
    assert "Abstract" in full
    assert "Methodology" in full
    assert "Results" in full
    assert "References" in full
    assert "ASTM D790" in full
    assert "Silva" in full


def test_empty_report():
    """An empty report should still return a valid structure."""
    report = ScientificReport(title="Minimal", authors=["A. Silva"])
    full = report.full_report()
    assert "# Minimal" in full
    assert "A. Silva" in full


def test_bibliography_list():
    """bibliography should return list of formatted citations."""
    report = ScientificReport(title="Test", authors=["A. Silva"])
    report.add_reference(
        authors=["Author, A."], title="Test Title",
        year=2023, ref_id="test_ref",
    )
    bib = report.bibliography(style="ieee")
    assert len(bib) == 1
    assert "Test Title" in bib[0]
