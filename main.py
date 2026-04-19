import time
from pathlib import Path
import json
from queue import Queue
import threading
import tkinter as tk
from tkinter import ttk
from pynput import keyboard
import shutil
from PIL import Image
import imagehash
from utils.capture import capture_game_window
from utils.grok_vision import analyze_screenshot
from utils.report import generate_report

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

class StatusWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VisionTester")
        self.root.geometry("280x88+0+0")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        
        frame = ttk.Frame(self.root)
        frame.pack(padx=8, pady=6, fill="x")
        
        self.queue_label = ttk.Label(frame, text="Queued: 0", font=("Consolas", 11))
        self.queue_label.pack(side="left")
        
        self.time_label = ttk.Label(frame, text="00:00", font=("Consolas", 11))
        self.time_label.pack(side="right")
        
        self.status_label = ttk.Label(self.root, text="Running • Ctrl+Alt+S to analyze", foreground="lime", font=("Consolas", 9))
        self.status_label.pack(pady=4)
        
        self.start_time = time.time()
        self.update_timer()
    
    def update_timer(self):
        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        self.time_label.config(text=f"{mins:02d}:{secs:02d}")
        self.root.after(1000, self.update_timer)
    
    def update_queue(self, count):
        self.queue_label.config(text=f"Queued: {count}")
    
    def set_analyzing(self):
        self.status_label.config(text="Analyzing... Please wait", foreground="orange")
    
    def set_complete(self):
        self.status_label.config(text="✅ Analysis complete", foreground="lime")
    
    def close(self):
        self.root.quit()

def clear_data():
    try:
        shutil.rmtree("screenshots", ignore_errors=True)
        shutil.rmtree("reports", ignore_errors=True)
        Path("screenshots").mkdir(exist_ok=True)
        Path("reports").mkdir(exist_ok=True)
        print("✅ Cleared screenshots and reports folders.")
    except Exception as e:
        print(f"❌ Clear error: {e}")

def run_preview_mode(config):
    print(f"\n📸 Preview Mode — every {config['screenshot_interval']} seconds")
    print(f"   Resolution: {config.get('max_resolution', '1280x720')}")
    print("   Press Ctrl + Alt + S to trigger batch analysis.\n")
    
    # Make sure screenshots folder exists
    Path("screenshots").mkdir(exist_ok=True)
    
    screenshot_queue = Queue()
    stop_event = threading.Event()
    status_win = StatusWindow()
    last_hash = None
    hash_threshold = 18

    def capture_loop():
        nonlocal last_hash
        while not stop_event.is_set():
            try:
                # Always save to screenshots/ folder
                screenshot_path = capture_game_window(
                    config["game_window_title"], 
                    "screenshots"   # ← Fixed: always save here
                )
                if screenshot_path:
                    img = Image.open(screenshot_path)

                    # === Resolution Scaling ===
                    res = config.get("max_resolution", "1280x720")
                    try:
                        max_width, max_height = map(int, res.split("x"))
                    except:
                        max_width, max_height = 1280, 720

                    ratio = min(max_width / img.width, max_height / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                    img.save(screenshot_path, "PNG")

                    # Smart Capture (hash check)
                    current_hash = imagehash.average_hash(img)
                    if last_hash is None or (current_hash - last_hash) > hash_threshold:
                        screenshot_queue.put(screenshot_path)
                        last_hash = current_hash
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
            print("\n⏹️ Hotkey pressed - Starting batch analysis...")
            status_win.root.after(0, status_win.set_analyzing)
            stop_event.set()
            status_win.root.after(100, lambda: perform_batch_analysis(status_win, screenshot_queue))

    def perform_batch_analysis(status_win, screenshot_queue):
        screenshots = []
        while not screenshot_queue.empty():
            screenshots.append(screenshot_queue.get())

        if screenshots:
            print(f"📊 Analyzing {len(screenshots)} screenshots in batch...")
            generate_report(screenshots, "reports")
            print(f"✅ Batch report complete with {len(screenshots)} screenshots")
            status_win.root.after(0, status_win.set_complete)
            status_win.root.after(2000, status_win.close)
        else:
            print("No new screenshots were captured.")
            status_win.root.after(0, status_win.close)

    hotkey_listener = keyboard.GlobalHotKeys({'<ctrl>+<alt>+s': on_hotkey})
    hotkey_listener.start()

    status_win.root.mainloop()

    stop_event.set()
    hotkey_listener.stop()
    capture_thread.join(timeout=3)

def main_menu():
    global config
    while True:
        res = config.get("max_resolution", "1280x720")
        print("\n=== AutoGameVisionTester ===")
        print(f"1. Preview Mode ({res})")
        print("2. Edit Config")
        print("3. Clear Data")
        print("4. Exit")
        choice = input("Choose an option (1-4): ").strip()

        if choice == "1":
            run_preview_mode(config)
        elif choice == "2":
            edit_config()
        elif choice == "3":
            clear_data()
        elif choice == "4":
            print("Goodbye!")
            break

def edit_config():
    global config
    config = load_config()
    keys = list(config.keys())

    while True:
        print("\n=== Current Config ===")
        for i, key in enumerate(keys, 1):
            print(f"  {i}. {key}: {config[key]}")
        print("  7. Done")

        choice = input("\nChoose option (1-7): ").strip()

        if choice == "7":
            break

        if choice == "5":
            # === Max Resolution Preset Menu ===
            print("\n=== Max Resolution ===")
            print("1. Budget     (960x540)")
            print("2. Balanced   (1280x720)")
            print("3. Full Res   (1920x1080)")

            res_choice = input("\nChoose resolution (1-3): ").strip()

            if res_choice == "1":
                config["max_resolution"] = "960x540"
            elif res_choice == "2":
                config["max_resolution"] = "1280x720"
            elif res_choice == "3":
                config["max_resolution"] = "1920x1080"
            else:
                print("Invalid choice.")
                continue

            print(f"✅ Resolution set to {config['max_resolution']}")

        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(keys):
                    key = keys[idx]
                    new_value = input(f"New value for {key}: ").strip()
                    if key == "screenshot_interval":
                        config[key] = int(new_value)
                    else:
                        config[key] = new_value
                    print("✅ Config updated.")
                else:
                    print("Invalid number.")
            except:
                print("Invalid input.")

        # Save after every change
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)

if __name__ == "__main__":
    config = load_config()
    main_menu()