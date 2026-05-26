import json
import re
import time
from typing import Any

from openai import OpenAI

from core.config import get_groq_api_key, get_groq_model

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client
    api_key = get_groq_api_key()
    if not api_key:
        from core.config import groq_key_status

        _, message = groq_key_status()
        raise RuntimeError(message)
    _client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    return _client


def _parse_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _chat(prompt: str) -> str:
    delay = 3
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            response = _get_client().chat.completions.create(
                model=get_groq_model(),
                messages=[
                    {
                        "role": "system",
                        "content": "You return only valid JSON. No markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:
            last_error = exc
            msg = str(exc).lower()
            if "429" in msg or "rate" in msg or "quota" in msg:
                if attempt >= 3:
                    raise RuntimeError(
                        "Groq rate limit hit. Wait a minute and try again, "
                        "or use GROQ_MODEL=llama-3.1-8b-instant in .env"
                    ) from exc
                time.sleep(delay)
                delay = min(delay * 2, 45)
                continue
            raise
    raise RuntimeError(f"Groq API error: {last_error}")


def parse_resume(resume_text: str) -> dict[str, Any]:
    prompt = f"""
From this resume return ONLY JSON:
{{
  "skills": ["skill1"],
  "location": "City, Country or Remote",
  "keywords": ["search phrase 1"]
}}

Max 20 skills, 3-5 keywords.

Resume:
{resume_text[:3500]}
"""
    data = _parse_json(_chat(prompt))
    return {
        "skills": data.get("skills") or [],
        "location": (data.get("location") or "Remote").strip(),
        "keywords": data.get("keywords") or data.get("skills", [])[:3],
    }


def extract_skills(resume_text: str) -> list[str]:
    return parse_resume(resume_text)["skills"]


def extract_location(resume_text: str) -> str:
    return parse_resume(resume_text)["location"]


def generate_keywords(skills: list[str]) -> list[str]:
    if not skills:
        return ["software developer"]
    prompt = f"""
Given skills: {skills[:15]}
Return ONLY a JSON array of 3-5 job search keyword strings.
"""
    return _parse_json(_chat(prompt))


def score_jobs_batch(
    resume_text: str, jobs: list[dict], skills: list[str]
) -> list[dict]:
    if not jobs:
        return []

    listings = [
        {
            "id": i,
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "description": (j.get("description") or j.get("title") or "")[:800],
        }
        for i, j in enumerate(jobs)
    ]

    prompt = f"""
Score each job vs this resume. Return ONLY a JSON array:
[{{"id": 0, "score": 85, "matched_skills": ["Python"], "summary": "one sentence"}}]

Resume skills: {skills[:20]}
Resume:
{resume_text[:1500]}

Jobs:
{json.dumps(listings, ensure_ascii=False)}
"""
    try:
        result = _parse_json(_chat(prompt))
    except (json.JSONDecodeError, ValueError):
        return []

    if isinstance(result, dict):
        result = result.get("jobs") or result.get("results") or result.get("data") or []
    if not isinstance(result, list):
        return []

    normalized: list[dict] = []
    for pos, item in enumerate(result):
        if isinstance(item, dict):
            if item.get("id") is None:
                item = {**item, "id": pos}
            normalized.append(item)
    return normalized


def score_job(
    resume_text: str,
    job_description: str,
    skills: list[str] | None = None,
    title: str = "",
) -> dict[str, Any]:
    batch = score_jobs_batch(
        resume_text,
        [{"title": title, "description": job_description}],
        skills or [],
    )
    if batch:
        item = batch[0]
        return {
            "score": int(item.get("score", 0)),
            "matched_skills": item.get("matched_skills", []),
            "summary": item.get("summary", ""),
        }
    return {"score": 0, "matched_skills": [], "summary": "No match."}
