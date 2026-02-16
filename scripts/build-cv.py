#!/usr/bin/env python3
"""
build-cv.py — Generate a LaTeX CV from data/cv.json and compile to PDF.

Reads the template from cv/templates/cv.tex, replaces marker sections
with actual data from cv.json, compiles with pdflatex, and copies
the result to static/cv.pdf so Hugo can serve it.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def tex_escape(s: str) -> str:
    """Escape special LaTeX characters."""
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s


def build_publications_tex(pubs: list[dict]) -> str:
    if not pubs:
        return "\\section{Publications \\& Preprints}\n\\textit{See Google Scholar for a full list.}\n"
    lines = ["\\section{Publications \\& Preprints}", "\\begin{itemize}[leftmargin=*, nosep]"]
    for p in pubs:
        title = tex_escape(p.get("title", ""))
        authors = tex_escape(p.get("authors", ""))
        journal = tex_escape(p.get("journal", ""))
        year = p.get("year", "")
        lines.append(f"  \\item {authors}. \\textit{{{title}}}. {journal}, {year}.")
    lines.append("\\end{itemize}")
    return "\n".join(lines)


def build_talks_tex(talks: list[dict]) -> str:
    if not talks:
        return "\\section{Selected Talks}\n\\textit{List available upon request.}\n"
    lines = ["\\section{Selected Talks}", "\\begin{itemize}[leftmargin=*, nosep]"]
    for t in talks:
        title = tex_escape(t.get("title", ""))
        venue = tex_escape(t.get("venue", ""))
        date = t.get("date", "")
        lines.append(f"  \\item \\textit{{{title}}}. {venue}, {date}.")
    lines.append("\\end{itemize}")
    return "\n".join(lines)


def build_teaching_tex(teaching: list[dict]) -> str:
    if not teaching:
        return "\\section{Teaching}\n\\textit{Details available upon request.}\n"
    lines = ["\\section{Teaching}", "\\begin{itemize}[leftmargin=*, nosep]"]
    for t in teaching:
        course = tex_escape(t.get("course", ""))
        term = t.get("term", "")
        institution = tex_escape(t.get("institution", ""))
        role = t.get("role", "")
        lines.append(f"  \\item \\textbf{{{course}}}, {institution}, {term}. {role}.")
    lines.append("\\end{itemize}")
    return "\n".join(lines)


def main():
    data_file = Path("data/cv.json")
    template = Path("cv/templates/cv.tex")
    output_dir = Path("cv/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    if data_file.exists():
        data = json.loads(data_file.read_text())
    else:
        data = {"publications": [], "talks": [], "teaching": []}

    # Read template
    tex = template.read_text()

    # Replace sections
    tex = re.sub(
        r"% PUBLICATIONS_START.*?% PUBLICATIONS_END",
        build_publications_tex(data.get("publications", [])),
        tex,
        flags=re.DOTALL,
    )
    tex = re.sub(
        r"% TALKS_START.*?% TALKS_END",
        build_talks_tex(data.get("talks", [])),
        tex,
        flags=re.DOTALL,
    )
    tex = re.sub(
        r"% TEACHING_START.*?% TEACHING_END",
        build_teaching_tex(data.get("teaching", [])),
        tex,
        flags=re.DOTALL,
    )

    # Write processed .tex
    processed = output_dir / "cv.tex"
    processed.write_text(tex)

    # Compile
    try:
        for _ in range(2):  # Run twice for references
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(output_dir), str(processed)],
                check=True,
                capture_output=True,
            )
        pdf = output_dir / "cv.pdf"
        if pdf.exists():
            static = Path("static")
            static.mkdir(exist_ok=True)
            shutil.copy(pdf, static / "cv.pdf")
            print(f"CV generated: static/cv.pdf")
        else:
            print("Warning: PDF was not generated", file=sys.stderr)
    except FileNotFoundError:
        print("Warning: pdflatex not found. Skipping PDF generation.", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Warning: pdflatex failed: {e.stderr[:500] if e.stderr else 'unknown error'}", file=sys.stderr)


if __name__ == "__main__":
    main()
