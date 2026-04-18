from pathlib import Path
from datetime import datetime
import markdown

def generate_report(screenshots: list, output_folder: Path):
    """
    Generates a nice markdown report from all the screenshots + analyses.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = output_folder / f"test_report_{timestamp}.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Game Testing Report - {timestamp}\n\n")
        f.write(f"**Total screenshots analyzed:** {len(screenshots)}\n\n")
        
        for i, entry in enumerate(screenshots, 1):
            f.write(f"## Screenshot {i}\n")
            filename = entry['screenshot'].name
            f.write(f"![Screenshot](screenshots/{filename})\n\n")
            f.write(f"**Grok Analysis:**\n")
            f.write(entry["analysis"] + "\n\n")
            f.write("---\n\n")
    
    print(f"✅ Report saved: {report_path}")
    
    # Optional HTML version
    html_path = output_folder / f"test_report_{timestamp}.html"
    html_content = markdown.markdown(open(report_path, "r", encoding="utf-8").read())
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(f"<html><body>{html_content}</body></html>")
    
    print(f"✅ HTML report also saved: {html_path}")