import json
import time
from pathlib import Path
from utils.capture import take_screenshot
from utils.grok_vision import analyze_screenshot
from utils.report import generate_report

def main():
    # Load config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    api_key = config["grok_api_key"]
    interval = config["screenshot_interval"]
    game_title = config["game_window_title"]
    output_folder = Path(config["output_folder"])
    output_folder.mkdir(exist_ok=True)
    
    print(f"🚀 AutoGameVisionTester started - Targeting: {game_title}")
    print(f"Screenshot every {interval} seconds. Press Ctrl+C to stop.\n")
    
    screenshots = []
    
    try:
        while True:
            screenshot_path = take_screenshot(game_title)
            if screenshot_path:
                print(f"📸 Captured: {screenshot_path.name}")
                analysis = analyze_screenshot(screenshot_path, api_key)
                screenshots.append({
                    "screenshot": screenshot_path,
                    "analysis": analysis
                })
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n⏹️  Stopping test session...")
        if screenshots:
            generate_report(screenshots, output_folder)
        print("✅ Report generated!")

if __name__ == "__main__":
    main()