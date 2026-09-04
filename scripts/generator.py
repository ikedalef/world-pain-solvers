import os
import json
import time
import re
import sys
from pydantic import BaseModel, Field
import google.generativeai as genai
from pain_miner import get_curated_pain_points

class SolvedAppSchema(BaseModel):
    app_slug: str = Field(default="useful-paid-tool")
    title: str = Field(default="Professional Problem Solver")
    target_pain: str = Field(default="Automate high-value manual tasks for global professionals.")
    key_features: list[str] = Field(default_factory=lambda: ["Instant local execution", "20-run pack or unlimited access", "100% Client-side privacy"])
    category: str = Field(default="Productivity")
    pricing_options: list[str] = Field(default_factory=lambda: ["$11 One-Time (20 Runs)", "$9/mo Unlimited Pro"])
    html_content: str = Field(default="")

def extract_safe_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
    cleaned = re.sub(r"\n```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{[\s\S]*\})", cleaned)
        if match:
            return json.loads(match.group(1))
        if "<!DOCTYPE html>" in text or "<html" in text:
            return {
                "app_slug": f"tool-{int(time.time())}",
                "title": "Autonomous Problem Solver Tool",
                "target_pain": "Automate daily productivity pain points in-browser",
                "html_content": text
            }
        raise ValueError(f"Unable to parse output: {text[:200]}")

def get_usable_model_pool():
    try:
        models = [
            m.name.replace("models/", "")
            for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
    except Exception as e:
        print(f"[Warn] ListModels failed: {e}")
        models = []

    preferred = [
        "gemini-3.5-flash",
        "gemini-flash-latest",
        "gemini-3.1-flash-preview",
        "gemini-2.5-pro",
        "gemini-pro-latest",
        "gemini-3.6-flash"
    ]
    pool = [m for m in preferred if m in models]
    for m in models:
        if m not in pool and "flash" in m:
            pool.append(m)
    return pool if pool else ["gemini-3.5-flash", "gemini-flash-latest"]

def generate_solution_app():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: GEMINI_API_KEY is not defined.")

    stripe_link = os.environ.get("STRIPE_PAYMENT_LINK", "https://buy.stripe.com/evqaEXafF6jw6kV0jg5J60j")
    genai.configure(api_key=api_key)

    model_pool = get_usable_model_pool()
    print(f"[Discovery] Usable model pool: {model_pool}")

    pains = get_curated_pain_points()[:2]

    system_instruction = f"""
You are an elite software engineer. You NEVER build fake, simulated, or dummy placeholder tools.
Every web tool you build MUST HAVE 100% REAL, FUNCTIONING, JAVASCRIPT-POWERED BUSINESS LOGIC.

【STRICT ZERO-TOLERANCE RULES】
1. NO SIMULATIONS / NO PLACEHOLDERS:
   - Absolute ban on text like "This is a simulated view", "In the full version...", or dummy sample outputs.
   - The user must be able to paste REAL input (CSV text, JSON data, log files, multi-line lists) and get 100% REAL TRANSFORMED RESULTS immediately in the browser.
2. HIGH-VALUE REAL PAIN POINTS ONLY:
   - Select real operations: Messy CSV/TSV Data Cleaner & Deduplicator, Broken JSON Fixer & Parser, Multi-currency Freelance Invoice Calculator, Regex Matcher & Replacer, Bulk Text Formatter.
   - Avoid cross-origin web scrapers (which fail in browser). Build direct data transformation tools.
3. PRICING & CREDIT ARCHITECTURE (Option A):
   - 3 Free Runs default.
   - "$11 One-Time (20 Runs Pack)" and "$9/month (Unlimited Pro)" linking to `{stripe_link}`.
   - Top credit badge: `Runs Left: X`.
   - LocalStorage key: `app_runs_remaining`. Decrements on click.
   - When 0, trigger paywall modal. Entering `PRO20` unlocks 20 additional runs or unlimited.
4. EXPORT / UTILITY:
   - Provide a real "Download Result" or "Copy to Clipboard" button that actually downloads or copies the real output.
5. 100% Polished English UI with Tailwind CSS CDN. Dark mode (slate-950).
"""

    prompt = f"""
{system_instruction}

【Pain Data Target】
{json.dumps(pains, ensure_ascii=False, indent=2)}

Build a fully functioning, REAL data-transforming web tool that directly solves high-friction manual work.
Output strictly valid JSON with keys:
- app_slug: string (kebab-case)
- title: string
- target_pain: string
- key_features: list of strings
- category: string
- pricing_options: list of strings (["$11 One-Time (20 Runs)", "$9/mo Unlimited Pro"])
- html_content: standalone <!DOCTYPE html> string with 100% working, non-mock transformation JS.
"""

    for model_name in model_pool:
        print(f"[Execution] Generating real tool with: {model_name}")
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            )
            res = model.generate_content(prompt)
            raw_dict = extract_safe_json(res.text)
            app_data = SolvedAppSchema(**raw_dict)

            slug = re.sub(r"[^a-zA-Z0-9\-]", "", app_data.app_slug.lower().replace(" ", "-")) or f"tool-{int(time.time())}"
            target_dir = os.path.join("apps", slug)
            os.makedirs(target_dir, exist_ok=True)

            with open(os.path.join(target_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(app_data.html_content)

            with open(os.path.join(target_dir, "meta.json"), "w", encoding="utf-8") as f:
                json.dump(app_data.model_dump(exclude={"html_content"}), f, ensure_ascii=False, indent=2)

            print(f"[Success] Real working product created at: {target_dir}")
            return slug

        except Exception as e:
            print(f"[Warn] Model {model_name} failed: {str(e)[:100]}")
            time.sleep(3)

    print("[Notice] Pool exhausted. Sleeping gracefully.")
    sys.exit(0)

if __name__ == "__main__":
    generate_solution_app()
