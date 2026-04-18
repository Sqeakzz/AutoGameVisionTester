# AutoGameVisionTester

A lightweight CLI tool that automatically captures screenshots from a running game and uses Grok-4 Vision to analyze them for bugs, UI issues, and visual glitches.

Currently built for Unreal Engine games (tested on Unreal Physics).

## Features
- Non-blocking screenshot capture every X seconds
- Queues screenshots in background
- Batch analysis with Grok Vision when you press Ctrl+C
- Generates clean markdown report with images + analysis
- Simple config-driven setup

## Setup
1. Clone the repo
2. Create and activate a virtual environment
3. `pip install -r requirements.txt`
4. Add your Grok API key to `config.json`

## Configuration (`config.json`)
```json
{
  "grok_api_key": "xai-...",
  "screenshot_interval": 8,
  "game_window_title": "Unreal Physics",
  "output_folder": "screenshots"
}
How to Use
Bash
python main.py

Let it run while your game is open
Press Ctrl+C to stop capture and generate the full report

Future Plans

Support for more game engines
Optional simple GUI
More detailed Unreal-specific analysis rules

Early prototype — feedback welcome.