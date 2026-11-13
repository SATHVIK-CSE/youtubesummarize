# KS Projects YouTube Summarizer

A small full-stack site. The browser sends a YouTube link and summary style to a FastAPI backend. The backend retrieves an available caption track and sends its text to Gemini to generate the summary.

## Deploy to Cloudflare Workers

This repository is configured as a Python Worker with static assets. Cloudflare Workers Builds can deploy it from GitHub using `uv run --group dev pywrangler deploy`.

After the first deployment, add `GEMINI_API_KEY` under **Workers & Pages → youtubesummarize → Settings → Variables and Secrets** as an encrypted secret. `GEMINI_MODEL` defaults to `gemini-3.8-flash` and can be changed in `wrangler.jsonc`. Keep API keys out of Git.

## Run locally on Windows

You need Python 3.10+ and a Gemini API key.

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install packages and configure the key:

   ```powershell
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

3. Edit `.env`, replacing the placeholder with your Gemini API key. Keep the file private.
4. Start the app with `uvicorn server:app --reload`, then open <http://127.0.0.1:8000>.

`GET /api/health` reports whether the server sees a Gemini key. `POST /api/summarize` accepts JSON such as `{"url":"https://youtu.be/jNQXAC9IVRw","style":"quick"}`. Styles are `quick`, `detailed`, and `bullets`.

## Caption availability

The backend uses the community `youtube-transcript-api` package to read captions exposed for public videos. This is not an official YouTube transcript API; it may stop working when YouTube changes its systems, and frequent requests can be limited. Videos that are private, restricted, or have no accessible captions cannot be summarized by this captions-based implementation.
