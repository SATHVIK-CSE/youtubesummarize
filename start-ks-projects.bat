@echo off
setlocal
cd /d "%~dp0"
title KS Projects setup

where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 or newer from python.org, then run this file again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo First-time setup: creating the private Python environment...
  py -m venv .venv
  if errorlevel 1 goto :failed
)

if not exist ".venv\Scripts\uvicorn.exe" (
  echo First-time setup: installing the website's backend packages...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  if errorlevel 1 goto :failed
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto :failed
)

if not exist ".env" (
  copy /y .env.example .env >nul
  echo Add your OpenAI API key in the Notepad window, save, and close it.
  start /wait notepad.exe .env
)

findstr /c:"your_openai_api_key_here" .env >nul
if not errorlevel 1 (
  echo Please replace your_openai_api_key_here in .env with your OpenAI API key before starting.
  start notepad.exe .env
  pause
  exit /b 1
)

echo Starting KS Projects. Keep the backend window open while you use the site.
start "KS Projects backend" ".venv\Scripts\python.exe" -m uvicorn server:app --host 127.0.0.1 --port 8000
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8000
exit /b 0

:failed
echo Setup could not finish. Check that Python is installed and that you have an internet connection, then run this file again.
pause
exit /b 1
