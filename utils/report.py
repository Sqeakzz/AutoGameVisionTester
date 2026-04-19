from pathlib import Path
from datetime import datetime
import json
from utils.grok_vision import analyze_screenshot

def generate_report(screenshots, output_folder, mode="balanced", config=None):
    if config is None:
        with open("config.json", "r") as f:
            config = json.load(f)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(output_folder) / f"test_report_{timestamp}.md"
    
    total_tokens = 0
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# 🎮 Game Testing Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Analysis Mode:** {mode.upper()}\n")
        f.write(f"**Screenshots Analyzed:** {len(screenshots)}\n\n")
        f.write("---\n\n")
        
        for i, screenshot in enumerate(screenshots, 1):
            f.write(f"## Screenshot {i}\n")
            f.write(f"![Screenshot]({screenshot.name})\n\n")
            
            print(f"Analyzing screenshot {i}/{len(screenshots)} ({mode})...")
            
            result = analyze_screenshot(
                screenshot, 
                config["grok_api_key"], 
                config.get("max_resolution", "1280x720"),
                mode=mode
            )
            
            if isinstance(result, dict):
                analysis = result.get("analysis", "No analysis returned.")
                tokens = result.get("tokens_used", 0)
            else:
                analysis = result
                tokens = 0
            
            total_tokens += tokens
            
            f.write("**Grok Analysis:**\n\n")
            f.write(f"{analysis}\n\n")
            
            if tokens > 0:
                f.write(f"*Tokens used: {tokens}*\n\n")
            
            f.write("---\n\n")
        
        f.write(f"\n**Total tokens used:** {total_tokens}\n")
        f.write(f"**Report generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"📄 Report saved: {report_path} ({total_tokens} tokens)")