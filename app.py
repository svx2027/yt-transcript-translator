import re
import sys
import json
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import anthropic

app = FastAPI()
client = anthropic.Anthropic()


class TranscriptRequest(BaseModel):
    url: str


def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Could not extract video ID from URL")


def fetch_transcript(video_id: str) -> tuple[str, str]:
    """Fetch transcript via subprocess to get a clean HTTP session."""
    result = subprocess.run(
        [sys.executable, "fetch_transcript.py", video_id],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise Exception(result.stderr.strip() or "Failed to fetch transcript")

    data = json.loads(result.stdout)
    if "error" in data:
        raise Exception(data["error"])
    return data["text"], data["lang"]


def translate_to_english(text: str, source_lang: str) -> str:
    """Use Claude for polished English translation."""
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Translate the following transcript from {source_lang} to fluent, natural English. "
                    "Preserve paragraph breaks. Output ONLY the translated text, nothing else.\n\n"
                    f"{text}"
                ),
            }
        ],
    )
    return message.content[0].text


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=open("static/index.html").read())


@app.post("/api/transcript")
def get_transcript(req: TranscriptRequest):
    try:
        video_id = extract_video_id(req.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        text, lang = fetch_transcript(video_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch transcript: {e}")

    if lang != 'en':
        try:
            text = translate_to_english(text, lang)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Translation failed: {e}")

    return {"transcript": text, "original_language": lang, "video_id": video_id}
