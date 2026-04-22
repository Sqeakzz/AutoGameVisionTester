import base64
import requests
import json

def analyze_screenshot(image_path, api_key, resolution="1280x720", mode="balanced"):
    try:
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")

        # Load model from config
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
            selected_model = config.get("model", "grok-4")
        except:
            selected_model = "grok-4"

        # This should be HERE (outside the try/except)
        print(f"Using model: {selected_model}")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # ====================== YOUR STYLE + JSON ======================
        base_prompt = f"""You are a senior game QA tester with 12+ years of experience shipping titles across multiple engines.

                            The screenshot has been downscaled to {resolution}. Only report issues clearly visible at this resolution.

                            Your goal is to deliver professional, actionable feedback that helps developers improve their game.

                            Ignore the debug or placeholder UI elements visible in top-left corner

                            **Output Format — Return ONLY valid JSON with this exact structure:**

                            {{
                            "screen_type": "Gameplay / Menu / Loading / Other",
                            "critical_issues": ["issue 1", "issue 2"],
                            "medium_issues": ["issue 1"],
                            "low_issues": ["issue 1", "issue 2", "issue 3"],
                            "suggested_fixes": ["fix 1", "fix 2"]
                            }}

                            **Analysis Guidelines:**
                            - Be direct, specific, and professional
                            - Focus on what actually impacts player experience
                            - Prioritize issues that break immersion or functionality
                            - For each issue, consider visual quality, UI clarity, technical problems, and gameplay feel
                            - If something looks like a placeholder or debug element, mention it

                            **Common areas to check:**
                            - Visual quality (lighting, textures, particles, reflections, aliasing)
                            - UI/HUD readability and consistency
                            - Technical issues (clipping, z-fighting, LOD problems, seams)
                            - Overall polish and immersion

                            Be honest with severity. Empty arrays are fine if there are no issues in a category."""

        # Mode instructions
        if mode == "quick":
            mode_instruction = "\n\nMODE: QUICK — Only report Critical (High) issues. Keep it very concise."
        elif mode == "deep":
            mode_instruction = "\n\nMODE: DEEP — Be thorough and detailed while still following the JSON format."
        else:
            mode_instruction = "\n\nMODE: BALANCED — Good balance of detail and clarity."

        full_prompt = base_prompt + mode_instruction

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
            "max_tokens": 850 if mode == "quick" else (1350 if mode == "deep" else 1050),
            "temperature": 0.25
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
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)

            try:
                content = content.strip()
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(content)
                return {
                    "analysis": parsed,
                    "tokens_used": tokens_used,
                    "mode": mode
                }
            except:
                return {
                    "analysis": {"error": "JSON parse failed"},
                    "tokens_used": tokens_used,
                    "mode": mode
                }
        else:
            return {
                "analysis": {"error": f"API Error {response.status_code}"},
                "tokens_used": 0,
                "mode": mode
            }

    except Exception as e:
        return {
            "analysis": {"error": str(e)},
            "tokens_used": 0,
            "mode": mode
        }