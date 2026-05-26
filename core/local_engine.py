"""
Local resume parsing and job scoring — 100% on your machine.
No API keys, no quotas, no cloud.
"""

import re
from typing import Any

from core.skills_db import SKILLS

_LOCATION_RE = re.compile(
    r"(?i)\b(?:based in|located in|location[:\s]+)\s*"
    r"([A-Za-z][A-Za-z\s,.'-]{2,60})"
)
_CITY_COUNTRY_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s*[A-Z][a-z][A-Za-z\s]+)\b"
)
_REMOTE_RE = re.compile(r"(?i)\b(remote|work from home|wfh|hybrid)\b")


def _normalize_skill(skill: str) -> str:
    s = skill.strip()
    if s.lower() in ("c#", "c++", ".net"):
        return s
    return s.title() if s.islower() else s


def extract_skills(resume_text: str) -> list[str]:
    lower = resume_text.lower()
    found: list[str] = []
    seen: set[str] = set()

    for skill in sorted(SKILLS, key=len, reverse=True):
        pattern = rf"\b{re.escape(skill)}\b"
        if re.search(pattern, lower, re.IGNORECASE):
            key = skill.lower()
            if key not in seen:
                seen.add(key)
                found.append(_normalize_skill(skill))

    return found[:30]


def extract_location(resume_text: str) -> str:
    if _REMOTE_RE.search(resume_text):
        # Still prefer a city if both appear
        pass

    for pattern in (_LOCATION_RE, _CITY_COUNTRY_RE):
        match = pattern.search(resume_text)
        if match:
            loc = match.group(1).strip().rstrip(".,;")
            if len(loc) > 2:
                return loc

    cities = (
        "Lahore",
        "Karachi",
        "Islamabad",
        "Rawalpindi",
        "London",
        "New York",
        "San Francisco",
        "Toronto",
        "Berlin",
        "Dubai",
        "Singapore",
        "Sydney",
        "Mumbai",
        "Delhi",
        "Bangalore",
    )
    for city in cities:
        if re.search(rf"\b{re.escape(city)}\b", resume_text, re.I):
            return city

    if _REMOTE_RE.search(resume_text):
        return "Remote"
    return "Remote"


def generate_keywords(skills: list[str]) -> list[str]:
    if not skills:
        return ["software developer", "engineer"]
    keywords: list[str] = []
    for skill in skills[:3]:
        keywords.append(f"{skill} developer")
    if len(keywords) < 3:
        keywords.append(" ".join(skills[:2]))
    return keywords[:5]


def parse_resume(resume_text: str) -> dict[str, Any]:
    skills = extract_skills(resume_text)
    location = extract_location(resume_text)
    keywords = generate_keywords(skills)
    return {
        "skills": skills,
        "location": location,
        "keywords": keywords,
    }


def score_job(
    resume_text: str,
    job_description: str,
    skills: list[str] | None = None,
    title: str = "",
) -> dict[str, Any]:
    skills = skills or extract_skills(resume_text)
    text = f"{title} {job_description}".lower()
    title_lower = (title or "").lower()

    matched: list[str] = []
    for skill in skills:
        if re.search(rf"\b{re.escape(skill.lower())}\b", text, re.I):
            matched.append(skill)

    if not matched:
        return {
            "score": 0,
            "matched_skills": [],
            "summary": "No strong skill overlap found.",
        }

    skill_ratio = len(matched) / max(len(skills), 1)
    title_hits = sum(
        1 for s in matched if re.search(rf"\b{re.escape(s.lower())}\b", title_lower, re.I)
    )

    score = int(min(100, 25 + skill_ratio * 55 + title_hits * 12 + len(matched) * 3))
    top = ", ".join(matched[:3])
    summary = f"Strong overlap on {top}."
    if title_hits:
        summary = f"Title and skills align ({top})."

    return {
        "score": score,
        "matched_skills": matched,
        "summary": summary,
    }


def score_jobs_batch(
    resume_text: str,
    jobs: list[dict],
    skills: list[str] | None = None,
) -> list[dict]:
    skills = skills or extract_skills(resume_text)
    results = []
    for i, job in enumerate(jobs):
        scored = score_job(
            resume_text,
            job.get("description") or "",
            skills=skills,
            title=job.get("title") or "",
        )
        results.append({"id": i, **scored})
    return results
