import base64
import requests

def analyze_screenshot(image_path, api_key, resolution="1280x720", mode="balanced"):
    """
    Modes:
    - "quick"   → Fast & concise (lower tokens)
    - "balanced"→ Default (your current quality)
    - "deep"    → Thorough + self-critique
    """
    try:
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # ====================== YOUR ORIGINAL PROMPT (kept 100%) ======================
        your_original_prompt = f"""You are a senior Unreal Engine QA tester with 12+ years shipping AAA titles. You take pride in spotting issues others miss and delivering actionable feedback that improves games.

                                    IMPORTANT: The screenshot has been downscaled to {resolution} before being sent to you. Do NOT expect fine details, small text, or subtle artifacts. Only report issues clearly visible at this reduced resolution.

                                    Goal: Deliver a concise, professional QA report that is immediately useful to developers. Be direct and actionable.

                                    Ignore the top-left status overlay completely.

                                    First identify the screen type:
                                    - Gameplay / In-game view
                                    - Menu / Settings / UI screen
                                    - Loading screen
                                    - Other

                                    Focus analysis on what matters for that screen type:
                                    - Menus/UI: layout, readability, button placement, text clarity, consistency, accessibility
                                    - Gameplay: clipping, lighting, textures, particles, physics, visual artifacts, immersion

                                    Rate every issue as High / Medium / Low severity. List in order of importance.

                                    For relevant issues, provide short copy-paste friendly Unreal C++ or Blueprint tips + a one-sentence "How to Reproduce".

                                    Use this exact output format:

                                    - Screen Type:
                                    - Critical Issues (High):
                                    - Medium/Low Issues:
                                    - Suggested Fixes + Code Snippets:

                                    Analyze the screenshot systematically in this order:
                                    1. Background / Environment
                                    2. Mid-ground objects and architecture
                                    3. Foreground / Character
                                    4. UI / HUD / Menus / Text
                                    5. Particles, effects, and lighting

                                    Pay extreme attention to stylized fonts. If text is hard to read, write "UNCLEAR FONT".

                                    Focus on common Unreal issues: Nanite, Lumen, clipping, LOD pop-in, lighting, UI scaling, particles, physics, text rendering.

                                    Be specific and actionable. Never hallucinate."""

        # ====================== MODE WRAPPER ======================
        if mode == "quick":
            mode_instruction = "\n\nMODE: QUICK — Be extremely concise. ONLY report Critical (High) issues. Max 4-5 bullet points total."
        elif mode == "deep":
            mode_instruction = """\n\nMODE: DEEP — Perform a proper self-critique:
                                1. Write your full analysis.
                                2. Critique your own work: Did I miss important issues? Are severities accurate? Are fixes specific enough? Is this thorough enough?
                                3. Revise and output ONLY the final improved version. Make this noticeably better than Balanced mode."""
        else:
            mode_instruction = "\n\nMODE: BALANCED — Deliver professional depth with clear prioritization."

        full_prompt = mode_instruction + "\n\n" + your_original_prompt

        payload = {
            "model": "grok-4",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1800 if mode == "deep" else 1200,
            "temperature": 0.3
        }

        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Simple token usage estimate (for future dashboard)
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            
            return {
                "analysis": content,
                "tokens_used": tokens_used,
                "mode": mode
            }
        else:
            return {
                "analysis": f"API Error {response.status_code}: {response.text}",
                "tokens_used": 0,
                "mode": mode
            }

    except Exception as e:
        return {
            "analysis": f"Error analyzing screenshot: {str(e)}",
            "tokens_used": 0,
            "mode": mode
        }