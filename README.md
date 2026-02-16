# Academic Personal Website — MWE

A GitHub Pages site that auto-builds from Google Drive data, using Hugo + LaTeX.

## Architecture

```
Google Drive (public folder)
  ├── Google Sheet (publications, talks, teaching tabs)
  └── Images folder (profile photo, etc.)
         │
         ▼  (daily cron / on push)
  GitHub Actions workflow
         │
         ├── scripts/sync-drive.py    → downloads Sheet as CSV, generates Hugo content
         ├── scripts/build-cv.py      → generates PDF CV from same data via LaTeX
         └── hugo --minify            → builds static site
         │
         ▼
  GitHub Pages (deployed)
```

## Quick Start

### 1. Set up Google Drive data source

1. Create a Google Sheet with tabs named: `publications`, `talks`, `teaching`
2. Each tab should have columns:
   - **publications:** `title`, `authors`, `year`, `journal`, `arxiv`, `doi`
   - **talks:** `title`, `venue`, `date`, `location`, `year`
   - **teaching:** `course`, `term`, `institution`, `role`, `year`
3. Publish the sheet: File → Share → Publish to web (as CSV)
4. Note the Sheet ID from the URL
5. (Optional) Create a public Drive folder for images, note the folder ID

### 2. Configure the repo

Set these as GitHub repository secrets (Settings → Secrets → Actions):
- `GOOGLE_SHEET_ID` — the Sheet ID
- `GOOGLE_DRIVE_FOLDER_ID` — the images folder ID

### 3. Deploy

Push to `main` and the GitHub Actions workflow will:
1. Download data from Google Drive
2. Generate Hugo content files
3. Build a PDF CV via LaTeX
4. Build the Hugo site
5. Deploy to GitHub Pages

The workflow also runs daily at 6 AM UTC via cron.

### 4. Enable GitHub Pages

Go to repo Settings → Pages → Source: **GitHub Actions**.

## Local Development

```bash
# Install Hugo (https://gohugo.io/installation/)
# Then:
hugo server
```

## File Structure

```
├── .github/workflows/build.yml   # CI/CD pipeline
├── content/                       # Hugo content (auto-generated or manual)
│   ├── _index.md                  # Homepage / bio
│   ├── publications/              # Papers
│   ├── talks/                     # Talks & travel
│   └── teaching/                  # Courses
├── cv/
│   ├── templates/cv.tex           # LaTeX CV template
│   └── output/                    # Build artifacts
├── data/                          # Structured data (cv.json)
├── layouts/                       # Hugo templates (custom, no theme dependency)
├── scripts/
│   ├── sync-drive.py              # Google Drive → Hugo content
│   └── build-cv.py                # cv.json → LaTeX → PDF
├── static/
│   ├── css/style.css              # Stylesheet
│   ├── img/                       # Images
│   └── cv.pdf                     # Generated CV
└── hugo.toml                      # Hugo config
```

## Design Decisions

- **No theme dependency:** Uses custom layouts (clean, minimal, academic). Easy to modify.
- **No OAuth:** Google Drive sync uses publicly shared resources only.
- **Single data source:** Google Sheet is the source of truth for all structured data.
- **PDF CV from same data:** LaTeX template is populated from the same JSON that builds the site.
- **MWE:** This is a minimum working example. Production use would add: search, BibTeX export, dark mode, etc.
