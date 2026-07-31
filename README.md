# yt-transcript-translator

Paste a YouTube URL, get the transcript back in fluent English.

A small FastAPI service: it pulls the video's transcript, detects the language,
and if it isn't English, translates it with Claude. Non-English transcripts of
talks, lectures, and interviews become readable in one paste.

## How it works

- `app.py`: FastAPI app. One page (`/`), one endpoint (`POST /api/transcript`).
- `fetch_transcript.py`: transcript fetching runs in a subprocess so every
  request gets a clean HTTP session (the transcript library misbehaves when a
  long-lived server process reuses sessions). Tries English first, falls back
  to whatever language exists.
- Translation: Claude (`claude-sonnet-5`) turns the raw transcript into
  natural English, preserving paragraph breaks. English transcripts skip the
  model call entirely.
- `static/index.html`: zero-dependency dark UI.

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # see .env.example
uvicorn app:app --reload
```

Open http://127.0.0.1:8000, paste a YouTube URL, hit Go.

## Honest limits

- Videos with transcripts disabled return a clear 404; there is no ASR
  fallback here (that lives in my heavier pipelines).
- YouTube sometimes blocks transcript requests from datacenter IPs; run it
  from a residential connection for best results.
- No caching and no queue: it is a single-user tool, not a service.
