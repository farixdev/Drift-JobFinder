# drift.jobs

**Your resume, working while you sleep.**

PyQt5 app that parses your resume, scrapes job boards, and scores matches using **[Groq](https://groq.com)** (fast Llama models, generous free tier).

## Setup

```powershell
cd c:\Users\User\Downloads\Drift
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Groq API key (free)

1. Go to https://console.groq.com/keys
2. Create an API key
3. Edit `.env`:

```env
GROQ_API_KEY=gsk_your_actual_key
GROQ_MODEL=llama-3.1-8b-instant
MAX_JOBS_TO_SCORE=15
```

4. Save `.env` and run:

```powershell
python main.py
```

## Features

- Resume upload: PDF, DOC, DOCX
- Sources: LinkedIn, Indeed, Remotive, We Work Remotely
- Groq AI: skill extraction, keywords, job scoring
- HTML report export
- SQLite duplicate filtering

## Tips

- Start with **Remotive only** for a reliable demo
- `llama-3.1-8b-instant` is fastest on free tier
- Lower `MAX_JOBS_TO_SCORE` if you hit rate limits

## License

MIT
