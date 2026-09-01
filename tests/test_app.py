"""Error-handling tests for /api/transcript: a private, deleted, or transcript-less
video must come back as a clean 404, never a raw crash or 500."""
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import app  # noqa: E402

client = TestClient(app)


def _fake_run(returncode, stdout="", stderr=""):
    return subprocess.CompletedProcess(
        args=["fetch_transcript.py"], returncode=returncode, stdout=stdout, stderr=stderr
    )


def test_invalid_url_returns_400():
    response = client.post("/api/transcript", json={"url": "not a youtube url"})
    assert response.status_code == 400


def test_video_with_transcripts_disabled_returns_404():
    """fetch_transcript.py reports its own 'no transcript' case as a clean
    exit-1 JSON error (e.g. a private or unavailable video with no captions)."""
    fake = _fake_run(1, stdout=json.dumps({"error": "No transcript available"}))
    with patch("app.subprocess.run", return_value=fake):
        response = client.post("/api/transcript", json={"url": "https://youtu.be/aaaaaaaaaaa"})
    assert response.status_code == 404
    assert "No transcript available" in response.json()["detail"]


def test_unreadable_video_does_not_crash_the_request():
    """A private/deleted video makes youtube_transcript_api raise inside the
    subprocess before it ever writes JSON (non-zero exit, traceback on stderr).
    The endpoint must still degrade to a 404, not bubble up a 500."""
    fake = _fake_run(1, stdout="", stderr="youtube_transcript_api._errors.VideoUnavailable: ...")
    with patch("app.subprocess.run", return_value=fake):
        response = client.post("/api/transcript", json={"url": "https://youtu.be/bbbbbbbbbbb"})
    assert response.status_code == 404
    assert "VideoUnavailable" in response.json()["detail"]


def test_translation_failure_returns_500_not_a_raw_exception():
    """A non-English transcript that fails to translate should still come back
    as a handled HTTPException, not an unhandled exception."""
    fake = _fake_run(0, stdout=json.dumps({"text": "contenu francais", "lang": "fr"}))
    with patch("app.subprocess.run", return_value=fake), \
         patch("app.translate_to_english", side_effect=Exception("model unavailable")):
        response = client.post("/api/transcript", json={"url": "https://youtu.be/ccccccccccc"})
    assert response.status_code == 500
    assert "Translation failed" in response.json()["detail"]
