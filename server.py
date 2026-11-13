"""KS Projects YouTube summarizer API."""
from __future__ import annotations

import os
import re
import logging
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()
app = FastAPI(title="KS Projects YouTube Summarizer", version="1.0.0")
logger = logging.getLogger(__name__)


class SummaryRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)
    style: str = Field(default="quick", pattern="^(quick|detailed|bullets)$")


def get_video_id(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())
    host = (parsed.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    video_id = ""
    if host == "youtube.com":
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            parts = parsed.path.split("/")
            video_id = parts[2] if len(parts) > 2 else ""
    elif host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise HTTPException(status_code=400, detail="That does not look like a valid YouTube video link.")
    return video_id


def get_transcript(video_id: str) -> tuple[str, str]:
    try:
        api = YouTubeTranscriptApi()
        tracks = api.list(video_id)
        try:
            track = tracks.find_transcript(["en"])
        except Exception:
            track = next(iter(tracks), None)
        if track is None:
            raise HTTPException(status_code=422, detail="No captions are available for this video.")
        fetched = track.fetch()
        text = " ".join(item.text.strip() for item in fetched if item.text.strip())
        if not text:
            raise HTTPException(status_code=422, detail="The available captions were empty.")
        return text, getattr(track, "language", "Caption language")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Could not retrieve captions. The video may be private, restricted, or have captions disabled. Please try another public video with captions.",
        ) from exc


def make_summary(transcript: str, style: str, key: str | None = None, model: str | None = None) -> str:
    key = key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="The server is missing GEMINI_API_KEY. Add it to the Cloudflare Worker secrets.")
    model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    instructions = {
        "quick": "Write a concise recap in 4-6 sentences, followed by 3 key takeaways.",
        "detailed": "Write structured, detailed notes with a short overview, important points, examples, and a brief conclusion.",
        "bullets": "Give a one-sentence overview followed by 5-8 specific, useful bullet-point takeaways.",
    }[style]
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model,
            contents=(
                "Summarize the supplied YouTube transcript faithfully. Do not invent facts or claim details that are not in the transcript. "
                "If the transcript is incomplete or unclear, say so. " + instructions +
                "\n\nTranscript:\n" + transcript[:120_000]
            ),
            config=types.GenerateContentConfig(
                max_output_tokens=1400 if style == "detailed" else 800,
            ),
        )
        summary = (response.text or "").strip()
        if not summary:
            raise HTTPException(status_code=502, detail="Gemini returned an empty summary. Please try again.")
        return summary
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Gemini summary request failed")
        raise HTTPException(status_code=502, detail="Gemini could not complete the summary. Check the Gemini API key, model access, and free-tier limits in Google AI Studio.") from exc


@app.get("/")
async def home(request: Request):
    env = request.scope.get("env")
    if env is None:
        from fastapi.responses import FileResponse
        from pathlib import Path
        return FileResponse(Path(__file__).resolve().parent / "index.html")
    asset = await env.ASSETS.fetch("https://assets.local/index.html")
    return Response(content=await asset.bytes(), status_code=asset.status, headers=asset.headers)


@app.get("/api/health")
def health(request: Request):
    env = request.scope.get("env")
    return {"ok": True, "ai_configured": bool(getattr(env, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY"))}


@app.post("/api/summarize")
def summarize(body: SummaryRequest, request: Request):
    video_id = get_video_id(body.url)
    transcript, language = get_transcript(video_id)
    env = request.scope.get("env")
    summary = make_summary(
        transcript,
        body.style,
        key=getattr(env, "GEMINI_API_KEY", None),
        model=getattr(env, "GEMINI_MODEL", None),
    )
    return {
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "title": "Video summary",
        "language": f"Captions: {language}",
        "summary": summary,
    }
