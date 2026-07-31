"""Standalone script to fetch a YouTube transcript. Called via subprocess to avoid uvicorn session issues."""
import sys
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

video_id = sys.argv[1]
ytt = YouTubeTranscriptApi()
formatter = TextFormatter()

transcript_list = ytt.list(video_id)

# Try English first
try:
    transcript = transcript_list.find_transcript(['en'])
    snippets = transcript.fetch()
    text = formatter.format_transcript(snippets)
    print(json.dumps({"text": text, "lang": "en"}))
    sys.exit(0)
except Exception:
    pass

# Get any available transcript
for transcript in transcript_list:
    snippets = transcript.fetch()
    text = formatter.format_transcript(snippets)
    print(json.dumps({"text": text, "lang": transcript.language_code}))
    sys.exit(0)

print(json.dumps({"error": "No transcript available"}))
sys.exit(1)
