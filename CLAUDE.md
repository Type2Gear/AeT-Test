# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Heart Rate Drift Test Analyzer — helps runners find their aerobic threshold by comparing the pace-to-heart-rate ratio between two sections of a workout. Supports `.fit` and `.gpx` file formats.

## Commands

```sh
# Install dependencies
pip install -r requirements.txt

# Run the web server (http://localhost:5001)
python web/app.py

# CLI analysis
python src/heart_rate_analyzer.py workout.fit \
    --section1-start 00:10:00 --section1-end 00:15:00 \
    --section2-start 00:30:00 --section2-end 00:35:00 \
    --plot --plot-file output.png

# Run tests
python -m pytest tests/
```

## Architecture

**Hybrid frontend/backend design:**

- `src/heart_rate_analyzer.py` — Core `HeartRateAnalyzer` class. Parses `.fit` (fitparse) and `.gpx` (gpxpy) files into pandas DataFrames, computes per-section averages (HR, pace, pace-to-HR ratio), and generates matplotlib plots.

- `web/app.py` — Flask REST API (port 5001). Routes: `POST /preview` (load file), `POST /analyze` (compute section metrics + generate plot), `GET /plot` (serve plot image). Stateless; temp files deleted after each request.

- `web/static/js/heart_rate_analyzer.js` — Frontend `HeartRateAnalyzer` class. Parses files **client-side** (fit-file-parser, gpxparser via CDN), renders dual-axis Chart.js preview, then sends selected section time ranges to the backend for analysis.

**Data flow:** File is parsed client-side for preview → user picks two sections via range sliders → section ranges POSTed to `/analyze` → backend calculates averages and returns JSON + plot URL → results displayed in table.

## Key Details

- **Pace-to-HR ratio change** is the core metric: <3.5% = below threshold, 3.5–5% = at threshold, >5% = above threshold.
- Times are in seconds from workout start internally; displayed as HH:MM:SS.
- Max upload size: 16MB.
- Frontend libraries loaded from CDN (Bootstrap 5, Chart.js, fit-file-parser, gpxparser).
- Tests in `tests/test_heart_rate_analyzer.py` are minimal and may reference methods not in current code.
