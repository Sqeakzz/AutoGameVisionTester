from pathlib import Path
from datetime import datetime
import json
from utils.grok_vision import analyze_screenshot

def generate_report(screenshots, output_folder, mode="balanced", config=None, progress_callback=None):
    
    if config is None:
        with open("config.json", "r") as f:
            config = json.load(f)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(output_folder) / f"test_report_{timestamp}.html"
    
    total_tokens = 0
    total_high = 0
    total_medium = 0
    total_low = 0
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Grok Game QA Pro Report - {timestamp}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f0f1a; color: #e0e0e0; padding: 20px; max-width: 1200px; margin: auto; }}
        h1 {{ color: #98FF98; text-align: center; }}
        .header {{ background: #1a1a2e; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .screenshot {{ background: #1a1a2e; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .section {{ margin: 15px 0; }}
        .high {{ color: #ff6b6b; }}
        .medium {{ color: #ffd93d; }}
        .low {{ color: #6bcb77; }}
        .fixes {{ color: #4ecdc4; }}
        img {{ max-width: 100%; border-radius: 8px; margin: 15px 0; border: 2px solid #333; }}
        .summary {{ background: #16213e; padding: 20px; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>🎮 Grok Game QA Pro Report</h1>
    
    <div class="header">
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Analysis Mode:</strong> {mode.upper()}</p>
        <p><strong>Screenshots Analyzed:</strong> {len(screenshots)}</p>
        <p><strong>Game Window:</strong> {config.get('game_window_title', 'Unknown')}</p>
    </div>
"""
    
    for i, screenshot in enumerate(screenshots, 1):
        print(f"Analyzing screenshot {i}/{len(screenshots)} ({mode})...")
        
        # Report progress if callback is provided
        if progress_callback:
            progress_callback(i, len(screenshots))

        result = analyze_screenshot(
            screenshot, 
            config["grok_api_key"], 
            config.get("max_resolution", "1280x720"),
            mode=mode
        )
        
        if isinstance(result, dict):
            analysis = result.get("analysis", {})
            tokens = result.get("tokens_used", 0)
        else:
            analysis = {}
            tokens = 0
        
        total_tokens += tokens
        
        html_content += f"""
    <div class="screenshot">
        <h2>📸 Screenshot {i}</h2>
        <img src="../screenshots/{screenshot.name}" alt="Screenshot {i}">
"""
        
        if isinstance(analysis, dict) and "error" not in analysis:
            screen_type = analysis.get("screen_type", "Unknown")
            critical = analysis.get("critical_issues", [])
            medium = analysis.get("medium_issues", [])
            low = analysis.get("low_issues", [])
            fixes = analysis.get("suggested_fixes", [])
            
            html_content += f"<p><strong>Screen Type:</strong> {screen_type}</p>"
            
            if critical:
                html_content += "<div class='section'><h3 class='high'>🔴 Critical Issues (High)</h3><ul>"
                for issue in critical:
                    html_content += f"<li>{issue}</li>"
                html_content += "</ul></div>"
                total_high += len(critical)
            
            if medium:
                html_content += "<div class='section'><h3 class='medium'>🟡 Medium Issues</h3><ul>"
                for issue in medium:
                    html_content += f"<li>{issue}</li>"
                html_content += "</ul></div>"
                total_medium += len(medium)
            
            if low:
                html_content += "<div class='section'><h3 class='low'>🟢 Low Issues</h3><ul>"
                for issue in low:
                    html_content += f"<li>{issue}</li>"
                html_content += "</ul></div>"
                total_low += len(low)
            
            if fixes:
                html_content += "<div class='section'><h3 class='fixes'>🔧 Suggested Fixes</h3><ul>"
                for fix in fixes:
                    html_content += f"<li>{fix}</li>"
                html_content += "</ul></div>"
        
        html_content += "</div>"
    
    # Summary
    html_content += f"""
    <div class="summary">
        <h2>📊 Summary</h2>
        <p><strong>Total Screenshots:</strong> {len(screenshots)}</p>
        <p><strong>High Severity Issues:</strong> {total_high}</p>
        <p><strong>Medium Severity Issues:</strong> {total_medium}</p>
        <p><strong>Low Severity Issues:</strong> {total_low}</p>
        <p><strong>Total Tokens Used:</strong> {total_tokens}</p>
        <p><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n✅ HTML Report saved: {report_path}")
    print(f"   High: {total_high} | Medium: {total_medium} | Low: {total_low}")
    print(f"   Total tokens: {total_tokens}")

    return {
        "path": report_path,
        "high": total_high,
        "medium": total_medium,
        "low": total_low,
        "tokens": total_tokens
    }