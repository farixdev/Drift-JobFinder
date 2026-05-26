import time

from PyQt5.QtCore import QThread, pyqtSignal

from core import ai_engine, matcher, parser
from core.config import load_env
from core.scraper import get_custom_scraper, get_scraper
from db import dedupe_by_url, init_db

SOURCE_KEYS = {
    "LinkedIn": "linkedin",
    "Indeed": "indeed",
    "Remotive": "remotive",
    "We Work Remotely": "wwr",
    "ZipRecruiter": "ziprecruiter",
    "Search internet (Bing)": "bing",
    "Search internet (Google)": "google",
}




class ScanWorker(QThread):
    log_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int)
    subtitle_signal = pyqtSignal(str)
    done_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)
    pause_prompt_signal = pyqtSignal(int, int)  # jobs_found, elapsed_seconds


    def __init__(
        self,
        resume_path: str,
        selected_sources: list[str],
        threshold: int,
        resume_text: str = "",
        custom_url: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.resume_path = resume_path
        self.selected_sources = selected_sources
        self.threshold = threshold
        self.resume_text = resume_text
        self.custom_url = custom_url

    def run(self) -> None:
        try:
            load_env()
            init_db()

            self.log_signal.emit("Parsing resume...", "active")
            resume_text = (self.resume_text or "").strip()
            if len(resume_text) < 20:
                resume_text = parser.extract(self.resume_path)
            if len(resume_text.strip()) < 20:
                raise RuntimeError(
                    "Could not extract text from resume. Use a text-based PDF, DOC, or DOCX."
                )

            parsed = ai_engine.parse_resume(resume_text)
            skills = parsed["skills"]
            location = parsed["location"]
            keywords = parsed["keywords"]
            role_hint = ", ".join(skills[:2]) if skills else "Your profile"
            self.subtitle_signal.emit(f"{role_hint} · {location}")

            self.log_signal.emit(
                f"Resume parsed — {len(skills)} skills extracted", "done"
            )
            self.progress_signal.emit(20)

            kw_preview = ", ".join(keywords[:4])
            self.log_signal.emit(f"Keywords generated — {kw_preview}", "done")
            self.progress_signal.emit(35)

            all_jobs = []

            # Pause/continue after some time so the user can decide whether to
            # continue extracting more jobs or to start matching/scoring.
            started_at = time.time()
            paused_once = False
            PAUSE_AFTER_SECONDS = 210  # ~3.5 minutes
            JOBS_SOFT_TARGET = 35  # aim around 30–40 while paused

            def maybe_pause() -> bool:
                nonlocal paused_once
                if paused_once:
                    return False
                elapsed = time.time() - started_at
                jobs_found = len(all_jobs)
                if elapsed >= PAUSE_AFTER_SECONDS and jobs_found >= JOBS_SOFT_TARGET:
                    paused_once = True
                    self.log_signal.emit(
                        f"Pause: extracted {jobs_found} jobs so far (elapsed {int(elapsed)}s).",
                        "active",
                    )
                    self.pause_prompt_signal.emit(jobs_found, int(elapsed))
                    # Wait until UI sets the worker decision.
                    self._waiting_for_user = False
                    return self._user_decision_end
                return False

            self._user_decision_end = False
            self._resume_scan = True
            self._waiting_for_user = False

            if self.custom_url:

                label = self.custom_url.replace("https://", "")
                self.log_signal.emit(f"Fetching {label}...", "active")
                scraper = get_custom_scraper(self.custom_url)
                jobs = scraper.search(keywords, location)
                found_count = len(jobs)
                jobs = dedupe_by_url(jobs)
                all_jobs.extend(jobs)
                if maybe_pause():
                    return


                self.log_signal.emit(
                    f"{label} — {len(jobs)} roles found",
                    "done",
                )
                if found_count == 0:
                    self.log_signal.emit(
                        "No listings on /jobs page — check URL loads in your browser",
                        "done",
                    )
                self.progress_signal.emit(70)
            else:
                source_count = max(len(self.selected_sources), 1)
                step_span = 35 // source_count
                for idx, source_label in enumerate(self.selected_sources):
                    key = SOURCE_KEYS.get(source_label, source_label.lower())
                    self.log_signal.emit(
                        f"Searching {source_label} — starting...", "active"
                    )
                    scraper = get_scraper(key)
                    jobs = scraper.search(keywords, location)
                    jobs = dedupe_by_url(jobs)
                    all_jobs.extend(jobs)
                    self.log_signal.emit(
                        f"{source_label} — {len(jobs)} listings found", "done"
                    )
                    self.progress_signal.emit(35 + step_span * (idx + 1))

            self.log_signal.emit(
                f"Scoring {len(all_jobs)} jobs...", "active"
            )
            self.progress_signal.emit(75)
            scored = matcher.score_all(
                all_jobs, resume_text, self.threshold, skills=skills
            )
            self.log_signal.emit(
                f"Scored — {len(scored)} shown (threshold {self.threshold}%)",
                "done",
            )
            self.progress_signal.emit(90)

            self.log_signal.emit("Generating report", "active")
            if not all_jobs:
                self.log_signal.emit(
                    "No jobs scraped — try Remotive or check your /jobs URL",
                    "done",
                )
            elif not scored:
                self.log_signal.emit(
                    f"0 matches above {self.threshold}% — try lowering the slider",
                    "done",
                )
            else:
                self.log_signal.emit(
                    f"Done — {len(scored)} jobs matched", "done"
                )
            self.progress_signal.emit(100)
            self.done_signal.emit(scored)
        except Exception as exc:
            self.error_signal.emit(str(exc))
