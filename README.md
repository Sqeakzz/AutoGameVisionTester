# AutoGameVisionTester

An automated Unreal Engine QA tool powered by Grok-4 Vision.

It captures screenshots from your game window in real-time, uses Smart Capture to skip duplicate frames, and generates detailed QA reports with Grok Vision analysis.

## Features

- **Smart Capture** — Automatically skips similar screenshots using perceptual hashing (saves tokens)
- **Variable Resolution** — Choose between Budget (960x540), Balanced (1280x720), or Full Res (1920x1080)
- **Live Status Popup** — Shows current queue count and runtime
- **Global Hotkey** — Press `Ctrl + Alt + S` anytime to trigger batch analysis
- **Clear Data** — Quickly wipe screenshots and reports folders
- **Non-blocking Capture** — Tool continues running while you play
- **Markdown Reports** — Clean, developer-friendly QA reports with embedded screenshots

## Requirements

- Python 3.10+
- Grok API Key (from https://console.x.ai)
- Unreal Engine game running

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Sqeakzz/AutoGameVisionTester.git
   cd AutoGameVisionTester

Install dependencies:Bashpip install -r requirements.txt
Add your Grok API key in config.json:JSON{
  "grok_api_key": "your-key-here",
  ...
}

How to Use

Run the tool:Bashpython main.py
Choose 1. Preview Mode from the menu.
Play your game. The tool will automatically capture and filter screenshots.
When you're ready for analysis, press Ctrl + Alt + S.
A markdown report will be generated in the reports/ folder.

Configuration
You can change settings from the menu:

screenshot_interval — Time between capture attempts (seconds)
max_resolution — Choose from 960x540, 1280x720, or 1920x1080
game_window_title — Name of your game window

Hotkeys

Ctrl + Alt + S — Stop capture and start batch analysis

Example Output
Reports include:

Screenshot count
Resolution mode used
Grok Vision analysis for each frame
Practical QA feedback

Future Plans

LowRes + Quick/Deep mode toggle
Support for more engines (Unity, Godot)
Automatic bug severity tagging


Built with ❤️ and Grok-4 Vision