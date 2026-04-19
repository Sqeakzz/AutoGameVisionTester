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

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


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
        self.root.destroy()


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
    
    Path("screenshots").mkdir(exist_ok=True)
    
    screenshot_queue = Queue()
    stop_event = threading.Event()
    hotkey_pressed = threading.Event()
    
    status_win = StatusWindow()
    last_hash = None
    hash_threshold = 18

    def capture_loop():
        nonlocal last_hash
        while not stop_event.is_set():
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
            status_win.close()
            handle_mode_selection()
            return
        status_win.root.after(100, check_for_hotkey)

    def handle_mode_selection():
        mode_input = input("Choose mode (quick / balanced / deep) [default: balanced]: ").strip().lower()
        mode = mode_input if mode_input in ["quick", "balanced", "deep"] else "balanced"
        
        screenshots = []
        while not screenshot_queue.empty():
            screenshots.append(screenshot_queue.get())

        if screenshots:
            print(f"\n📊 Analyzing {len(screenshots)} screenshots in **{mode.upper()}** mode...")
            generate_report(screenshots, "reports", mode=mode, config=config)
            print(f"✅ Batch report complete ({mode} mode)")
        else:
            print("No new screenshots were captured.")

    hotkey_listener = keyboard.GlobalHotKeys({'<ctrl>+<alt>+s': on_hotkey})
    hotkey_listener.start()

    check_for_hotkey()
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

        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)


if __name__ == "__main__":
    config = load_config()
    main_menu()