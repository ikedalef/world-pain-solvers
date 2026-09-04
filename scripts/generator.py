import os
import json
import time
import re
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

def discover_working_model():
    """APIから実際に利用可能なモデル名を取得し、疎通確認して返す"""
    print("[Discovery] Querying supported models from API...")
    try:
        raw_models = [
            m.name.replace("models/", "")
            for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        print(f"[Discovery] Available supported models: {raw_models}")
    except Exception as e:
        print(f"[Warn] ListModels failed: {e}")
        raw_models = []

    # API側が現在アクティブにサポートしている順に指定
    preferred = [
        "gemini-3.6-flash",
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest"
    ]

    # 利用可能リストに存在するものを優先順に整理
    candidates = [p for p in preferred if p in raw_models]
    # なければAPIが返したリストそのものを使用
    if not candidates:
        candidates = raw_models

    for model_name in candidates:
        try:
            print(f"[Probe] Testing: {model_name} ...", end=" ")
            m = genai.GenerativeModel(model_name=model_name)
            res = m.generate_content("ping", generation_config={"max_output_tokens": 5})
            if res and res.text:
                print("-> SUCCESS")
                return model_name
        except Exception as e:
            err = str(e)
            print(f"-> FAILED ({err[:40]}...)")
            time.sleep(3)

    # 最後の手段（API推奨モデル）
    return "gemini-3.6-flash"

def generate_solution_app():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: GEMINI_API_KEY is not defined.")

    stripe_link = os.environ.get("STRIPE_PAYMENT_LINK", "https://buy.stripe.com/evqaEXafF6jw6kV0jg5J60j")

    genai.configure(api_key=api_key)
    active_model = discover_working_model()
    pains = get_curated_pain_points()[:2]

    system_instruction = f"""
You are an elite Silicon Valley software architect building high-converting, monetized Micro-SaaS tools.
Target Market: Global English-speaking users.

【Monetization Model (Strict Architecture)】
1. Pricing Tiers:
   - Free Trial: 3 free runs included by default.
   - Option 1 (Pay-As-You-Go): "$11 One-Time - 20 Runs Pack (No Expiration)"
   - Option 2 (Pro): "$9/month - Unlimited Access + Continuous Updates"
2. Checkout URL: Both checkout buttons must link directly to: `{stripe_link}`
3. Credit Management Logic (100% In-Browser JavaScript):
   - Store credits in localStorage (`app_runs_remaining`). Initialize to 3 if not present.
   - Display a clean top badge: "Runs Left: X" (or "Pro Unlimited").
   - When a user performs the core tool action, decrement by 1.
   - When credits reach 0, show a sleek Paywall Modal displaying the two pricing options and an "Enter License / Receipt Key" field.
   - If user enters code `PRO20` or any non-empty key in license modal, add 20 runs or set unlimited and save to localStorage.
4. UI & Usability:
   - Complete single-file HTML using Tailwind CSS CDN (https://cdn.tailwindcss.com).
   - Modern dark mode (slate-950 background, slate-900 cards, indigo/emerald accents).
   - 100% English copywriting.
"""

    prompt = f"""
{system_instruction}

【Verified Global User Pain Points】
{json.dumps(pains, ensure_ascii=False, indent=2)}

Build a single-page monetized web app solving one of these pains with the exact credit & paywall model.
Output strictly valid JSON with keys:
- app_slug: string (kebab-case)
- title: string
- target_pain: string
- key_features: list of strings
- category: string
- pricing_options: list of strings (["$11 One-Time (20 Runs)", "$9/mo Unlimited Pro"])
- html_content: complete standalone <!DOCTYPE html> string with Tailwind CSS and the complete credit/paywall JS logic.
"""

    print(f"[Execution] Generating monetized application via: {active_model}")
    model = genai.GenerativeModel(
        model_name=active_model,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.3
        }
    )

    for attempt in range(3):
        try:
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

            print(f"[Success] Built monetized product at: {target_dir}")
            return slug
        except Exception as e:
            print(f"[Warn] Attempt {attempt+1} failed: {e}")
            time.sleep(10)

    raise RuntimeError("Failed to finalize monetized app generation.")

if __name__ == "__main__":
    generate_solution_app()
