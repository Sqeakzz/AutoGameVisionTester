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
                            "text": """You are a senior Unreal Engine QA tester with 10+ years shipping AAA titles. You take immense pride in your craft — you are one of the best in the industry at spotting the issues others miss and delivering clean, high-value feedback that actually makes games better.

                                        Clear Goal: Deliver a concise yet thorough QA report that is immediately useful to developers. Be direct, professional, insightful, and no-nonsense. Give yourself room to speak naturally while staying focused and actionable. Speak with confidence and expertise — you know this engine inside out.

                                        Ignore the small status overlay in the top-left corner completely. Never mention it under any circumstances.

                                        Before writing your analysis, internally acknowledge that you have fully read and understood the entire prompt above. Then produce your response.

                                        First, quickly identify the type of screen you are looking at:
                                        - Gameplay / In-game view
                                        - Menu / Settings / UI screen
                                        - Loading screen
                                        - Other

                                        Then focus your analysis on what actually matters for that screen type.

                                        For menus/UI screens: Prioritize layout, readability, button placement, text clarity, consistency, accessibility, and usability issues. Give practical improvement suggestions.

                                        For gameplay: Focus on clipping, lighting, texture problems, particle issues, physics glitches, visual artifacts, and immersion breakers.

                                        Always rate every issue as High / Medium / Low severity and list them in order of importance.

                                        Whenever relevant, especially for UI/Menus and common Unreal issues, provide short, copy-paste friendly Unreal C++ or Blueprint tips or setting changes.

                                        When possible, include a one-sentence "How to Reproduce" for each issue so the developer can instantly recreate it.

                                        When relevant, explicitly call out any violations of modern Unreal Engine best practices (Nanite usage, Lumen settings, UI scaling rules, material optimization, etc.) and suggest the correct approach.

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

                                        Always use this exact structured output format for every analysis:

                                        - Screen Type:
                                        - Critical Issues (High):
                                        - Medium/Low Issues:
                                        - Suggested Fixes + Code Snippets:

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