# drift.jobs — implementation checklist

- [x] Inspect current scraping flow (done)
- [x] Add new scrapers: ZipRecruiter (best-effort) + Bing internet search (best-effort)
- [x] Register new scrapers in core/scraper/__init__.py
- [x] Update UI setup screen to add checkboxes for ZipRecruiter + Search internet (Bing)

- [ ] Update scraping worker to collect up to 40–50 unique jobs per scan (incremental batches)
- [ ] Add pagination attempts for Indeed + LinkedIn during scraping
- [ ] Implement timed “Continue scraping?” prompt after ~3–4 minutes
- [ ] Improve scan UI with live counters (elapsed time, collected jobs/target, active source, batch #)
- [ ] Verify scoring still works and results screen displays scored jobs
- [ ] Quick manual test plan:
  - [ ] Remotive only scan
  - [ ] Indeed+LinkedIn scan (ensure it collects more than first page)
  - [ ] ZipRecruiter scan
  - [ ] Internet search scan (ensure it doesn’t crash)

