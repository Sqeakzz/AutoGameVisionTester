import time
from pathlib import Path
import json
import sys
from queue import Queue
import threading
import tkinter as tk
from tkinter import ttk
from pynput import keyboard
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

def run_capture(config):
    print(f"\n📸 Starting capture every {config['screenshot_interval']} seconds (non-blocking).")
    print("   Live status bar opened at top-left.")
    print("   Press Ctrl + Alt + S to stop and analyze.\n")
    
    screenshot_queue = Queue()
    stop_event = threading.Event()
    status_win = StatusWindow()
    
    def capture_loop():
        while not stop_event.is_set():
            start_time = time.time()
            try:
                screenshot_path = capture_game_window(config["game_window_title"], "screenshots")
                if screenshot_path:
                    screenshot_queue.put(screenshot_path)
                    print(f"📸 Captured: {screenshot_path.name}")
                    status_win.root.after(0, lambda c=screenshot_queue.qsize(): status_win.update_queue(c))
            except Exception as e:
                print(f"❌ Capture error: {e}")
            
            elapsed = time.time() - start_time
            sleep_time = max(0.0, config["screenshot_interval"] - elapsed)
            time.sleep(sleep_time)
    
    capture_thread = threading.Thread(target=capture_loop, daemon=True)
    capture_thread.start()
    
    def on_hotkey():
        if not stop_event.is_set():
            print("\n⏹️ Hotkey pressed - Starting batch analysis...")
            status_win.root.after(0, status_win.set_analyzing)
            stop_event.set()
            # Schedule analysis + complete message after window closes
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
            print("No screenshots were captured.")
            status_win.root.after(0, status_win.close)
    
    hotkey_listener = keyboard.GlobalHotKeys({'<ctrl>+<alt>+s': on_hotkey})
    hotkey_listener.start()
    
    status_win.root.mainloop()
    
    stop_event.set()
    hotkey_listener.stop()
    capture_thread.join(timeout=3)

def main_menu():
    while True:
        config = load_config()
        print("\n=== AutoGameVisionTester ===")
        print("1. Start Capture")
        print("2. Edit Config")
        print("3. Exit")
        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            run_capture(config)
        elif choice == "2":
            edit_config()
        elif choice == "3":
            print("Goodbye.")
            sys.exit(0)
        else:
            print("Invalid option.")

def edit_config():
    config = load_config()
    keys = list(config.keys())
    print("\nCurrent Config:")
    for i, key in enumerate(keys, 1):
        print(f"  {i}. {key}: {config[key]}")
    
    choice = input("\nEnter number to edit (or 'done'): ").strip()
    if choice.lower() == "done":
        return
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(keys):
            key = keys[idx]
            new_value = input(f"New value for {key}: ").strip()
            if key == "screenshot_interval":
                config[key] = int(new_value)
            else:
                config[key] = new_value
            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)
            print("Config updated.")
        else:
            print("Invalid number.")
    except:
        print("Invalid input.")

if __name__ == "__main__":
    main_menu()