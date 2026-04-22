import time
from pathlib import Path
import json
from queue import Queue
import threading
import tkinter as tk
from pynput import keyboard
import shutil
from PIL import Image
import imagehash
from utils.capture import capture_game_window
from utils.grok_vision import analyze_screenshot
from utils.report import generate_report
import os
import subprocess
import pygetwindow as gw
import sys
import logging

# === Basic Logging Setup (file + console) ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("visiontester.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AutoGameVisionTester")

capture_running = False
started_from_dashboard = False   # ← Add this
capture_start_time = None
current_queue_size = 0
analysis_progress = {"current": 0, "total": 0}
# Thread safety lock
state_lock = threading.Lock()

def main():
    global config
    config = load_config()
    
    
    if len(sys.argv) > 1 and sys.argv[1] == "--capture":
        run_preview_mode(config)
        return
    
    main_menu()

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def save_to_history(report_path, mode, high, medium, low, tokens):
    """Save report metadata to history.json"""
    history_file = Path("history.json")
    
    entry = {
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "report_file": str(report_path),
        "mode": mode,
        "high_issues": high,
        "medium_issues": medium,
        "low_issues": low,
        "tokens_used": tokens
    }
    
    if history_file.exists():
        with open(history_file, "r") as f:
            history = json.load(f)
    else:
        history = []
    
    history.append(entry)
    
    # Keep only last 50 reports
    if len(history) > 50:
        history = history[-50:]
    
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

def view_history():
    """Display history and allow opening reports"""
    history_file = Path("history.json")
    
    if not history_file.exists():
        print("\nNo history found yet.")
        return
    
    with open(history_file, "r") as f:
        history = json.load(f)
    
    if not history:
        print("\nNo reports in history.")
        return
    
    print("\n=== Report History ===")
    for i, entry in enumerate(history, 1):
        print(f"{i}. {entry['date']} | {entry['mode']} | High: {entry['high_issues']} | Medium: {entry['medium_issues']} | Low: {entry['low_issues']} | Tokens: {entry['tokens_used']}")
    
    print("\nEnter number to open report, or 0 to go back:")
    try:
        choice = int(input("> ").strip())
        if choice == 0:
            return
        if 1 <= choice <= len(history):
            report_path = history[choice - 1]["report_file"]
            if Path(report_path).exists():
                print(f"\nOpening: {report_path}")
                if os.name == 'nt':  # Windows
                    os.startfile(report_path)
                else:
                    subprocess.run(['xdg-open', report_path])
            else:
                print("Report file not found.")
        else:
            print("Invalid choice.")
    except:
        print("Invalid input.")

class StatusWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VisionTester")
        self.root.geometry("260x95+0+0")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        self.root.configure(bg="#0D0D0D")

        # Main mint green frame with purple glow
        self.main_frame = tk.Frame(
            self.root,
            bg="#98FF98",
            bd=3,
            relief="solid",
            highlightbackground="#9D4EDD",
            highlightthickness=4
        )
        self.main_frame.pack(padx=4, pady=4, fill="both", expand=True)

        # Two-column layout
        top_frame = tk.Frame(self.main_frame, bg="#98FF98")
        top_frame.pack(padx=10, pady=10, fill="x")

        # Left - Queue
        left_frame = tk.Frame(top_frame, bg="#98FF98")
        left_frame.pack(side="left", expand=True)
        
        self.queue_label = tk.Label(
            left_frame, 
            text="📈 0", 
            font=("Segoe UI", 16, "bold"),
            bg="#98FF98",
            fg="#1A1A2E"
        )
        self.queue_label.pack()
        
        tk.Label(left_frame, text="Queued", font=("Segoe UI", 8), bg="#98FF98", fg="#1A1A2E").pack()

        # Right - Runtime
        right_frame = tk.Frame(top_frame, bg="#98FF98")
        right_frame.pack(side="right", expand=True)
        
        self.time_label = tk.Label(
            right_frame, 
            text="🕐 00:00", 
            font=("Segoe UI", 16, "bold"),
            bg="#98FF98",
            fg="#1A1A2E"
        )
        self.time_label.pack()
        
        tk.Label(right_frame, text="Runtime", font=("Segoe UI", 8), bg="#98FF98", fg="#1A1A2E").pack()

        self.start_time = time.time()
        self.timer_id = None
        self.update_timer()

    def update_timer(self):
        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        self.time_label.config(text=f"🕐 {mins:02d}:{secs:02d}")
        self.timer_id = self.root.after(1000, self.update_timer)

    def cancel_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def update_queue(self, count):
        self.queue_label.config(text=f"📈 {count}")

    def close(self):
            self.cancel_timer()
            try:
                self.root.destroy()
            except:
                pass  # Already destroyed or closed


def clear_data():
    try:
        shutil.rmtree("screenshots", ignore_errors=True)
        shutil.rmtree("reports", ignore_errors=True)
        Path("screenshots").mkdir(exist_ok=True)
        Path("reports").mkdir(exist_ok=True)
        
        # Also clear history.json (same as dashboard)
        if Path("history.json").exists():
            Path("history.json").write_text("[]")
        
        print("✅ Cleared screenshots, reports, and history.")
    except Exception as e:
        print(f"❌ Clear error: {e}")


def run_preview_mode(config, show_status_window=True):
    print(f"\n📸 Preview Mode — every {config['screenshot_interval']} seconds")
    print(f"   Resolution: {config.get('max_resolution', '1280x720')}")
    print("   Press Ctrl + Alt + S to trigger batch analysis.\n")
    
    Path("screenshots").mkdir(exist_ok=True)
    
    screenshot_queue = Queue()
    stop_event = threading.Event()
    hotkey_pressed = threading.Event()

    global capture_running, started_from_dashboard
    capture_running = True
    started_from_dashboard = False
    
    # Only create StatusWindow if requested (False when started from dashboard)
    status_win = None
    if show_status_window:
        status_win = StatusWindow()
    
    last_hash = None
    hash_threshold = 18

    def capture_loop():
        nonlocal last_hash
        while not stop_event.is_set() and capture_running:
            try:
                screenshot_path = capture_game_window(
                    config["game_window_title"], 
                    "screenshots"
                )
                if screenshot_path:
                    img = Image.open(screenshot_path)

                    res = config.get("max_resolution", "1280x720")
                    try:
                        max_width, max_height = map(int, res.split("x"))
                    except:
                        max_width, max_height = 1280, 720

                    ratio = min(max_width / img.width, max_height / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                    img.save(screenshot_path, "PNG")

                    current_hash = imagehash.average_hash(img)
                    if last_hash is None or (current_hash - last_hash) > hash_threshold:
                        screenshot_queue.put(screenshot_path)
                        last_hash = current_hash

                        global current_queue_size
                        current_queue_size = screenshot_queue.qsize()
                        
                        if status_win:  # Only update if window exists
                            status_win.update_queue(screenshot_queue.qsize())
                            
                        
                        print(f"📸 Captured + Kept → {screenshot_path.name}")
                    else:
                        screenshot_path.unlink()
                        print(f"📸 Captured + Skipped (duplicate)")

            except Exception as e:
                print(f"Capture error: {e}")

            time.sleep(config["screenshot_interval"])

    capture_thread = threading.Thread(target=capture_loop, daemon=True)
    capture_thread.start()

    def on_hotkey():
        if not stop_event.is_set():
            print("\n⏹️ Hotkey pressed - Stopping capture...")
            stop_event.set()
            hotkey_pressed.set()

    def check_for_hotkey():
        if hotkey_pressed.is_set():
            if status_win:
                status_win.close()
            handle_mode_selection()
            return
        
        # Always reschedule (even without StatusWindow)
        if status_win:
            status_win.root.after(100, check_for_hotkey)
        else:
            # Fallback polling when no GUI window
            threading.Timer(0.1, check_for_hotkey).start()

    def handle_mode_selection():
        global started_from_dashboard, capture_running
        
        if started_from_dashboard:
            print("\n✅ Analysis mode selection is now handled in the Dashboard GUI.")
            started_from_dashboard = False
            return
        
        # Normal CLI flow (only runs if NOT started from dashboard)
        mode_input = input("Choose mode (quick / balanced / deep) [default: balanced]: ").strip().lower()
        mode = mode_input if mode_input in ["quick", "balanced", "deep"] else "balanced"
        
        screenshots = []
        while not screenshot_queue.empty():
            screenshots.append(screenshot_queue.get())

        if screenshots:
            print(f"\n📊 Analyzing {len(screenshots)} screenshots in **{mode.upper()}** mode...")
            result = generate_report(screenshots, "reports", mode=mode, config=config)
            
            if result:
                save_to_history(
                    report_path=result["path"],
                    mode=mode,
                    high=result["high"],
                    medium=result["medium"],
                    low=result["low"],
                    tokens=result["tokens"]
                )
                print(f"✅ Batch report complete ({mode} mode)")
            else:
                print("Report generation failed.")
        else:
            print("No new screenshots were captured.")

    hotkey_listener = keyboard.GlobalHotKeys({'<ctrl>+<alt>+s': on_hotkey})
    hotkey_listener.start()

    check_for_hotkey()
    if status_win:
        status_win.root.mainloop()

    stop_event.set()
    hotkey_listener.stop()
    capture_thread.join(timeout=3)

def list_running_windows():
    """List all currently open windows to help user find game title"""
    try:
        windows = gw.getAllWindows()
        
        if not windows:
            print("\nNo windows detected.")
            return
            
        print("\n=== Currently Open Windows ===")
        count = 0
        for window in windows:
            if window.title.strip():  # Only show windows with titles
                count += 1
                print(f"{count}. {window.title}")
        
        if count == 0:
            print("No titled windows found.")
        else:
            print(f"\nFound {count} windows. Use part of the title in your config.")
            
    except Exception as e:
        print(f"Error listing windows: {e}")

def main_menu():
    global config
    while True:
        res = config.get("max_resolution", "1280x720")
        print("\n=== AutoGameVisionTester ===")
        print(f"1. Preview Mode ({res})")
        print("2. Edit Config")
        print("3. Clear Data")
        print("4. View History")
        print("5. Launch Dashboard")
        print("6. Exit")
        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":
            run_preview_mode(config)
        elif choice == "2":
            edit_config()
        elif choice == "3":
            clear_data()
        elif choice == "4":
            view_history()
        elif choice == "5":
            launch_dashboard()
        elif choice == "6":
            print("Goodbye!")
            break

def launch_dashboard():
    import webbrowser
    import threading
    import time
    
    def start_server():
        import http.server
        import socketserver
        import json as json_module
        
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
            # Suppress default server logging (127.0.0.1 - - [...])
                pass
            def do_POST(self):
                if self.path == '/save-config':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    
                    try:
                        new_config = json_module.loads(post_data.decode('utf-8'))
                        
                        if save_config(new_config):
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(b'{"status": "success"}')
                        else:
                            self.send_response(500)
                            self.end_headers()
                    except Exception as e:
                        self.send_response(400)
                        self.end_headers()
                        print(f"Error processing config save: {e}")
                
                elif self.path == '/start-capture':
                    try:
                        start_capture_from_dashboard()
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(b'{"status": "started"}')
                    except Exception as e:
                        self.send_response(500)
                        self.end_headers()
                        print(f"Error starting capture: {e}")

                elif self.path == '/stop-capture':
                    try:
                        stop_capture_from_dashboard()
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(b'{"status": "stopped"}')
                    except Exception as e:
                        self.send_response(500)
                        self.end_headers()
                        print(f"Error stopping capture: {e}")

                elif self.path == '/run-analysis':
                    try:
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        data = json_module.loads(post_data.decode('utf-8'))
                        mode = data.get('mode', 'balanced')
                        
                        from pathlib import Path
                        from utils.report import generate_report
                        
                        # Get screenshots from current capture session only
                        all_screenshots = sorted(Path("screenshots").glob("*.png"))
                        
                        current_session_screenshots = []
                        
                        if capture_start_time:
                            for screenshot in all_screenshots:
                                if screenshot.stat().st_mtime >= capture_start_time:
                                    current_session_screenshots.append(screenshot)
                        else:
                            # Fallback: use last 10 if no timestamp
                            current_session_screenshots = all_screenshots[-10:] if len(all_screenshots) > 10 else all_screenshots
                        
                        if not current_session_screenshots:
                            self.send_response(400)
                            self.end_headers()
                            self.wfile.write(b'{"error": "No screenshots found"}')
                            return
                        
                        # Progress callback
                        def progress_updater(current, total):
                            analysis_progress["current"] = current
                            analysis_progress["total"] = total
                        
                        # Run analysis
                        result = generate_report(
                            current_session_screenshots, 
                            "reports", 
                            mode=mode, 
                            config=config,
                            progress_callback=progress_updater
                        )
                        
                        if result:
                            save_to_history(
                                report_path=result["path"],
                                mode=mode,
                                high=result["high"],
                                medium=result["medium"],
                                low=result["low"],
                                tokens=result["tokens"]
                            )
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(b'{"status": "success"}')
                        else:
                            self.send_response(500)
                            self.end_headers()
                            
                    except Exception as e:
                        self.send_response(500)
                        self.end_headers()
                        print(f"Error running analysis: {e}")
                elif self.path == '/clear-data':
                    try:
                        import shutil
                        from pathlib import Path
                        
                        # Clear folders
                        for folder in ["screenshots", "reports"]:
                            if Path(folder).exists():
                                shutil.rmtree(folder)
                                Path(folder).mkdir()
                        
                        # Clear history
                        if Path("history.json").exists():
                            Path("history.json").write_text("[]")
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(b'{"status": "success"}')
                    except Exception as e:
                        self.send_response(500)
                        self.end_headers()
                        print(f"Error clearing data: {e}")
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_GET(self):
                if self.path == '/detect-windows':
                    try:
                        windows = get_running_windows()
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(windows).encode('utf-8'))
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                elif self.path == '/get-session-screenshots':
                    try:
                        from pathlib import Path
                        import time as time_module
                        
                        all_screenshots = sorted(Path("screenshots").glob("*.png"))
                        
                        # Filter to only screenshots from current session
                        current_session = []
                        if capture_start_time:
                            for screenshot in all_screenshots:
                                if screenshot.stat().st_mtime >= capture_start_time:
                                    current_session.append(screenshot)
                        else:
                            current_session = all_screenshots[-5:]  # fallback
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"count": len(current_session)}).encode('utf-8'))
                        
                    except Exception as e:
                        self.send_response(500)
                        self.end_headers()
                        print(f"Error getting session screenshots: {e}")

                elif self.path == '/get-queue-count':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"queue_size": current_queue_size}).encode('utf-8'))
                elif self.path == '/analysis-progress':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(analysis_progress).encode('utf-8'))
                else:
                    # Serve normal files
                    super().do_GET()

        PORT = 8000
        Handler = CustomHandler
        
        try:
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print(f"\n🌐 Dashboard server running at http://localhost:{PORT}")
                print("📌 Dashboard is now active. You can close this terminal when done or Ctrl + C for menu.")
                httpd.serve_forever()
        except OSError:
            print(f"\n🌐 Dashboard already running at http://localhost:{PORT}")
            print("📌 You can keep using the dashboard in your browser.")
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    time.sleep(1)
    
    dashboard_url = "http://localhost:8000/dashboard.html"
    print(f"🚀 Opening dashboard at: {dashboard_url}")
    webbrowser.open(dashboard_url)
    
    # Just hang until user closes terminal
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Returning to main menu...")

def edit_config():
    global config
    config = load_config()
    keys = list(config.keys())

    while True:
        print("\n=== Current Config ===")
        for i, key in enumerate(keys, 1):
            print(f"  {i}. {key}: {config[key]}")
        print(f"  {len(keys) + 1}. List Running Windows (to find game title)")
        print(f"  {len(keys) + 2}. Done")

        choice = input(f"\nChoose option (1-{len(keys) + 2}): ").strip()

        if choice == str(len(keys) + 2):
            break

        if choice == str(len(keys) + 1):
            list_running_windows()
            continue

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(keys):
                key = keys[idx]
                
                # Special handling for max_resolution
                if key == "max_resolution":
                    print("\n=== Max Resolution ===")
                    print("1. Budget     (960x540)")
                    print("2. Balanced   (1280x720)")
                    print("3. Full Res   (1920x1080)")
                    
                    res_choice = input("\nChoose resolution (1-3): ").strip()
                    
                    if res_choice == "1":
                        config[key] = "960x540"
                    elif res_choice == "2":
                        config[key] = "1280x720"
                    elif res_choice == "3":
                        config[key] = "1920x1080"
                    else:
                        print("Invalid choice.")
                        continue
                    print(f"✅ Resolution set to {config[key]}")
                
                else:
                    # Normal input for other settings
                    new_value = input(f"New value for {key}: ").strip()
                    if key == "screenshot_interval" or key == "max_screenshots":
                        config[key] = int(new_value)
                    else:
                        config[key] = new_value
                    print("✅ Config updated.")
            else:
                print("Invalid number.")
        except:
            print("Invalid input.")

        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)

def save_config(new_config):
    """Save updated config to config.json"""
    try:
        with open("config.json", "w") as f:
            json.dump(new_config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_running_windows():
    """Get list of running windows (same logic as CLI)"""
    try:
        import pygetwindow as gw
        windows = [w.title for w in gw.getAllWindows() if w.title.strip()]
        return windows
    except Exception as e:
        print(f"Error detecting windows: {e}")
        return []

# Global flag to control capture


def start_capture_from_dashboard():
    global config, capture_running, started_from_dashboard, capture_start_time
    if config is None:
        config = load_config()
    
    capture_running = True
    started_from_dashboard = True
    capture_start_time = time.time()
    
    print("\n🚀 Capture started from Dashboard!")
    print("   Press Ctrl + Alt + S in game to stop capture.\n")
    
    import threading
    # Pass show_status_window=False
    capture_thread = threading.Thread(
        target=run_preview_mode, 
        args=(config, False),   # ← False = don't show StatusWindow
        daemon=True
    )
    capture_thread.start()
    
    return True

def stop_capture_from_dashboard():
    global capture_running, started_from_dashboard
    started_from_dashboard = False
    print("\n⏹️ Capture stopped from Dashboard.")
    return True

    def validate_config(config):
        """Basic validation for config values"""
        errors = []
        
        if not config.get("game_window_title", "").strip():
            errors.append("game_window_title cannot be empty")
        
        interval = config.get("screenshot_interval", 0)
        if not isinstance(interval, int) or interval < 1 or interval > 30:
            errors.append("screenshot_interval must be between 1 and 30 seconds")
        
        max_shots = config.get("max_screenshots", 0)
        if not isinstance(max_shots, int) or max_shots < 10 or max_shots > 2000:
            errors.append("max_screenshots must be between 10 and 2000")
        
        res = config.get("max_resolution", "")
        if res not in ["960x540", "1280x720", "1920x1080"]:
            errors.append("max_resolution must be 960x540, 1280x720, or 1920x1080")
        
        if errors:
            print("\n⚠️ Config validation warnings:")
            for e in errors:
                print(f"   - {e}")
            print("   (The app will still try to run, but some features may not work correctly)\n")

if __name__ == "__main__":
    main()

