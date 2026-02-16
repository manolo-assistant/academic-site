#!/usr/bin/env python3

import csv
import json
import os
import sys
import re
import subprocess
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time

def read_csv(filepath):
    """Read CSV file and return list of dictionaries"""
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up any empty string values
                cleaned_row = {k: v.strip() if v else '' for k, v in row.items()}
                data.append(cleaned_row)
        print(f"Read {len(data)} records from {filepath}")
    except FileNotFoundError:
        print(f"Warning: {filepath} not found")
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return data

def read_hugo_talks(talks_dir):
    """Read existing Hugo talk files and extract metadata"""
    data = []
    talks_path = Path(talks_dir)
    
    if not talks_path.exists():
        print(f"Warning: {talks_dir} not found")
        return data
    
    for md_file in talks_path.glob("*.md"):
        if md_file.name == "_index.md":
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    body = parts[2].strip()
                    
                    # Parse YAML-like frontmatter
                    metadata = {}
                    for line in frontmatter.split('\n'):
                        line = line.strip()
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            
                            # Handle nested params
                            if key == 'params':
                                continue
                            elif line.startswith('  '):
                                # This is a param
                                param_key = key.strip()
                                metadata[param_key] = value
                            else:
                                metadata[key] = value
                    
                    # Extract abstract from body
                    abstract = ""
                    abstract_match = re.search(r'### Abstract\s*\n\n(.+?)(?:\n\n###|\Z)', body, re.DOTALL)
                    if abstract_match:
                        abstract = abstract_match.group(1).strip()
                    
                    # Convert to standard format
                    talk = {
                        'title': metadata.get('title', ''),
                        'type': metadata.get('type', ''),
                        'event': metadata.get('event', ''),
                        'date': metadata.get('date', ''),
                        'url': extract_url_from_body(body),
                        'abstract': abstract,
                        'tags': metadata.get('tags', ''),
                        'source': f'hugo:{md_file.name}'
                    }
                    data.append(talk)
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    print(f"Read {len(data)} records from Hugo files")
    return data

def extract_url_from_body(body):
    """Extract URL from markdown body"""
    # Look for [Event page](URL) pattern
    url_match = re.search(r'\[Event page\]\(([^)]+)\)', body)
    if url_match:
        return url_match.group(1)
    
    # Look for any markdown link
    url_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', body)
    if url_match:
        return url_match.group(2)
    
    return ""

def normalize_date(date_str):
    """Normalize date to ISO format YYYY-MM-DDTHH:MM:SSZ"""
    if not date_str:
        return ""
    
    # If already in ISO format, return as is
    if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?', date_str):
        if not date_str.endswith('Z'):
            date_str += 'Z'
        return date_str
    
    # Handle YYYY-MM-DD format
    if re.match(r'\d{4}-\d{2}-\d{2}$', date_str):
        return f"{date_str}T12:00:00Z"
    
    return date_str

def create_dedup_key(talk):
    """Create a key for deduplication based on title + date"""
    title = talk.get('title', '').lower().strip()
    date = talk.get('date', '')
    
    # Extract just the date part (YYYY-MM-DD)
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', date)
    if date_match:
        date_part = date_match.group(1)
    else:
        date_part = date
    
    return f"{title}|{date_part}"

def merge_and_deduplicate(unified_data, cv_data, hugo_data):
    """Merge all data sources and deduplicate"""
    all_talks = []
    seen_keys = set()
    
    # Add source information
    for talk in unified_data:
        talk['source'] = 'unified'
    for talk in cv_data:
        talk['source'] = 'cv'
    # hugo_data already has source info
    
    # Merge all data
    all_data = unified_data + cv_data + hugo_data
    
    for talk in all_data:
        # Normalize date
        talk['date'] = normalize_date(talk.get('date', ''))
        
        # Create dedup key
        key = create_dedup_key(talk)
        
        if key not in seen_keys:
            seen_keys.add(key)
            all_talks.append(talk)
        else:
            print(f"Duplicate found: {talk['title']} on {talk['date']} (source: {talk['source']})")
    
    # Sort by date (newest first)
    all_talks.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    print(f"After deduplication: {len(all_talks)} unique talks")
    return all_talks

def search_for_abstract(talk):
    """Search online for talk abstract if missing"""
    if talk.get('abstract', '').strip():
        return talk['abstract']  # Already has abstract
    
    url = talk.get('url', '')
    if not url or url in ['#', '']:
        return ""
    
    try:
        print(f"Searching for abstract: {talk['title']} at {url}")
        
        # Add User-Agent to avoid blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            
            # Look for abstracts - search for paragraphs that mention the speaker or contain mathematical terms
            title_words = talk['title'].lower().split()
            abstract_indicators = ['abstract', 'summary', talk['title'].lower()]
            
            potential_abstracts = []
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(indicator in line_lower for indicator in abstract_indicators):
                    # Look for a substantial paragraph nearby
                    for j in range(max(0, i-3), min(len(lines), i+5)):
                        candidate = lines[j]
                        if len(candidate) > 100:  # Substantial text
                            potential_abstracts.append(candidate)
            
            if potential_abstracts:
                # Return the longest candidate
                abstract = max(potential_abstracts, key=len)
                if len(abstract) > 50:
                    print(f"Found abstract for {talk['title']}")
                    return abstract[:1000]  # Limit length
        
        time.sleep(1)  # Be nice to servers
        
    except Exception as e:
        print(f"Error searching for abstract at {url}: {e}")
    
    return ""

def update_google_sheet(talks_data):
    """Update the Google Sheet with merged talks data"""
    # Prepare data for Google Sheets - convert to flat list of values for each row
    sheet_rows = []
    
    # Header row
    sheet_rows.append(['title', 'type', 'event', 'date', 'url', 'abstract'])
    
    for talk in talks_data:
        row = [
            talk.get('title', ''),
            talk.get('type', ''),
            talk.get('event', ''),
            talk.get('date', ''),
            talk.get('url', ''),
            talk.get('abstract', '')
        ]
        sheet_rows.append(row)
    
    print(f"Prepared {len(sheet_rows)-1} data rows for Google Sheets")
    
    # Construct the range - assuming gid 508483272 corresponds to a sheet name
    # We need to clear a large range first and then update
    spreadsheet_id = "1X7VKV3pwBoYjQoUHpxckYJAgaErCYkevc47bJoMV0J0"
    range_name = "Talks!A:F"  # Clear all columns A through F
    
    try:
        # First clear the existing data
        print("Clearing existing sheet data...")
        clear_cmd = [
            'bash', '-c',
            f'source ~/.bashrc && '
            f'GOG_KEYRING_PASSWORD="$GOG_KEYRING_PASSWORD" '
            f'gog sheets clear "{spreadsheet_id}" "{range_name}" '
            f'--account manolo.assistant@gmail.com'
        ]
        result = subprocess.run(clear_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Clear command failed: {result.stderr}")
            return False
        
        # Now update with new data using the update command
        print("Updating sheet with new data...")
        
        # Prepare the values as command line arguments
        values_args = []
        for row in sheet_rows:
            # Each row becomes a separate argument, with cells separated by tabs
            row_str = '\t'.join(str(cell) for cell in row)
            values_args.append(row_str)
        
        # Use a range starting from A1
        update_range = "Talks!A1:F"
        
        # Create the command
        update_cmd = [
            'bash', '-c',
            f'source ~/.bashrc && '
            f'GOG_KEYRING_PASSWORD="$GOG_KEYRING_PASSWORD" '
            f'gog sheets update "{spreadsheet_id}" "{update_range}" '
        ] + values_args + [
            f'--account manolo.assistant@gmail.com'
        ]
        
        # Actually, let me use a different approach with a temp file
        temp_file = '/tmp/talks_update.tsv'
        with open(temp_file, 'w', encoding='utf-8') as f:
            for row in sheet_rows:
                f.write('\t'.join(str(cell) for cell in row) + '\n')
        
        # Use the file as input
        update_cmd = [
            'bash', '-c',
            f'source ~/.bashrc && '
            f'GOG_KEYRING_PASSWORD="$GOG_KEYRING_PASSWORD" '
            f'gog sheets update "{spreadsheet_id}" "{update_range}" '
            f'"$(cat {temp_file})" '
            f'--account manolo.assistant@gmail.com'
        ]
        
        result = subprocess.run(update_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Update command failed: {result.stderr}")
            # Try a different approach - update row by row
            return update_sheet_row_by_row(spreadsheet_id, sheet_rows)
        
        print("Google Sheet updated successfully")
        
        # Clean up temp file
        try:
            os.remove(temp_file)
        except:
            pass
            
    except Exception as e:
        print(f"Error updating Google Sheet: {e}")
        return False
    
    return True

def update_sheet_row_by_row(spreadsheet_id, sheet_rows):
    """Fallback method to update sheet row by row"""
    print("Trying row-by-row update approach...")
    try:
        for i, row in enumerate(sheet_rows):
            row_range = f"Talks!A{i+1}:F{i+1}"
            row_str = '\t'.join(str(cell) for cell in row)
            
            cmd = [
                'bash', '-c',
                f'source ~/.bashrc && '
                f'GOG_KEYRING_PASSWORD="$GOG_KEYRING_PASSWORD" '
                f'gog sheets update "{spreadsheet_id}" "{row_range}" '
                f'"{row_str}" '
                f'--account manolo.assistant@gmail.com'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Failed to update row {i+1}: {result.stderr}")
                return False
        
        print(f"Successfully updated {len(sheet_rows)} rows")
        return True
        
    except Exception as e:
        print(f"Row-by-row update failed: {e}")
        return False

def update_hugo_files(talks_data, talks_dir):
    """Update Hugo content files based on merged data"""
    talks_path = Path(talks_dir)
    
    # Clear existing files (except _index.md)
    for md_file in talks_path.glob("*.md"):
        if md_file.name != "_index.md":
            md_file.unlink()
            
    # Create new files
    for i, talk in enumerate(talks_data):
        # Generate filename
        title_slug = re.sub(r'[^\w\s-]', '', talk.get('title', '').lower())
        title_slug = re.sub(r'[-\s]+', '-', title_slug).strip('-')
        date_part = talk.get('date', '')[:10] if talk.get('date') else f"unknown-{i}"
        filename = f"{date_part}-{title_slug}.md" if title_slug else f"{date_part}-talk-{i}.md"
        filename = filename.replace('--', '-')
        
        file_path = talks_path / filename
        
        # Create content
        content = f"""---
title: "{talk.get('title', '')}"
date: {talk.get('date', '')[:10] if talk.get('date') else '2000-01-01'}
params:
  type: "{talk.get('type', '')}"
  event: "{talk.get('event', '')}"
  tags: "{talk.get('tags', 'Past')}"
---

**{talk.get('event', '')}** — {talk.get('type', '')}, {talk.get('date', '')[:10] if talk.get('date') else 'Date TBD'}

"""
        
        # Add URL if available
        if talk.get('url') and talk.get('url') not in ['#', '']:
            content += f"[Event page]({talk.get('url')})\n\n"
        
        # Add abstract if available
        if talk.get('abstract', '').strip():
            content += f"### Abstract\n\n{talk.get('abstract')}\n"
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"Updated {len(talks_data)} Hugo talk files")

def main():
    # Paths
    data_dir = "/root/clawd/data/website-rebuild"
    hugo_talks_dir = "/tmp/academic-site/content/talks"
    
    print("=== Merging Talks Data ===")
    
    # Read data from all sources
    unified_data = read_csv(f"{data_dir}/unified-talks.csv")
    cv_data = read_csv(f"{data_dir}/cv-talks.csv") 
    hugo_data = read_hugo_talks(hugo_talks_dir)
    
    # Merge and deduplicate
    merged_talks = merge_and_deduplicate(unified_data, cv_data, hugo_data)
    
    # Search for missing abstracts (only for talks with URLs)
    print("\n=== Searching for missing abstracts ===")
    for talk in merged_talks:
        if not talk.get('abstract', '').strip() and talk.get('url') and talk.get('url') not in ['#', '']:
            abstract = search_for_abstract(talk)
            if abstract:
                talk['abstract'] = abstract
    
    # Update Google Sheet
    print("\n=== Updating Google Sheet ===")
    if update_google_sheet(merged_talks):
        print("Google Sheet updated successfully")
    else:
        print("Failed to update Google Sheet")
        return False
    
    # Update Hugo files
    print("\n=== Updating Hugo files ===")
    update_hugo_files(merged_talks, hugo_talks_dir)
    
    print(f"\n=== Complete! Processed {len(merged_talks)} talks ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)