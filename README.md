<div align="center">

```
      _      _  __  _   
   __| |_ __(_)/ _|| |_ 
  / _` | '__| | |_ | __|
 | (_| | |  | |  _|| |_ 
  \__,_|_|  |_|_|   \__|
```

### **drift.jobs**
*Your resume, working while you sleep.*

![Python](https://img.shields.io/badge/Python-3.10+-black?style=flat-square)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15-black?style=flat-square)
![Gemini](https://img.shields.io/badge/Gemini_2.0_Flash-free-black?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-black?style=flat-square)

</div>

---

**drift** is a minimal desktop app that reads your resume, scrapes job boards, and uses AI to score every listing against your profile — then surfaces only the ones worth your time.

Upload your CV. Pick your sources. Set a match threshold. Let it run.

---

## How it works

```
your resume (PDF/DOCX)
        │
        ▼
  AI extracts skills,
  keywords, location
        │
        ▼
  scrapes LinkedIn,
  Indeed, Remotive,
  We Work Remotely
        │
        ▼
  Gemini scores each
  job against your CV
        │
        ▼
  only jobs above your
  threshold appear — 
  one click to apply
```

---

## Features

- **Smart resume parsing** — extracts skills, experience, and location from any PDF or DOCX
- **Multi-source scraping** — LinkedIn, Indeed, Remotive, We Work Remotely (mix and match)
- **AI-powered scoring** — Gemini 2.0 Flash rates each job 0–100 against your exact profile
- **Match threshold slider** — only see jobs above your minimum (e.g. 70%+)
- **Live scan log** — watch the pipeline run step by step in real time
- **One-click apply** — opens the job listing directly in your browser
- **Export report** — save your results as a clean HTML file
- **Duplicate filtering** — SQLite tracks seen jobs so you never see the same listing twice

---

## Screenshots

> Screen 1 — Setup · Screen 2 — Live scan · Screen 3 — Results

*(add screenshots here)*

---

## Getting started

### Prerequisites

- Python 3.10+
- Google Chrome installed (for Selenium scrapers)
- A free Gemini API key → [get one here](https://aistudio.google.com)

### Installation

```bash
# clone the repo
git clone https://github.com/yourusername/drift-jobs.git
cd drift-jobs

# create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_api_key_here
```

### Run

```bash
python main.py
```

---

## Usage

1. **Upload your resume** — drag and drop a `.pdf` or `.docx` file onto the upload zone
2. **Select job sources** — pick which boards to scrape (Remotive is fastest, no login needed)
3. **Set your threshold** — drag the slider to your minimum match score (70% is a good start)
4. **Hit "Start scanning"** — watch the live log as drift works through each step
5. **Review results** — job cards sorted by match score, with matched skills highlighted
6. **Apply** — click the apply button on any card to open the listing in your browser

---

## Project structure

```
drift/
├── main.py                  # entry point
├── ui/
│   ├── app.py               # main window, screen manager
│   ├── screen_setup.py      # screen 1: upload + config
│   ├── screen_scan.py       # screen 2: live log
│   └── screen_results.py    # screen 3: job cards
├── core/
│   ├── parser.py            # resume text extraction
│   ├── ai_engine.py         # Gemini — skill extraction + scoring
│   ├── matcher.py           # score jobs, filter by threshold
│   └── scraper/
│       ├── base.py          # base scraper class
│       ├── linkedin.py      # LinkedIn scraper (Selenium)
│       ├── indeed.py        # Indeed scraper (Selenium)
│       ├── remotive.py      # Remotive (open API, no Selenium)
│       └── wwr.py           # We Work Remotely scraper
├── db/
│   └── jobs.db              # SQLite job store
├── templates/
│   └── report.html          # export template
├── requirements.txt
└── .env.example
```

---

## Tech stack

| | |
|---|---|
| Language | Python 3.10+ |
| UI | PyQt5 |
| Resume parsing | pdfplumber · python-docx |
| AI / scoring | Google Gemini 2.0 Flash (free tier) |
| Scraping | Selenium · undetected-chromedriver |
| Storage | SQLite3 |
| Export | Jinja2 |

---

## Gemini free tier limits

drift uses **Gemini 2.0 Flash** which is completely free with no credit card required.

| | |
|---|---|
| Requests per minute | 60 |
| Requests per day | 1,500 |
| Cost | $0 |

For a typical scan of 50 jobs, drift makes roughly 55 API calls (1 for resume parsing + ~1 per job for scoring). Well within the free limits.

---

## Roadmap

- [ ] Email digest — daily summary sent to your inbox
- [ ] Saved searches — re-run the same config automatically
- [ ] Cover letter generator — AI drafts a tailored cover letter per job
- [ ] Dark mode
- [ ] More job sources (Glassdoor, Otta, Y Combinator jobs)

---

## Known limitations

- **LinkedIn scraping** is fragile — LinkedIn actively detects bots. If you get blocked, try adding a delay or using a different IP. The app uses `undetected-chromedriver` to reduce detection.
- **Job descriptions** aren't always available from scraped cards alone — scoring quality improves when the full JD text is fetched.
- **Location filtering** depends on what's in your resume — if no location is found, searches default to remote.

---

## Contributing

Pull requests are welcome. For major changes, open an issue first.

```bash
# run in dev mode
python main.py --dev
```

---

## License

MIT — do whatever you want with it.

---

<div align="center">
  <sub>Built by <a href="https://github.com/farixdev">faris</a> · give it a ⭐ if it helped</sub>
</div>
