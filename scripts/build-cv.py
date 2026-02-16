#!/usr/bin/env python3
"""
build-cv.py — Generate a LaTeX CV from data/cv.json and compile to PDF.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def tex_escape(s: str) -> str:
    for old, new in [("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                     ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                     ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")]:
        s = s.replace(old, new)
    return s


def build_publications_tex(pubs: list[dict]) -> str:
    if not pubs:
        return "\\section{Publications \\& Preprints}\n\\textit{See Google Scholar for a full list.}\n"
    lines = ["\\section{Publications \\& Preprints}", "\\begin{itemize}[leftmargin=*, nosep]"]
    for p in sorted(pubs, key=lambda x: x.get("year", "0"), reverse=True):
        title = tex_escape(p.get("title", ""))
        authors = tex_escape(p.get("authors", ""))
        journal = tex_escape(p.get("journal", ""))
        year = p.get("year", "")
        arxiv = p.get("arxiv", "")
        arxiv_ref = f" \\href{{https://arxiv.org/abs/{arxiv}}}{{arXiv:{tex_escape(arxiv)}}}" if arxiv else ""
        lines.append(f"  \\item {authors}. \\textit{{{title}}}. {journal}, {year}.{arxiv_ref}")
    lines.append("\\end{itemize}")
    return "\n".join(lines)


def build_talks_tex(talks: list[dict]) -> str:
    if not talks:
        return "\\section{Selected Talks}\n\\textit{See website for full list.}\n"
    lines = ["\\section{Selected Talks}", "\\begin{itemize}[leftmargin=*, nosep]"]
    seen_titles = set()
    for t in sorted(talks, key=lambda x: x.get("date", ""), reverse=True):
        title = t.get("title", "")
        if title in seen_titles:
            continue
        seen_titles.add(title)
        event = tex_escape(t.get("event", ""))
        date = t.get("date", "")[:10]
        lines.append(f"  \\item \\textit{{{tex_escape(title)}}}. {event}, {date}.")
    lines.append("\\end{itemize}")
    return "\n".join(lines)


def build_conferences_tex(conferences: list[dict]) -> str:
    if not conferences:
        return ""
    lines = ["\\section{Conferences \\& Workshops (selected)}", "\\begin{itemize}[leftmargin=*, nosep]"]
    for c in sorted(conferences, key=lambda x: x.get("date", ""), reverse=True)[:15]:
        title = tex_escape(c.get("title", ""))
        location = tex_escape(c.get("location", ""))
        date = c.get("date", "")
        lines.append(f"  \\item {title}, {location}, {date}.")
    lines.append("\\end{itemize}")
    return "\n".join(lines)


def main():
    data_file = Path("data/cv.json")
    template = Path("cv/templates/cv.tex")
    output_dir = Path("cv/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(data_file.read_text()) if data_file.exists() else {}

    tex = template.read_text()

    pub_tex = build_publications_tex(data.get("publications", []))
    talks_tex = build_talks_tex(data.get("talks", []))
    conf_tex = build_conferences_tex(data.get("conferences", []))

    tex = re.sub(r"% PUBLICATIONS_START.*?% PUBLICATIONS_END",
                 lambda m: pub_tex, tex, flags=re.DOTALL)
    tex = re.sub(r"% TALKS_START.*?% TALKS_END",
                 lambda m: talks_tex, tex, flags=re.DOTALL)
    tex = re.sub(r"% TEACHING_START.*?% TEACHING_END",
                 lambda m: conf_tex, tex, flags=re.DOTALL)

    processed = output_dir / "cv.tex"
    processed.write_text(tex)

    try:
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(output_dir), str(processed)],
                check=True, capture_output=True,
            )
        pdf = output_dir / "cv.pdf"
        if pdf.exists():
            Path("static").mkdir(exist_ok=True)
            shutil.copy(pdf, Path("static/cv.pdf"))
            print(f"CV generated: static/cv.pdf")
    except FileNotFoundError:
        print("Warning: pdflatex not found.", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Warning: pdflatex failed: {e.stderr[:500] if e.stderr else ''}", file=sys.stderr)


if __name__ == "__main__":
    main()
