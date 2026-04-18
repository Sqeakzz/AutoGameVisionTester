import mss
from PIL import Image
import time
from pathlib import Path
import pygetwindow as gw

def capture_game_window(window_title, output_folder):
    """Capture game window by partial title match"""
    try:
        # Find any window containing the title
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            print(f"⚠️ No window found containing '{window_title}'")
            return None
        
        # Use the first matching window
        target_window = windows[0]
        
        # Activate and get coordinates
        if not target_window.isActive:
            target_window.activate()
            time.sleep(0.2)  # small delay for focus
        
        left, top, right, bottom = target_window.left, target_window.top, target_window.right, target_window.bottom
        
        with mss.mss() as sct:
            monitor = {
                "top": top,
                "left": left,
                "width": right - left,
                "height": bottom - top
            }
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = Path(output_folder) / f"game_{timestamp}.png"
            img.save(filepath)
            
            print(f"📸 Captured window: {target_window.title}")
            return filepath
            
    except Exception as e:
        print(f"❌ Capture error: {e}")
        return None