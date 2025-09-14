<h1 align="center">movie2manual</h1>

<p align="center">
  <a href="README.md">🇯🇵 日本語</a> · 
  <a href="README_EN.md">🇺🇸 English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" />
  <img src="https://img.shields.io/badge/ffmpeg-required-orange" />
  <img src="https://img.shields.io/badge/LLM-Gemini%20%7C%20OpenAI%20API%20Compatible%20%7C%20Ollama-green" />
</p>

Video-to-manual tool that analyzes videos, generates a draft manual (JSON), extracts screenshots via ffmpeg, and outputs Markdown.

## Features
- Generate draft manual with LLM (Gemini / OpenAI-compatible / Ollama)
- Extract screenshots by timestamps with ffmpeg
- Save body text as Markdown (supports PDF export via python-markdown + WeasyPrint)

## Requirements
- Python 3.9+
- ffmpeg
- LLM provider configured via `.env`

## Setup
```bash
git clone https://github.com/Tomatio13/movie2manual.git
cd movie2manual
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set LLM_PROVIDER/LLM_MODEL/LLM_API_KEY, etc.
```

## Environment variables (.env)
- LLM_PROVIDER: gemini | openai | ollama
- LLM_BASE_URL: for OpenAI-compatible or Ollama (e.g., https://api.openai.com/v1, http://localhost:11434/v1)
- LLM_MODEL: e.g., models/gemini-2.5-flash, gpt-4o-mini, llama3.1
- LLM_API_KEY: required for Gemini and typically OpenAI-compatible; not required for Ollama

## Usage
```bash
python main.py --video /path/to/video.mp4
```

### PDF export (optional)
- This repo converts Markdown to HTML via `markdown.markdown()` and renders PDF with WeasyPrint.
- Python deps: `markdown`, `weasyprint` (already in requirements.txt)
- System deps (Ubuntu example): `libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libssl-dev`

Examples:
```bash
python main.py --video /path/to/video.mp4 --export-pdf
python main.py --video /path/to/video.mp4 --export-pdf --pdf-output ./manual_assets/manual.pdf
```

### Quickstart (per provider)
```bash
# Gemini
echo -e "LLM_PROVIDER=gemini\nLLM_MODEL=models/gemini-2.5-flash\nLLM_API_KEY=AIza..." > .env
python main.py --video /path/to/video.mp4

# OpenAI compatible
echo -e "LLM_PROVIDER=openai\nLLM_BASE_URL=https://api.openai.com/v1\nLLM_MODEL=gpt-4o-mini\nLLM_API_KEY=sk-..." > .env
python main.py --video /path/to/video.mp4

# Ollama
echo -e "LLM_PROVIDER=ollama\nLLM_BASE_URL=http://localhost:11434/v1\nLLM_MODEL=llama3.1" > .env
python main.py --video /path/to/video.mp4
```

### Sample output
- `manual_assets/manual.md`
- `manual_assets/step01_start.png`

## Troubleshooting
- JSON extraction failure: adjust provider or prompt.
- ffmpeg not found: install ffmpeg and retry.
- Missing env vars: set `LLM_PROVIDER`, and `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY` if needed.
- Invalid --video path: specify an existing file.
- PDF export fails (WeasyPrint): ensure Python packages `markdown`, `weasyprint` are installed.
- PDF export fails (system deps): install `libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libssl-dev`.
- n8n MCP Client default timeout is 60s; increase to 600s for long videos (set timeout in the MCP Client options).

## License
MIT
