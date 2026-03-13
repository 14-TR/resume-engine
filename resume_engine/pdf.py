"""PDF output via pandoc -- converts markdown to PDF with a clean resume style."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

# Common LaTeX binary locations (macOS BasicTeX, MacTeX, Linux)
_TEX_PATHS = [
    "/Library/TeX/texbin",
    "/usr/local/texlive/bin",
    "/usr/bin",
    "/usr/local/bin",
]

LATEX_HEADER = r"""
\usepackage{geometry}
\geometry{margin=1in}
\usepackage{parskip}
\setlength{\parskip}{4pt}
\usepackage{titlesec}
\titlespacing\section{0pt}{8pt}{4pt}
\titlespacing\subsection{0pt}{6pt}{2pt}
\titleformat{\section}{\large\bfseries}{}{0em}{}[\titlerule]
\usepackage{enumitem}
\setlist[itemize]{noitemsep, topsep=2pt}
\pagestyle{empty}
"""


def _build_env() -> dict:
    """Return env with common TeX binary dirs added to PATH."""
    env = os.environ.copy()
    extra = ":".join(_TEX_PATHS)
    env["PATH"] = extra + ":" + env.get("PATH", "")
    return env


def markdown_to_pdf(markdown_path: str, output_path: str) -> str:
    """
    Convert a markdown file to PDF using pandoc.

    Requires pandoc (brew install pandoc) and a LaTeX engine.
    On macOS, install BasicTeX: brew install basictex

    Args:
        markdown_path: Path to the input markdown file.
        output_path: Path for the output PDF file.

    Returns:
        The resolved output path.

    Raises:
        RuntimeError: If pandoc is not installed or conversion fails.
    """
    env = _build_env()
    pandoc_bin = shutil.which("pandoc", path=env["PATH"])
    if not pandoc_bin:
        raise RuntimeError(
            "pandoc is not installed.\n"
            "Install it with: brew install pandoc\n"
            "On Linux: sudo apt install pandoc"
        )

    # Write a temporary LaTeX header for nicer resume formatting
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".tex", delete=False, prefix="resume_header_"
    ) as hf:
        hf.write(LATEX_HEADER)
        header_path = hf.name

    try:
        # Try pdflatex first (available with BasicTeX), fall back to plain pandoc
        pdflatex = shutil.which("pdflatex", path=env["PATH"])

        base_cmd = [pandoc_bin, markdown_path, "-o", output_path, "--standalone"]
        if pdflatex:
            base_cmd += [
                f"--pdf-engine={pdflatex}",
                f"--include-in-header={header_path}",
                "-V",
                "fontsize=11pt",
            ]

        result = subprocess.run(base_cmd, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            raise RuntimeError(
                f"pandoc PDF conversion failed:\n{result.stderr}\n\n"
                "Ensure a LaTeX engine is installed:\n"
                "  macOS: brew install basictex\n"
                "  Linux: sudo apt install texlive-latex-base"
            )

        return os.path.abspath(output_path)
    finally:
        try:
            os.unlink(header_path)
        except OSError:
            pass


def md_path_to_pdf_path(md_path: str) -> str:
    """Given a .md output path, return the equivalent .pdf path."""
    p = Path(md_path)
    return str(p.with_suffix(".pdf"))
