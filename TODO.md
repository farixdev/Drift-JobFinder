# TODO - Drift job scanner enhancements

## Step 1 — Add Google source option in UI
- [ ] Update `ui/screen_setup.py` to add checkbox: `Search internet (Google)` (default off)

## Step 2 — Implement Google scraper
- [ ] Add `core/scraper/internet_google.py` (best-effort Google search HTML parsing to extract job-like links)
- [ ] Register `google` scraper in `core/scraper/__init__.py`

## Step 3 — Update source mapping
- [ ] Update `ui/worker.py` `SOURCE_KEYS` to map `Search internet (Google)` -> `google`

## Step 4 — Scrape more jobs per source
- [ ] Increase caps in `core/scraper/indeed.py` and `core/scraper/linkedin.py` (aim higher than 30)
- [ ] Ensure Bing already returns up to 50; adjust if needed

## Step 5 — Add timed pause / continue-end flow
- [ ] Modify `ui/worker.py` to track elapsed time and extracted job count
- [ ] Add new signal(s) to UI for: `pause_prompt` with context (jobs found so far)
- [ ] Implement modal in `ui/app.py` (or worker-safe mechanism) to block until user chooses continue/end
- [ ] Target prompt time: ~3.30 minutes (3–4 minutes requirement)
- [ ] If user selects End: proceed directly to scoring + results

## Step 6 — Improve scanning UI feedback
- [ ] Update `ui/screen_scan.py` logs to show:
  - which source is running
  - Google query text
  - extracted job count updates
  - pause prompt status (continuing vs ending)

## Step 7 — Validation
- [ ] Verify checked boxes correspond to visited/scraped sources (log per source start/end + extracted count)
- [ ] Verify goal: attempt 40–50 jobs per selected website/source when possible
- [ ] Verify pause prompt appears after ~3.30 min during active scraping
- [ ] Verify if user ends, scoring/matching starts immediately


