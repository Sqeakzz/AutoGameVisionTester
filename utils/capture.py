import mss
from PIL import Image
import time
from pathlib import Path
import pygetwindow as gw
import ctypes
from ctypes import wintypes

def capture_game_window(window_title, output_folder):
    """Capture game window with reliable foreground activation"""
    try:
        # Find windows that contain the title
        windows = [w for w in gw.getAllWindows() if window_title.lower() in w.title.lower()]
        
        if not windows:
            print(f"⚠️ No window found containing '{window_title}'")
            return None
        
        target_window = windows[0]
        hwnd = target_window._hWnd
        
        # === Reliable Window Activation (AttachThreadInput trick) ===
        try:
            # Get current foreground window and thread
            foreground_hwnd = ctypes.windll.user32.GetForegroundWindow()
            current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
            foreground_thread = ctypes.windll.user32.GetWindowThreadProcessId(foreground_hwnd, None)
            
            # Attach to foreground thread
            if current_thread != foreground_thread:
                ctypes.windll.user32.AttachThreadInput(foreground_thread, current_thread, True)
            
            # Restore if minimized
            if target_window.isMinimized:
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                time.sleep(0.2)
            
            # Bring to front
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.SetActiveWindow(hwnd)
            ctypes.windll.user32.SetFocus(hwnd)
            
            # Detach from foreground thread
            if current_thread != foreground_thread:
                ctypes.windll.user32.AttachThreadInput(foreground_thread, current_thread, False)
            
            time.sleep(0.3)  # Give Windows time to focus
            
        except Exception as e:
            print(f"⚠️ Window activation warning: {e}")
        
        # Capture
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
            
            print(f"📸 Captured: {target_window.title}")
            return filepath
            
    except Exception as e:
        print(f"❌ Capture error: {e}")
        return None