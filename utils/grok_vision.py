import base64
import requests
from pathlib import Path

def analyze_screenshot(screenshot_path, api_key):
    """Send screenshot to Grok-4 (multimodal)"""
    try:
        with open(screenshot_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "grok-4",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """You are a senior Unreal Engine QA tester.

                                    Analyze the ENTIRE screenshot systematically. Scan the image in this exact order and give balanced attention to every area:

                                    1. Background / Environment
                                    2. Mid-ground objects and architecture
                                    3. Foreground / Character
                                    4. UI / HUD / Menus / Text
                                    5. Particles, effects, and lighting

                                    Pay extreme attention to stylized game fonts and menu text.
                                    - If text is unclear or hard to read, write "UNCLEAR FONT" instead of guessing letters.
                                    - Never hallucinate or invent words. Be honest when text is ambiguous.
                                    - Focus on UI glitches, texture issues, clipping, lighting problems, and inconsistencies.

                                    Focus on common Unreal Engine issues:
                                    - Nanite / Lumen artifacts
                                    - Material / shader problems
                                    - Clipping / z-fighting
                                    - LOD pop-in
                                    - Lighting inconsistencies
                                    - UI scaling / overlap
                                    - Particle system glitches
                                    - Physics / collision problems
                                    - Text rendering issues

                                    Describe what you see clearly and professionally. Be specific and balanced across the whole frame."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"API Error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"Vision error: {e}")
        return None