from mss import mss
from PIL import Image
import time
from pathlib import Path

def capture_game_window(window_title, output_folder):
    """Capture the game window and save screenshot"""
    with mss() as sct:
        # Capture primary monitor for now (we can improve window targeting later)
        monitor = sct.monitors[1]  # 1 = primary monitor
        screenshot = sct.grab(monitor)
        
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = Path(output_folder) / f"game_{timestamp}.png"
        img.save(filepath)
        
        return filepath
    return None