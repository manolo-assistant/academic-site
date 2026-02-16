#!/usr/bin/env python3
"""
sync-drive.py — Download data from a public Google Drive folder and generate Hugo content.

Architecture:
  1. Downloads a Google Sheet (published as CSV) with structured data
  2. Downloads images from a public Drive folder
  3. Generates Hugo markdown files from the data
  4. Generates a JSON data file for the LaTeX CV

Usage:
  python scripts/sync-drive.py --sheet-id SHEET_ID --image-folder-id FOLDER_ID

The Google Sheet should have tabs named: publications, talks, teaching, bio
Each tab becomes a content section. The sheet must be "published to the web" as CSV.

For the MWE, if no IDs are provided, it generates placeholder content.
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


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80]


def download_sheet_tab(sheet_id: str, tab_name: str) -> list[dict]:
    """Download a single tab from a published Google Sheet as CSV."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={tab_name}"
    try:
        with urlopen(url, timeout=30) as resp:
            text = resp.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        return list(reader)
    except URLError as e:
        print(f"Warning: Could not download tab '{tab_name}': {e}", file=sys.stderr)
        return []


def download_drive_folder_images(folder_id: str):
    """Download images from a public Google Drive folder.
    
    Uses the Drive API v3 (no auth needed for public folders).
    """
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    url = (
        f"https://www.googleapis.com/drive/v3/files"
        f"?q=%27{folder_id}%27+in+parents"
        f"&fields=files(id,name,mimeType)"
        f"&key=none"  # Public folder — API key optional for truly public files
    )
    try:
        with urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read())
        for f in data.get("files", []):
            if f["mimeType"].startswith("image/"):
                dl_url = f"https://drive.google.com/uc?export=download&id={f['id']}"
                dest = STATIC_DIR / f["name"]
                if not dest.exists():
                    print(f"Downloading image: {f['name']}")
                    urlretrieve(dl_url, dest)
    except URLError as e:
        print(f"Warning: Could not list drive folder: {e}", file=sys.stderr)


def generate_publications(rows: list[dict]):
    out = CONTENT_DIR / "publications"
    out.mkdir(parents=True, exist_ok=True)
    # Remove old generated files
    for f in out.glob("*.md"):
        if f.name != "_index.md":
            f.unlink()

    for row in rows:
        title = row.get("title", "").strip()
        if not title:
            continue
        authors = row.get("authors", "")
        year = row.get("year", "")
        journal = row.get("journal", "")
        arxiv = row.get("arxiv", "")
        doi = row.get("doi", "")
        slug = slugify(title)

        links = []
        if arxiv:
            links.append(f"[arXiv]({arxiv})")
        if doi:
            links.append(f"[DOI]({doi})")

        md = f"""---
title: "{title}"
params:
  year: {year}
---

{authors}. *{journal}*, {year}.

{' · '.join(links)}
"""
        (out / f"{slug}.md").write_text(md)
    print(f"Generated {len(rows)} publications")


def generate_talks(rows: list[dict]):
    out = CONTENT_DIR / "talks"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.md"):
        if f.name != "_index.md":
            f.unlink()

    for row in rows:
        title = row.get("title", "").strip()
        if not title:
            continue
        venue = row.get("venue", "")
        date = row.get("date", "")
        location = row.get("location", "")
        year = row.get("year", date[:4] if len(date) >= 4 else "")
        slug = slugify(f"{title}-{venue}")

        md = f"""---
title: "{title}"
params:
  year: {year}
---

**{venue}**, {date}, {location}.
"""
        (out / f"{slug}.md").write_text(md)
    print(f"Generated {len(rows)} talks")


def generate_teaching(rows: list[dict]):
    out = CONTENT_DIR / "teaching"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.md"):
        if f.name != "_index.md":
            f.unlink()

    for row in rows:
        course = row.get("course", "").strip()
        if not course:
            continue
        term = row.get("term", "")
        institution = row.get("institution", "")
        role = row.get("role", "")
        year = row.get("year", "")
        slug = slugify(f"{course}-{term}")

        md = f"""---
title: "{course} — {term}"
params:
  year: {year}
---

**{institution}**, {term}. {role}.
"""
        (out / f"{slug}.md").write_text(md)
    print(f"Generated {len(rows)} teaching entries")


def generate_cv_data(publications, talks, teaching):
    """Generate a JSON file that the LaTeX CV template reads."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cv_data = {
        "publications": publications,
        "talks": talks,
        "teaching": teaching,
    }
    (DATA_DIR / "cv.json").write_text(json.dumps(cv_data, indent=2))
    print("Generated data/cv.json for LaTeX CV")


def main():
    parser = argparse.ArgumentParser(description="Sync Google Drive data to Hugo content")
    parser.add_argument("--sheet-id", help="Google Sheet ID (must be published to web)")
    parser.add_argument("--image-folder-id", help="Google Drive folder ID for images")
    args = parser.parse_args()

    publications, talks, teaching = [], [], []

    if args.sheet_id:
        print(f"Downloading from Google Sheet: {args.sheet_id}")
        publications = download_sheet_tab(args.sheet_id, "publications")
        talks = download_sheet_tab(args.sheet_id, "talks")
        teaching = download_sheet_tab(args.sheet_id, "teaching")

        if publications:
            generate_publications(publications)
        if talks:
            generate_talks(talks)
        if teaching:
            generate_teaching(teaching)
    else:
        print("No --sheet-id provided. Using existing placeholder content.")

    if args.image_folder_id:
        print(f"Downloading images from Drive folder: {args.image_folder_id}")
        download_drive_folder_images(args.image_folder_id)
    else:
        print("No --image-folder-id provided. Skipping image sync.")

    # Always generate CV data (from downloaded or empty)
    generate_cv_data(publications, talks, teaching)


if __name__ == "__main__":
    main()
