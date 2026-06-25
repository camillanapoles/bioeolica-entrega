#!/usr/bin/env python3
"""
Scientific Writing Module — Methodology, Results, Citations, Bibliography.

Generates publication-ready content for engineering papers:
  - Methodology section text from analysis parameters
  - Results tables formatted for journal publication (LaTeX compatible)
  - Reference tracking with IEEE and ABNT citation formats
  - BibTeX generation for bibliography management

Usage:
    from scientific_writing import ScientificReport

    report = ScientificReport(
        title="Mechanical Characterization of Paper Mache Composites",
        authors=["Silva, A.", "Santos, B."],
    )

    # Generate methodology from test parameters
    meth = report.methodology_section(
        test_type="3-point bending",
        standard="ASTM D790",
        params={"span_mm": 80, "width_mm": 25, "thickness_mm": 5,
                "speed_mm_min": 2.0, "n_samples": 5}
    )

    # Format results table
    table = report.results_table(
        headers=["Sample", "E (GPa)", "Strength (MPa)", "Strain (%)"],
        rows=[
            ["PM-01", 2.45, 28.3, 1.52],
            ["PM-02", 2.52, 29.1, 1.48],
            ["PM-03", 2.38, 27.8, 1.55],
        ],
        caption="Flexural test results for paper mache composite."
    )

    # Add and format citations
    report.add_reference(
        authors=["ASTM International"],
        title="ASTM D790: Standard Test Methods for Flexural Properties",
        year=2020,
        doi="10.1520/D0790-17",
    )
    citation = report.citation_format("astm_d790", style="ieee")
    bibtex = report.generate_bibtex()

    print(table["latex"])
    print(report.full_report())
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
#  METHODOLOGY SECTION GENERATOR
# ═══════════════════════════════════════════════════════════════

METHODOLOGY_TEMPLATES = {
    "3-point bending": (
        "Three-point bending tests were conducted according to {standard}. "
        "Specimens with dimensions {width_mm} mm x {thickness_mm} mm "
        "(width x thickness) and a span length of {span_mm} mm were used, "
        "giving a span-to-thickness ratio of {span_ratio:.1f}. "
        "Tests were performed at a crosshead speed of {speed_mm_min} mm/min "
        "using a universal testing machine. "
        "A total of {n_samples} specimens were tested for each condition. "
        "The flexural modulus was calculated from the initial linear portion "
        "of the stress-strain curve, and the flexural strength was determined "
        "at the maximum load according to ASTM D790 equations."
    ),
    "tensile": (
        "Tensile tests were performed following {standard}. "
        "Dog-bone specimens with a gauge length of {gauge_length_mm} mm, "
        "width of {width_mm} mm, and thickness of {thickness_mm} mm were tested. "
        "The crosshead speed was set to {speed_mm_min} mm/min. "
        "Strain was measured using an extensometer with {extensometer_mm} mm gauge length. "
        "A minimum of {n_samples} specimens per condition were tested. "
        "Tensile modulus was determined from the linear elastic region "
        "(0.05--0.25% strain), and ultimate tensile strength was recorded "
        "at the maximum load before failure."
    ),
    "compression": (
        "Compression tests were carried out in accordance with {standard}. "
        "Rectangular specimens measuring {width_mm} mm x {thickness_mm} mm "
        "in cross-section with a gauge length of {gauge_length_mm} mm were used. "
        "The test speed was {speed_mm_min} mm/min. "
        "Anti-buckling guides were employed to prevent Euler buckling "
        "during compression. "
        "Compressive modulus and strength were determined from "
        "{n_samples} replicate specimens."
    ),
    "fatigue": (
        "Fatigue tests were conducted using a servo-hydraulic testing machine "
        "following {standard}. "
        "Tests were performed under load control at a stress ratio of R = {stress_ratio} "
        "and a frequency of {frequency_Hz} Hz. "
        "The maximum stress was varied between {stress_min_MPa} MPa and "
        "{stress_max_MPa} MPa. "
        "A run-out limit of {runout_cycles} cycles was defined. "
        "S-N curves were constructed from tests on {n_samples} specimens "
        "per stress level."
    ),
    "cfd": (
        "Computational fluid dynamics simulations were performed using "
        "the finite volume method. "
        "The computational domain extended {domain_size} diameters in each direction. "
        "A mesh with approximately {mesh_elements} elements was generated, "
        "with refinement near the walls to achieve y+ < {yplus_target}. "
        "The {turbulence_model} turbulence model was employed. "
        "Boundary conditions consisted of velocity inlet at {inlet_velocity_ms} m/s "
        "and pressure outlet. "
        "Steady-state simulations were run until residuals fell below {convergence_criterion}."
    ),
    "fem": (
        "Finite element analysis was conducted using {solver_name}. "
        "The model was meshed with {element_type} elements, "
        "totaling approximately {mesh_elements} elements. "
        "A mesh convergence study was performed with {n_mesh_levels} refinement levels. "
        "Boundary conditions were applied as follows: {boundary_conditions}. "
        "Material properties were assigned as per {material_model}. "
        "The analysis considered {analysis_type} with geometric nonlinearity "
        "enabled where applicable."
    ),
}


METHODOLOGY_TEMPLATES_PT = {
    "3-point bending": (
        "Os ensaios de flexao de tres pontos foram realizados de acordo com a {standard}. "
        "Corpos de prova com dimensoes {width_mm} mm x {thickness_mm} mm "
        "(largura x espessura) e vao de {span_mm} mm foram utilizados, "
        "resultando em uma relacao vao-espessura de {span_ratio:.1f}. "
        "Os ensaios foram conduzidos a velocidade de {speed_mm_min} mm/min "
        "em maquina universal de ensaios. "
        "Foram testados {n_samples} corpos de prova para cada condicao. "
        "O modulo de flexao foi calculado a partir da regiao linear inicial "
        "da curva tensao-deformacao, e a resistencia a flexao foi determinada "
        "na carga maxima de acordo com as equacoes da ASTM D790."
    ),
    "tensile": (
        "Os ensaios de tracao foram realizados conforme a {standard}. "
        "Corpos de prova tipo osso com comprimento util de {gauge_length_mm} mm, "
        "largura de {width_mm} mm e espessura de {thickness_mm} mm foram testados. "
        "A velocidade de ensaio foi de {speed_mm_min} mm/min. "
        "A deformacao foi medida com extensometro de {extensometer_mm} mm. "
        "Foram testados no minimo {n_samples} corpos de prova por condicao."
    ),
}


# ═══════════════════════════════════════════════════════════════
#  RESULTS TABLE FORMATTER
# ═══════════════════════════════════════════════════════════════

def format_results_table(
    headers: List[str],
    rows: List[List],
    caption: str = "",
    label: str = "",
    fmt: str = "latex",
    decimal_places: int = 2,
) -> Dict:
    """Format results data into publication-ready tables.

    Args:
        headers: Column header strings
        rows: List of rows, each a list of values
        caption: Table caption (for LaTeX)
        label: Cross-reference label (e.g., 'tab:flexure')
        fmt: Output format: 'latex', 'markdown', 'csv'
        decimal_places: Rounding for numeric values

    Returns:
        Dict with formatted table string and format metadata.
    """
    formatted_rows = []
    for row in rows:
        formatted_row = []
        for val in row:
            if isinstance(val, (int, float, np.integer, np.floating)):
                formatted_row.append(f"{val:.{decimal_places}f}")
            else:
                formatted_row.append(str(val))
        formatted_rows.append(formatted_row)

    n_cols = len(headers)

    result = {}

    if fmt == "latex":
        col_format = "l" + "c" * (n_cols - 1)
        lines = [
            "\\begin{table}[htbp]",
            "\\centering",
            f"\\caption{{{caption}}}",
            f"\\label{{{label}}}",
            "\\begin{tabular}{" + col_format + "}",
            "\\toprule",
            " & ".join(headers) + " \\\\",
            "\\midrule",
        ]
        for row in formatted_rows:
            lines.append(" & ".join(row) + " \\\\")
        lines.extend([
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
        ])
        result["latex"] = "\n".join(lines)

    elif fmt == "markdown":
        lines = [
            f"Table: {caption}" if caption else "",
        ]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * n_cols) + " |")
        for row in formatted_rows:
            lines.append("| " + " | ".join(row) + " |")
        result["markdown"] = "\n".join(lines)

    elif fmt == "csv":
        import io
        buf = io.StringIO()
        buf.write(",".join(headers) + "\n")
        for row in formatted_rows:
            buf.write(",".join(row) + "\n")
        result["csv"] = buf.getvalue()

    result["headers"] = headers
    result["n_rows"] = len(rows)
    result["n_cols"] = n_cols
    result["format"] = fmt
    result["caption"] = caption
    result["label"] = label

    return result


# ═══════════════════════════════════════════════════════════════
#  REFERENCE / CITATION SYSTEM
# ═══════════════════════════════════════════════════════════════

@dataclass
class Reference:
    """Scholarly reference entry.

    Args:
        ref_id: Unique identifier for cross-referencing
        authors: List of author names
        title: Full title
        year: Publication year
        journal: Journal name (for articles)
        volume: Volume number
        number: Issue/number
        pages: Page range string
        publisher: Publisher name (for books/standards)
        doi: Digital Object Identifier
        url: URL
        ref_type: 'article', 'book', 'standard', 'proceedings',
                 'thesis', 'report', 'manual'
    """
    ref_id: str
    authors: List[str]
    title: str
    year: int
    journal: str = ""
    volume: str = ""
    number: str = ""
    pages: str = ""
    publisher: str = ""
    doi: str = ""
    url: str = ""
    ref_type: str = "article"


# IEEE citation formatting
def _format_ieee(ref: Reference) -> str:
    """Format a reference in IEEE style.

    IEEE: [1] A. Author and B. Author, "Title," Journal, vol. X,
          no. Y, pp. Z, year.
    """
    # Authors
    author_str = ", ".join(ref.authors)
    if len(ref.authors) > 3:
        author_str = ", ".join(ref.authors[:3]) + ", et al."

    if ref.ref_type == "standard":
        return (
            f"{author_str}, \"{ref.title},\" {ref.publisher}, "
            f"{ref.year}."
        )
    elif ref.ref_type == "book":
        return (
            f"{author_str}, \"{ref.title},\" "
            f"{ref.publisher}, {ref.year}."
        )
    elif ref.ref_type == "manual":
        return (
            f"{author_str}, \"{ref.title},\" {ref.publisher}, "
            f"{ref.year}."
        )
    else:
        parts = [f"{author_str}, \"{ref.title},\""]
        if ref.journal:
            parts.append(f" {ref.journal},")
        if ref.volume:
            parts.append(f" vol. {ref.volume},")
        if ref.number:
            parts.append(f" no. {ref.number},")
        if ref.pages:
            parts.append(f" pp. {ref.pages},")
        parts.append(f" {ref.year}.")
        return " ".join(parts)


# ABNT NBR 6023 citation formatting
def _format_abnt(ref: Reference) -> str:
    """Format a reference in ABNT NBR 6023 style.

    ABNT: AUTHOR. Title. Edition. City: Publisher, year.
    """
    # Authors (last name first)
    author_abnt = []
    for author in ref.authors:
        parts = author.split(", ")
        if len(parts) == 2:
            author_abnt.append(f"{parts[0].upper()}, {parts[1]}")
        else:
            author_abnt.append(author.upper())

    author_str = "; ".join(author_abnt)

    if ref.ref_type == "standard":
        return (
            f"{author_str}. {ref.title}. {ref.publisher}, "
            f"{ref.year}."
        )
    elif ref.ref_type == "book":
        return (
            f"{author_str}. {ref.title}. {ref.publisher}, "
            f"{ref.year}."
        )
    else:
        journal_part = f" {ref.journal}," if ref.journal else ""
        vol_part = f" v. {ref.volume}," if ref.volume else ""
        pages_part = f" p. {ref.pages}," if ref.pages else ""
        return (
            f"{author_str}. {ref.title}.{journal_part}{vol_part}"
            f"{pages_part} {ref.year}."
        )


# ═══════════════════════════════════════════════════════════════
#  SCIENTIFIC REPORT CLASS
# ═══════════════════════════════════════════════════════════════

@dataclass
class ScientificReport:
    """Generate publication-ready scientific content.

    Manages document metadata, methodology sections, results tables,
    and reference bibliography for engineering papers and reports.

    Args:
        title: Document title
        authors: List of author names
        abstract: Abstract text (optional)
        keywords: List of keywords (optional)
        language: 'en' or 'pt'
    """
    title: str
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    language: str = "en"
    _references: Dict[str, Reference] = field(default_factory=dict)
    _tables: List[Dict] = field(default_factory=list)
    _methodology_sections: List[str] = field(default_factory=list)

    def add_reference(
        self,
        authors: List[str],
        title: str,
        year: int,
        ref_id: str = "",
        journal: str = "",
        volume: str = "",
        number: str = "",
        pages: str = "",
        publisher: str = "",
        doi: str = "",
        url: str = "",
        ref_type: str = "article",
    ) -> str:
        """Add a reference to the document's bibliography.

        Args:
            authors: List of authors
            title: Full title
            year: Publication year
            ref_id: Short ID for citation. Auto-generated if empty.
            journal: Journal name
            volume: Volume number
            number: Issue number
            pages: Page range
            publisher: Publisher name
            doi: Digital Object Identifier
            url: URL
            ref_type: Type: 'article', 'book', 'standard', 'thesis', etc.

        Returns:
            The ref_id assigned to this reference.
        """
        if not ref_id:
            # Generate from first author's last name + short title
            first_author = authors[0].split(",")[0].strip().lower()
            short_title = title.split(":")[0].split(".")[0].lower()
            short_title = "".join(c for c in short_title if c.isalnum() or c == "_")
            ref_id = f"{first_author}_{short_title[:30]}_{year}"

        self._references[ref_id] = Reference(
            ref_id=ref_id,
            authors=authors,
            title=title,
            year=year,
            journal=journal,
            volume=volume,
            number=number,
            pages=pages,
            publisher=publisher,
            doi=doi,
            url=url,
            ref_type=ref_type,
        )
        return ref_id

    def citation_format(self, ref_id: str, style: str = "ieee") -> str:
        """Format a single reference in the specified citation style.

        Args:
            ref_id: Reference identifier
            style: 'ieee' or 'abnt'

        Returns:
            Formatted citation string.
        """
        ref = self._references.get(ref_id)
        if ref is None:
            return f"[missing reference: {ref_id}]"

        if style == "abnt":
            return _format_abnt(ref)
        return _format_ieee(ref)

    def methodology_section(
        self,
        test_type: str,
        standard: str,
        params: Dict,
        template_key: Optional[str] = None,
    ) -> str:
        """Generate a methodology section paragraph.

        Args:
            test_type: Type of test (e.g. '3-point bending', 'tensile')
            standard: Applicable standard (e.g. 'ASTM D790')
            params: Dict of parameters for template filling
            template_key: Force a specific template key. Auto-detected
                         from test_type if None.

        Returns:
            Formatted methodology paragraph.
        """
        if template_key is None:
            lower_type = test_type.lower().strip()
            if "3-point" in lower_type or "flex" in lower_type or "bend" in lower_type:
                template_key = "3-point bending"
            elif "tensile" in lower_type or "tracao" in lower_type:
                template_key = "tensile"
            elif "compress" in lower_type:
                template_key = "compression"
            elif "fatigue" in lower_type or "fadiga" in lower_type:
                template_key = "fatigue"
            elif "cfd" in lower_type or "fluid" in lower_type:
                template_key = "cfd"
            elif "fem" in lower_type or "finite" in lower_type:
                template_key = "fem"

        templates = METHODOLOGY_TEMPLATES_PT if self.language == "pt" else METHODOLOGY_TEMPLATES
        template = templates.get(template_key, METHODOLOGY_TEMPLATES["3-point bending"])

        # Ensure standard and n_samples are in params
        fill_params = dict(params)
        fill_params["standard"] = standard
        if "n_samples" not in fill_params:
            fill_params["n_samples"] = 5

        # Compute span ratio if applicable
        if "span_mm" in fill_params and "thickness_mm" in fill_params:
            if fill_params["thickness_mm"] > 0:
                fill_params["span_ratio"] = fill_params["span_mm"] / fill_params["thickness_mm"]
            else:
                fill_params["span_ratio"] = 16.0

        try:
            text = template.format(**fill_params)
        except KeyError as e:
            text = (
                f"{test_type} tests were conducted following {standard}. "
                f"Details: {params}. "
                f"[Template missing parameter: {e}]"
            )

        self._methodology_sections.append(text)

        # Also add the standard as a reference if not already present
        std_ref_id = standard.lower().replace(" ", "_").replace(".", "")
        if std_ref_id not in self._references and standard:
            self.add_reference(
                authors=[standard.split(" ")[0]],
                title=standard,
                year=2020,
                ref_id=std_ref_id,
                publisher="Standards Organization",
                ref_type="standard",
            )

        return text

    def results_table(
        self,
        headers: List[str],
        rows: List[List],
        caption: str = "",
        label: str = "",
        fmt: str = "latex",
    ) -> Dict:
        """Generate and store a formatted results table.

        Args:
            headers: Column headers
            rows: Data rows
            caption: Table caption
            label: Table label
            fmt: 'latex', 'markdown', or 'csv'

        Returns:
            Dict with formatted table and metadata.
        """
        if not label:
            label = f"tab:{headers[0].lower().replace(' ', '_')}" if headers else "tab:results"

        table = format_results_table(
            headers=headers,
            rows=rows,
            caption=caption,
            label=label,
            fmt=fmt,
        )
        self._tables.append(table)
        return table

    def generate_bibtex(self) -> str:
        """Generate BibTeX bibliography from stored references.

        Returns:
            BibTeX formatted string.
        """
        entries = []
        for ref_id, ref in self._references.items():
            entry_type = {
                "article": "article",
                "book": "book",
                "standard": "misc",
                "proceedings": "inproceedings",
                "thesis": "phdthesis",
                "report": "techreport",
                "manual": "manual",
            }.get(ref.ref_type, "misc")

            lines = [f"@{entry_type}{{{ref_id},"]
            lines.append(f"  author = {{{' and '.join(ref.authors)}}},")
            lines.append(f"  title = {{{ref.title}}},")
            lines.append(f"  year = {{{ref.year}}},")
            if ref.journal:
                lines.append(f"  journal = {{{ref.journal}}},")
            if ref.volume:
                lines.append(f"  volume = {{{ref.volume}}},")
            if ref.number:
                lines.append(f"  number = {{{ref.number}}},")
            if ref.pages:
                lines.append(f"  pages = {{{ref.pages}}},")
            if ref.publisher:
                lines.append(f"  publisher = {{{ref.publisher}}},")
            if ref.doi:
                lines.append(f"  doi = {{{ref.doi}}},")
            if ref.url:
                lines.append(f"  url = {{{ref.url}}},")
            lines.append("}")
            entries.append("\n".join(lines))

        return "\n\n".join(entries)

    def bibliography(self, style: str = "ieee") -> List[str]:
        """Generate formatted bibliography list.

        Args:
            style: 'ieee' or 'abnt'

        Returns:
            List of formatted citation strings.
        """
        return [
            self.citation_format(ref_id, style=style)
            for ref_id in self._references
        ]

    def full_report(self) -> str:
        """Generate complete structured report as text.

        Combines title, authors, abstract, methodology sections,
        tables, and bibliography into a single formatted document.

        Returns:
            Full report string.
        """
        sections = []
        sections.append(f"# {self.title}")
        sections.append("")
        sections.append(f"**Authors:** {', '.join(self.authors)}")
        sections.append("")

        if self.abstract:
            sections.append("## Abstract")
            sections.append(self.abstract)
            sections.append("")

        if self.keywords:
            sections.append("**Keywords:** " + ", ".join(self.keywords))
            sections.append("")

        if self._methodology_sections:
            sections.append("## Methodology")
            for sec in self._methodology_sections:
                sections.append(sec)
                sections.append("")

        if self._tables:
            sections.append("## Results")
            for table in self._tables:
                tbl_fmt = table.get("markdown") or table.get("latex") or ""
                sections.append(tbl_fmt)
                sections.append("")

        if self._references:
            sections.append("## References")
            for i, (ref_id, ref) in enumerate(self._references.items(), 1):
                ieee = self.citation_format(ref_id, style="ieee")
                sections.append(f"[{i}] {ieee}")
            sections.append("")

        return "\n".join(sections)
