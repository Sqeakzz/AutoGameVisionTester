from pathlib import Path
from datetime import datetime
import json
from utils.grok_vision import analyze_screenshot

def generate_report(screenshots, output_folder):
    """Generate markdown report with real Grok Vision analysis"""
    # Load config to get api_key
    with open("config.json", "r") as f:
        config = json.load(f)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(output_folder) / f"test_report_{timestamp}.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Game Testing Report - {timestamp}\n\n")
        f.write(f"**Total screenshots analyzed:** {len(screenshots)}\n\n")
        
        for i, screenshot in enumerate(screenshots, 1):
            f.write(f"## Screenshot {i}\n")
            f.write(f"![Screenshot]({screenshot.name})\n\n")
            
            print(f"Analyzing screenshot {i}/{len(screenshots)}...")
            analysis = analyze_screenshot(screenshot, config["grok_api_key"])
            
            if analysis:
                f.write("**Grok Analysis:**\n")
                f.write(f"{analysis}\n\n")
            else:
                f.write("**Grok Analysis:**\n")
                f.write("No analysis returned (API error or timeout).\n\n")
            
            f.write("---\n\n")
    
    print(f"📄 Full report generated: {report_path}")