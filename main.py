import time
from pathlib import Path
import json
from queue import Queue
import threading
from utils.capture import capture_game_window
from utils.grok_vision import analyze_screenshot
from utils.report import generate_report

def main():
    with open("config.json", "r") as f:
        config = json.load(f)
    
    screenshots_dir = Path("screenshots")
    reports_dir = Path("reports")
    screenshots_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)
    
    screenshot_queue = Queue()
    stop_event = threading.Event()
    
    print(f"📸 Starting capture every {config['screenshot_interval']} seconds (non-blocking). Press Ctrl+C to stop and analyze.\n")
    
    def capture_loop():
        while not stop_event.is_set():
            start_time = time.time()
            try:
                screenshot_path = capture_game_window(config["game_window_title"], str(screenshots_dir))
                if screenshot_path:
                    screenshot_queue.put(screenshot_path)
                    print(f"📸 Queued: {screenshot_path.name}")
            except Exception as e:
                print(f"❌ Capture error: {e}")
            
            elapsed = time.time() - start_time
            sleep_time = max(0.0, config["screenshot_interval"] - elapsed)
            time.sleep(sleep_time)
    
    # Start capture in background thread
    capture_thread = threading.Thread(target=capture_loop, daemon=True)
    capture_thread.start()
    
    try:
        while True:
            time.sleep(1)  # Keep main thread alive
    except KeyboardInterrupt:
        print("\n⏹️ Stopping capture and starting batch analysis...")
        stop_event.set()
        capture_thread.join(timeout=2)
        
        # Process queued screenshots
        screenshots = []
        while not screenshot_queue.empty():
            screenshots.append(screenshot_queue.get())
        
        if screenshots:
            print(f"📊 Analyzing {len(screenshots)} screenshots in batch...")
            generate_report(screenshots, str(reports_dir))
            print(f"✅ Batch report complete with {len(screenshots)} screenshots")
        else:
            print("No screenshots were captured.")

if __name__ == "__main__":
    main()