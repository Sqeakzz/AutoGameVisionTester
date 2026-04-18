import mss
import mss.tools
from pathlib import Path
from datetime import datetime

def take_screenshot(game_window_title: str) -> Path | None:
    """
    Takes a screenshot focused on the game window (falls back to primary monitor).
    """
    try:
        with mss.mss() as sct:
            # Try to find the game window by title
            for monitor in sct.monitors:
                if game_window_title.lower() in str(monitor).lower():  # crude title match
                    screenshot = sct.grab(monitor)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = Path("screenshots") / f"game_{timestamp}.png"
                    screenshot_path.parent.mkdir(exist_ok=True)
                    
                    mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(screenshot_path))
                    return screenshot_path
            
            # Fallback: primary monitor
            screenshot = sct.grab(sct.monitors[1])  # monitors[1] is usually primary
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = Path("screenshots") / f"game_{timestamp}.png"
            screenshot_path.parent.mkdir(exist_ok=True)
            
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(screenshot_path))
            return screenshot_path
                
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return None