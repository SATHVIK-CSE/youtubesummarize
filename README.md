# KS Projects YouTube Summarizer

A small full-stack starter website. The browser sends a YouTube link and summary style to a FastAPI backend. The backend retrieves an available caption track, sends its text to the OpenAI Responses API, and returns the generated summary.

## Easiest start on Windows

Double-click `start-ks-projects.bat` in File Explorer. The first run creates a private Python environment and installs the backend packages, then opens `.env` in Notepad so you can add your OpenAI API key. Save and close Notepad; the launcher starts the backend and opens the website at <http://127.0.0.1:8000>. Keep the backend command window open while using the website. Later, double-click the same file to start it again.

## Run locally from a terminal

You need Python 3.10+ and an OpenAI API key with API billing enabled.

1. Open a terminal in this folder.
2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies and configure the key:

   ```powershell
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

4. Edit `.env`, replacing `your_openai_api_key_here` with your OpenAI API key. Keep this file private; the API key stays on the server and is never sent to the browser.
5. Start the site:

   ```powershell
   uvicorn server:app --reload
   ```

6. Open <http://127.0.0.1:8000>.

`GET /api/health` reports whether the server sees an OpenAI key. `POST /api/summarize` accepts JSON such as `{"url":"https://youtu.be/jNQXAC9IVRw","style":"quick"}`. Styles are `quick`, `detailed`, and `bullets`.

## Caption availability

The backend uses the community `youtube-transcript-api` package to read captions exposed for public videos. This is not an official YouTube transcript API; it may stop working when YouTube changes its systems, and frequent requests can be limited. Videos that are private, restricted, or have no accessible captions cannot be summarized by this captions-based implementation. YouTube's official captions download API requires authorization and permission to edit the video, so it is not a general solution for arbitrary videos.

For a production deployment, use a transcript provider whose terms and access rights fit your use case, add rate limits and abuse protection, configure HTTPS, and set `OPENAI_API_KEY` in the hosting provider's secret settings. Do not commit `.env` or expose the key in frontend code.
