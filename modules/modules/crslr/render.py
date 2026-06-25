"""
render.py — Markdown/HTML → PDF conversion via WeasyPrint (optional).

Only import this module if weasyprint is installed.
"""

from __future__ import annotations


def render_pdf(html_content: str, output_path: str) -> str:
    """
    Render HTML string to PDF via WeasyPrint.

    Parameters
    ----------
    html_content : str
        Full HTML document string.
    output_path : str
        Path to write the PDF file.

    Returns
    -------
    str
        Absolute path to generated PDF.
    """
    from weasyprint import HTML

    HTML(string=html_content).write_pdf(output_path)
    return output_path


def render_markdown_to_pdf(md_content: str, output_path: str) -> str:
    """
    Convert Markdown → HTML → PDF.

    Requires `markdown` and `weasyprint` packages.
    """
    import markdown as md_lib

    html = md_lib.markdown(md_content, extensions=["extra", "tables"])
    return render_pdf(html, output_path)
