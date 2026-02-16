#!/usr/bin/env python3
"""
sync-drive.py — Download data from Jaume's published Google Sheet and generate Hugo content.

The spreadsheet has published CSV URLs for each tab:
  - gid=0: conferences/travel (id, title, url, location, tags, date, date_end)
  - gid=1581332120: talks (id, title, type, event, url, abstract, tags, date, date_end, time_zone)

Usage:
  python scripts/sync-drive.py
  python scripts/sync-drive.py --sheet-id SHEET_ID   # override sheet
  python scripts/sync-drive.py --image-folder-id ID   # also sync images from Drive
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

# Published CSV URLs from the URLs sheet
SHEET_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRchAxHUEFwDxDinsba7BZqejlUPdOdiD1jjQv6NAXtEufiZU1_UfPlAAzks4tw3AHUf5h105w-AN-c/pub"
PUBLISHED_CSVS = {
    "conferences": f"{SHEET_BASE}?gid=0&single=true&output=csv",
    "talks": f"{SHEET_BASE}?gid=1581332120&single=true&output=csv",
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80]


def download_csv(url: str) -> list[dict]:
    """Download a CSV from a URL and return list of dicts."""
    try:
        with urlopen(url, timeout=30) as resp:
            text = resp.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        return [row for row in reader]
    except URLError as e:
        print(f"Warning: Could not download CSV: {e}", file=sys.stderr)
        return []


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
                    print(f"Downloading image: {f['name']}")
                    urlretrieve(dl_url, dest)
    except URLError as e:
        print(f"Warning: Could not list drive folder: {e}", file=sys.stderr)


def generate_talks_travel(conferences: list[dict], talks: list[dict]):
    """Generate the Talks & Travel page from conferences + talks data.

    Conferences = travel/events attended (with date ranges).
    Talks = specific talks given (with abstracts).
    We merge them: talks get their own pages, conferences appear in the travel list.
    """
    # Generate individual talk pages
    talks_dir = CONTENT_DIR / "talks"
    talks_dir.mkdir(parents=True, exist_ok=True)
    for f in talks_dir.glob("*.md"):
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
        year = date[:4] if date else ""

        url_line = f'[Event page]({url})' if url and url != "#" else ""

        md = f"""---
title: "{title.replace('"', '\\"')}"
date: {date or "2020-01-01"}
params:
  year: {year}
  type: "{talk_type}"
  event: "{event.replace('"', '\\"')}"
  tags: "{tags}"
---

**{event}**{f" — {talk_type}" if talk_type else ""}, {date}

{url_line}

{("### Abstract" + chr(10) + chr(10) + abstract) if abstract else ""}
"""
        (talks_dir / f"{slugify(talk_id)}.md").write_text(md)

    print(f"Generated {len(talks)} talk pages")

    # Generate travel/conferences list page
    travel_dir = CONTENT_DIR / "travel"
    travel_dir.mkdir(parents=True, exist_ok=True)
    for f in travel_dir.glob("*.md"):
        if f.name != "_index.md":
            f.unlink()

    # Sort conferences by date descending
    sorted_conf = sorted(conferences, key=lambda r: r.get("date", ""), reverse=True)

    current = [c for c in sorted_conf if c.get("tags", "").strip() == "Current"]
    past = [c for c in sorted_conf if c.get("tags", "").strip() == "Past"]

    lines = ["---", 'title: "Talks & Travel"', "---", ""]
    lines.append("Travel plans and topics for upcoming events. If I'm travelling near you and want to meet, contact me!\n")

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

    (travel_dir / "_index.md").write_text("\n".join(lines))
    print(f"Generated travel page with {len(conferences)} events")


def generate_cv_data(conferences, talks):
    """Generate JSON data file for LaTeX CV."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cv_data = {
        "conferences": [
            {k: v for k, v in row.items() if k and v}
            for row in conferences
        ],
        "talks": [
            {k: v for k, v in row.items() if k and v}
            for row in talks
        ],
    }
    (DATA_DIR / "cv.json").write_text(json.dumps(cv_data, indent=2, ensure_ascii=False))
    print("Generated data/cv.json for LaTeX CV")


def main():
    parser = argparse.ArgumentParser(description="Sync Google Drive data to Hugo content")
    parser.add_argument("--sheet-id", help="Google Sheet ID (overrides hardcoded URLs)")
    parser.add_argument("--image-folder-id", help="Google Drive folder ID for images")
    args = parser.parse_args()

    # Download data
    print("Downloading conferences data...")
    conferences = download_csv(PUBLISHED_CSVS["conferences"])
    print(f"  → {len(conferences)} conferences")

    print("Downloading talks data...")
    talks = download_csv(PUBLISHED_CSVS["talks"])
    print(f"  → {len(talks)} talks")

    # Generate content
    if conferences or talks:
        generate_talks_travel(conferences, talks)

    # Images
    if args.image_folder_id:
        print(f"Downloading images from Drive folder: {args.image_folder_id}")
        download_drive_folder_images(args.image_folder_id)

    # CV data
    generate_cv_data(conferences, talks)


if __name__ == "__main__":
    main()
