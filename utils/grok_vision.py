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

                                        Ignore the small status overlay in the top-left corner of the screenshot. Do not mention it, describe it, or acknowledge it in any way.

                                        First, quickly identify the type of screen you are looking at:
                                        - Gameplay / In-game view
                                        - Menu / Settings / UI screen
                                        - Loading screen
                                        - Other

                                        Then focus your analysis on what actually matters for that screen type.

                                        For menus/UI screens: Prioritize layout, readability, button placement, text clarity, consistency, accessibility, and usability issues. Give practical improvement suggestions.

                                        For gameplay: Focus on clipping, lighting, texture problems, particle issues, physics glitches, visual artifacts, and immersion breakers.

                                        Always be concise and actionable. Never waste tokens describing irrelevant background details when the focus is clearly on UI or a specific element.

                                        Pay special attention to stylized fonts. If text is hard to read, say "UNCLEAR FONT".

                                        Describe what you see clearly and professionally.

                                        Then analyze the ENTIRE screenshot systematically in this exact order, giving balanced attention to every area:

                                        1. Background / Environment
                                        2. Mid-ground objects and architecture
                                        3. Foreground / Character
                                        4. UI / HUD / Menus / Text
                                        5. Particles, effects, and lighting

                                        Pay extreme attention to stylized game fonts and menu text.
                                        - If text is unclear or hard to read, write "UNCLEAR FONT" instead of guessing letters.
                                        - Never hallucinate or invent words. Be honest when text is ambiguous.

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

                                        Give practical improvement suggestions when relevant.

                                        Describe what you see clearly and professionally. Be specific, balanced, and actionable."""
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