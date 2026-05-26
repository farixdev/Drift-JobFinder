from datetime import datetime

from core import ai_engine
from core.config import get_max_jobs_to_score
from core.scraper.base import RawJob
from models import Job


def _local_prefilter_score(skills: list[str], text: str) -> int:
    if not skills or not text:
        return 0
    lower = text.lower()
    hits = sum(1 for s in skills if s and s.lower() in lower)
    return min(100, hits * 12)


def _local_score_item(skills: list[str], raw: RawJob) -> dict:
    text = f"{raw.title} {raw.description} {raw.company}"
    matched = [s for s in skills if s and s.lower() in text.lower()]
    score = _local_prefilter_score(skills, text)
    if score < 40 and matched:
        score = 40 + len(matched) * 10
    if score < 25 and raw.title:
        score = 25
    summary = (
        f"Matched on: {', '.join(matched[:4])}" if matched else "Found on jobs page."
    )
    return {
        "score": min(100, score),
        "matched_skills": matched,
        "summary": summary,
    }


def _normalize_score(item: dict | None) -> int | None:
    if not item:
        return None
    raw = item.get("score")
    if raw is None:
        return None
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return None


def score_all(
    raw_jobs: list[RawJob],
    resume_text: str,
    threshold: int,
    skills: list[str] | None = None,
) -> list[Job]:
    if not raw_jobs:
        return []

    skills = skills or []
    max_jobs = get_max_jobs_to_score()

    ranked = sorted(
        raw_jobs,
        key=lambda r: _local_prefilter_score(
            skills, f"{r.title} {r.description} {r.company}"
        ),
        reverse=True,
    )
    to_score = ranked[:max_jobs]

    payloads = [
        {
            "title": raw.title,
            "company": raw.company,
            "description": raw.description or raw.title,
        }
        for raw in to_score
    ]

    scored_items: list[dict] = []
    try:
        scored_items = ai_engine.score_jobs_batch(resume_text, payloads, skills)
    except Exception:
        scored_items = []

    by_id: dict[int, dict] = {}
    for pos, item in enumerate(scored_items):
        if not isinstance(item, dict):
            continue
        idx = item.get("id")
        if idx is not None:
            try:
                by_id[int(idx)] = item
            except (TypeError, ValueError):
                by_id[pos] = item
        else:
            by_id[pos] = item

    candidates: list[tuple[RawJob, dict]] = []
    for i, raw in enumerate(to_score):
        local = _local_score_item(skills, raw)
        ai_item = by_id.get(i)
        if ai_item is None and i < len(scored_items) and isinstance(scored_items[i], dict):
            ai_item = scored_items[i]

        ai_score = _normalize_score(ai_item)
        local_score = local["score"]
        final_score = max(s for s in (ai_score, local_score) if s is not None)

        matched = local.get("matched_skills") or []
        summary = local.get("summary") or ""
        if ai_item:
            matched = ai_item.get("matched_skills") or matched
            summary = ai_item.get("summary") or summary

        candidates.append(
            (
                raw,
                {
                    "score": final_score,
                    "matched_skills": matched,
                    "summary": summary,
                },
            )
        )

    results: list[Job] = []
    for raw, item in candidates:
        score = int(item["score"])
        if score >= threshold:
            results.append(
                Job(
                    title=raw.title,
                    company=raw.company,
                    location=raw.location,
                    job_type=raw.job_type or "",
                    url=raw.url,
                    source=raw.source,
                    matched_skills=item.get("matched_skills", []),
                    score=score,
                    summary=item.get("summary", ""),
                    scraped_at=datetime.now(),
                )
            )

    if not results and candidates:
        top = sorted(candidates, key=lambda x: x[1]["score"], reverse=True)[:10]
        for raw, item in top:
            results.append(
                Job(
                    title=raw.title,
                    company=raw.company,
                    location=raw.location,
                    job_type=raw.job_type or "",
                    url=raw.url,
                    source=raw.source,
                    matched_skills=item.get("matched_skills", []),
                    score=int(item["score"]),
                    summary=item.get("summary", ""),
                    scraped_at=datetime.now(),
                )
            )

    return sorted(results, key=lambda j: j.score, reverse=True)
