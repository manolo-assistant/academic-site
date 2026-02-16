#!/usr/bin/env python3
"""
sync-drive.py — Download data from a unified Google Sheet and generate Hugo content.

Handles tabs: bio, positions, education, publications, talks, conferences, teaching, awards.
Falls back to hardcoded data for tabs not yet in the spreadsheet.

Usage:
  python scripts/sync-drive.py                    # uses default published URLs
  python scripts/sync-drive.py --sheet-id ID      # override with a different sheet
  python scripts/sync-drive.py --image-folder-id ID  # also sync images from Drive
"""

import argparse
import csv
import io
import json
import os
import re
import sys
from pathlib import Path
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError

CONTENT_DIR = Path("content")
DATA_DIR = Path("data")
STATIC_DIR = Path("static/img")

# Default published CSV URLs (from Curriculum_Vitae spreadsheet)
SHEET_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRchAxHUEFwDxDinsba7BZqejlUPdOdiD1jjQv6NAXtEufiZU1_UfPlAAzks4tw3AHUf5h105w-AN-c/pub"
DEFAULT_CSV_URLS = {
    "conferences": f"{SHEET_BASE}?gid=0&single=true&output=csv",
    "talks": f"{SHEET_BASE}?gid=1581332120&single=true&output=csv",
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80]


def download_csv(url: str, label: str = "") -> list[dict]:
    """Download a CSV from a URL and return list of dicts."""
    try:
        with urlopen(url, timeout=30) as resp:
            text = resp.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        rows = [row for row in reader]
        print(f"  Downloaded {label}: {len(rows)} rows")
        return rows
    except URLError as e:
        print(f"  Warning: Could not download {label}: {e}", file=sys.stderr)
        return []


def download_sheet_tab(sheet_id: str, tab_name: str) -> list[dict]:
    """Download a tab from a Google Sheet using gviz endpoint."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={tab_name}"
    return download_csv(url, tab_name)


def download_drive_folder_images(folder_id: str):
    """Download images from a public Google Drive folder."""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    url = (
        f"https://www.googleapis.com/drive/v3/files"
        f"?q=%27{folder_id}%27+in+parents"
        f"&fields=files(id,name,mimeType)"
    )
    try:
        with urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read())
        for f in data.get("files", []):
            if f["mimeType"].startswith("image/"):
                dl_url = f"https://drive.google.com/uc?export=download&id={f['id']}"
                dest = STATIC_DIR / f["name"]
                if not dest.exists():
                    print(f"  Downloading image: {f['name']}")
                    urlretrieve(dl_url, dest)
    except URLError as e:
        print(f"  Warning: Could not list drive folder: {e}", file=sys.stderr)


# ── Hardcoded fallback data (until spreadsheet tabs are created) ──────────

PUBLICATIONS_FALLBACK = [
    {"title": "Sharp bounds on the failure of the hot spots conjecture",
     "authors": "J. de Dios Pont, A.W. Hsu, M.A. Taylor",
     "year": "2025", "journal": "Preprint", "arxiv": "2508.16321", "status": "preprint"},
    {"title": "Convex sets can have interior hot spots",
     "authors": "J. de Dios Pont",
     "year": "2024", "journal": "Preprint", "arxiv": "2412.06344", "status": "preprint"},
    {"title": "Predicting quantum channels over general product distributions",
     "authors": "S. Chen, J. de Dios Pont, J.-T. Hsieh, H.-Y. Huang, J. Lange, J. Li",
     "year": "2024", "journal": "Preprint", "arxiv": "2409.03684", "status": "preprint"},
    {"title": "Periodicity and decidability of translational tilings by rational polygonal sets",
     "authors": "J. de Dios Pont, J. Grebík, R. Greenfeld, J. Madrid",
     "year": "2024", "journal": "Expositiones Mathematicae", "arxiv": "2408.02151", "status": "published"},
    {"title": "Query lower bounds for log-concave sampling",
     "authors": "S. Chewi, J. de Dios Pont, J. Li, C. Lu, S. Narayanan",
     "year": "2024", "journal": "Journal of the ACM, 71(4), 1-42", "arxiv": "2304.02599", "status": "published"},
    {"title": "A new proof of the description of the convex hull of space curves with totally positive torsion",
     "authors": "J. de Dios Pont, P. Ivanisvili, J. Madrid",
     "year": "2025", "journal": "Michigan Mathematical Journal, 1(1), 1-47", "arxiv": "2201.12932", "status": "published"},
    {"title": "Additive energies on discrete cubes",
     "authors": "J. de Dios Pont, R. Greenfeld, P. Ivanisvili, J. Madrid",
     "year": "2023", "journal": "Discrete Analysis", "arxiv": "2112.09352", "status": "published"},
    {"title": "Uniform Fourier Restriction Estimate for Simple Curves of Bounded Frequency",
     "authors": "J. de Dios Pont, H. Jørgen Samuelsen",
     "year": "2023", "journal": "Preprint", "arxiv": "2303.11693", "status": "preprint"},
    {"title": "On classical inequalities for autocorrelations and autoconvolutions",
     "authors": "J. de Dios Pont, J. Madrid",
     "year": "2021", "journal": "Preprint", "arxiv": "2106.13873", "status": "preprint"},
    {"title": "Decoupling for fractal subsets of the parabola",
     "authors": "A. Chang, J. de Dios Pont, R. Greenfeld, A. Jamneshan, Z.K. Li, J. Madrid",
     "year": "2022", "journal": "Mathematische Zeitschrift, 301(2), 1851-1879", "arxiv": "2012.11458", "status": "published"},
    {"title": "On Sparsity in Overparametrised Shallow ReLU Networks",
     "authors": "J. de Dios Pont, J. Bruna",
     "year": "2020", "journal": "Preprint", "arxiv": "2006.10225", "status": "preprint"},
    {"title": "A geometric lemma for complex polynomial curves with applications in Fourier restriction theory",
     "authors": "J. de Dios Pont",
     "year": "2020", "journal": "Preprint", "arxiv": "2003.14140", "status": "preprint"},
    {"title": "Role Detection in Bicycle-Sharing Networks Using Multilayer Stochastic Block Models",
     "authors": "J. Carlen, J. de Dios Pont, C. Mentus, S.-S. Chang, S. Wang, M.A. Porter",
     "year": "2022", "journal": "Network Science, 10(1), 46-81", "arxiv": "1908.09440", "status": "published"},
]

TEACHING_FALLBACK = [
    {"course": "Teaching Assistant", "role": "TA", "institution": "ETH Zurich",
     "term": "2023-2025", "year": "2024", "description": "Various courses during postdoc"},
    {"course": "Teaching Assistant — UCLA Mathematics", "role": "TA", "institution": "UCLA",
     "term": "2018-2023", "year": "2022", "description": "Various undergraduate math courses during PhD"},
]


# ── Content generators ────────────────────────────────────────────────────

def generate_publications(pubs: list[dict]):
    """Generate publication pages from data."""
    out = CONTENT_DIR / "publications"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.md"):
        if f.name != "_index.md":
            f.unlink()

    # Sort by year desc
    pubs_sorted = sorted(pubs, key=lambda p: p.get("year", "0"), reverse=True)

    for pub in pubs_sorted:
        title = pub.get("title", "").strip()
        if not title:
            continue
        authors = pub.get("authors", "")
        year = pub.get("year", "")
        journal = pub.get("journal", "")
        arxiv = pub.get("arxiv", "")
        doi = pub.get("doi", "")
        status = pub.get("status", "")

        links = []
        if arxiv:
            links.append(f"[arXiv:{arxiv}](https://arxiv.org/abs/{arxiv})")
        if doi:
            links.append(f"[DOI]({doi})")

        status_label = ""
        if status == "preprint":
            status_label = "Preprint"
        elif journal:
            status_label = journal

        slug = slugify(title)
        md = f"""---
title: "{title.replace('"', '\\"')}"
date: {year}-01-01
params:
  year: {year}
  status: "{status}"
---

{authors}

*{status_label}*, {year}.

{' · '.join(links)}
"""
        (out / f"{slug}.md").write_text(md)

    print(f"Generated {len(pubs_sorted)} publication pages")


def generate_talks(talks: list[dict]):
    """Generate individual talk pages."""
    out = CONTENT_DIR / "talks"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.md"):
        if f.name != "_index.md":
            f.unlink()

    for row in talks:
        title = row.get("title", "").strip()
        if not title:
            continue
        talk_id = row.get("id", slugify(title))
        event = row.get("event", "")
        url = row.get("url", "")
        abstract = row.get("abstract", "")
        tags = row.get("tags", "")
        date = row.get("date", "")[:10] if row.get("date") else ""
        talk_type = row.get("type", "")

        url_line = f'[Event page]({url})' if url and url != "#" else ""

        md = f"""---
title: "{title.replace('"', '\\"')}"
date: {date or "2020-01-01"}
params:
  type: "{talk_type}"
  event: "{event.replace('"', '\\"')}"
  tags: "{tags}"
---

**{event}**{f" — {talk_type}" if talk_type else ""}, {date}

{url_line}

{("### Abstract" + chr(10) + chr(10) + abstract) if abstract else ""}
"""
        (out / f"{slugify(talk_id)}.md").write_text(md)

    print(f"Generated {len(talks)} talk pages")


def generate_travel(conferences: list[dict]):
    """Generate the travel/conferences list page."""
    out = CONTENT_DIR / "travel"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.md"):
        f.unlink()

    sorted_conf = sorted(conferences, key=lambda r: r.get("date", ""), reverse=True)
    current = [c for c in sorted_conf if c.get("tags", "").strip() == "Current"]
    past = [c for c in sorted_conf if c.get("tags", "").strip() == "Past"]

    lines = ["---", 'title: "Talks & Travel"', "---", ""]
    lines.append("Travel plans and topics for upcoming events. If I'm travelling near you and want to meet, [contact me](mailto:jdedios@nyu.edu)!\n")

    if current:
        lines.append("## Upcoming\n")
        for c in current:
            title = c.get("title", "")
            url = c.get("url", "")
            location = c.get("location", "")
            date = c.get("date", "")
            date_end = c.get("date_end", "")
            link = f"[{title}]({url})" if url and url != "#" else title
            lines.append(f"- **{link}**, {location}. {date} — {date_end}")
        lines.append("")

    if past:
        lines.append("## Past\n")
        for c in past:
            title = c.get("title", "")
            url = c.get("url", "")
            location = c.get("location", "")
            date = c.get("date", "")
            date_end = c.get("date_end", "")
            link = f"[{title}]({url})" if url and url != "#" else title
            lines.append(f"- **{link}**, {location}. {date} — {date_end}")
        lines.append("")

    (out / "_index.md").write_text("\n".join(lines))
    print(f"Generated travel page with {len(conferences)} events")


def generate_teaching(teaching: list[dict]):
    """Generate teaching section."""
    out = CONTENT_DIR / "teaching"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.md"):
        if f.name != "_index.md":
            f.unlink()

    for row in teaching:
        course = row.get("course", "").strip()
        if not course:
            continue
        term = row.get("term", "")
        institution = row.get("institution", "")
        role = row.get("role", "")
        year = row.get("year", "")
        desc = row.get("description", "")
        url = row.get("url", "")
        slug = slugify(f"{course}-{term}")

        md = f"""---
title: "{course.replace('"', '\\"')}"
date: {year}-01-01
params:
  year: {year}
  institution: "{institution}"
  term: "{term}"
---

**{institution}**, {term}. {role}.

{desc}
{f'[Course page]({url})' if url else ''}
"""
        (out / f"{slug}.md").write_text(md)

    print(f"Generated {len(teaching)} teaching entries")


def generate_cv_data(publications, talks, conferences, teaching):
    """Generate JSON data file for LaTeX CV."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cv_data = {
        "publications": publications,
        "talks": [{k: v for k, v in row.items() if k and v} for row in talks],
        "conferences": [{k: v for k, v in row.items() if k and v} for row in conferences],
        "teaching": teaching,
    }
    (DATA_DIR / "cv.json").write_text(json.dumps(cv_data, indent=2, ensure_ascii=False))
    print("Generated data/cv.json for LaTeX CV")


def main():
    parser = argparse.ArgumentParser(description="Sync Google Drive data to Hugo content")
    parser.add_argument("--sheet-id", help="Unified Google Sheet ID (overrides defaults)")
    parser.add_argument("--image-folder-id", help="Google Drive folder ID for images")
    args = parser.parse_args()

    # ── Download data ──
    conferences = []
    talks = []
    publications = []
    teaching = []

    if args.sheet_id:
        # Try downloading all tabs from unified sheet
        print(f"Downloading from unified sheet: {args.sheet_id}")
        conferences = download_sheet_tab(args.sheet_id, "conferences")
        talks = download_sheet_tab(args.sheet_id, "talks")
        publications = download_sheet_tab(args.sheet_id, "publications")
        teaching = download_sheet_tab(args.sheet_id, "teaching")
    else:
        # Use default published CSV URLs
        print("Downloading from published CSV URLs...")
        conferences = download_csv(DEFAULT_CSV_URLS["conferences"], "conferences")
        talks = download_csv(DEFAULT_CSV_URLS["talks"], "talks")

    # Fall back to hardcoded data for missing tabs
    if not publications:
        print("  Using hardcoded publications (add 'publications' tab to spreadsheet)")
        publications = PUBLICATIONS_FALLBACK

    if not teaching:
        print("  Using hardcoded teaching (add 'teaching' tab to spreadsheet)")
        teaching = TEACHING_FALLBACK

    # ── Generate content ──
    print("\nGenerating Hugo content...")
    generate_publications(publications)
    generate_talks(talks)
    generate_travel(conferences)
    generate_teaching(teaching)

    # ── Images ──
    if args.image_folder_id:
        print(f"\nDownloading images from Drive folder: {args.image_folder_id}")
        download_drive_folder_images(args.image_folder_id)

    # ── CV data ──
    generate_cv_data(publications, talks, conferences, teaching)
    print("\nDone!")


if __name__ == "__main__":
    main()
