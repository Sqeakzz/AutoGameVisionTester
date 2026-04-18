import requests
import base64
from pathlib import Path
from PIL import Image

def analyze_screenshot(screenshot_path: Path, api_key: str) -> str:
    """
    Sends screenshot to Grok Vision and returns the analysis text.
    """
    try:
        # Resize image to reduce payload size (helps prevent timeouts)
        img = Image.open(screenshot_path)
        img.thumbnail((1280, 720))  # keep it reasonable size
        img.save(screenshot_path, "PNG")

        with open(screenshot_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "model": "grok-4",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior game QA tester. Analyze the screenshot for bugs, UI glitches, clipping, texture issues, performance hints, or anything that looks wrong. Be specific and professional."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this game screenshot for any issues:"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                        }
                    ]
                }
            ],
            "max_tokens": 800
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60   # increased timeout
        )

        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"❌ Grok Vision failed: {e}")
        return f"Error analyzing screenshot: {str(e)}"