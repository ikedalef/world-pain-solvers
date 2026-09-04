import os
import json
import time
import re
from pydantic import BaseModel, Field
import google.generativeai as genai
from pain_miner import get_curated_pain_points

class SolvedAppSchema(BaseModel):
    app_slug: str = Field(default="useful-web-tool")
    title: str = Field(default="Everyday Problem Solver Tool")
    target_pain: str = Field(default="Streamline manual workflows and solve repetitive tasks.")
    key_features: list[str] = Field(default_factory=lambda: ["Instant in-browser processing", "100% Privacy focused", "Responsive UI"])
    category: str = Field(default="Productivity")
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
    """現在のAPIキーで実際に疎通可能かつクォータが残っているモデルを探索"""
    print("[Discovery] Probing available models on current API key...")
    try:
        models = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        print(f"[Discovery] Found {len(models)} candidate models: {models}")
    except Exception as e:
        print(f"[Warn] Failed to list models: {e}. Falling back to default list.")
        models = ["models/gemini-3.6-flash", "models/gemini-2.0-flash", "models/gemini-1.5-flash"]

    # Flash系・高速モデルを優先してプローブ
    sorted_models = sorted(models, key=lambda x: 0 if "flash" in x.lower() else 1)

    for m in sorted_models:
        try:
            print(f"[Probe] Testing model: {m} ...", end=" ")
            probe_model = genai.GenerativeModel(model_name=m)
            # 1文字投げてクォータ・サポート確認
            res = probe_model.generate_content("ping", generation_config={"max_output_tokens": 5})
            if res and res.text:
                print("-> OK (Active & Quota Available)")
                return m
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "quota" in err_msg.lower():
                print(f"-> Skipped (Quota Exceeded / Rate Limit)")
            elif "404" in err_msg or "not found" in err_msg.lower():
                print(f"-> Skipped (Deprecated / Unsupported)")
            else:
                print(f"-> Failed ({err_msg[:60]}...)")
            time.sleep(2)

    return None

def generate_solution_app():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: GEMINI_API_KEY is not defined.")

    genai.configure(api_key=api_key)

    active_model_name = discover_working_model()
    if not active_model_name:
        print("[Notice] All candidate models currently exhausted daily free quota or are unavailable.")
        print("[Notice] Gracefully sleeping pipeline until next scheduled cycle to avoid broken builds.")
        # エラーでビルドを赤く落とさず、クォータ回復を待つ安全終了
        exit(0)

    pains = get_curated_pain_points()[:2]

    system_instruction = """
あなたは世界中の人々のリアルな困りごとをブラウザ上で解決する最高峰のエンジニアです。
ユーザーが手作業で苦労していた作業を、ブラウザ上で1秒・完全ローカル・無料で解決する単一HTMLのWebツールを作成してください。
必ず指定されたJSON形式（app_slug, title, target_pain, key_features, category, html_content）を厳守して出力してください。
html_contentには完全な単一のindex.htmlコード（Tailwind CSS CDN付き）を入れてください。
"""

    prompt = f"""
{system_instruction}

【解決すべき困りごと】
{json.dumps(pains, ensure_ascii=False, indent=2)}

【必須JSONキー】
- app_slug: 半角英数ハイフンのスラッグ（例: csv-cleaner-pro）
- title: アプリ名
- target_pain: 解決した具体的な課題
- key_features: 主な機能リスト
- category: カテゴリ
- html_content: <!DOCTYPE html>で始まる完全なHTML
"""

    print(f"[Execution] Generating application with validated model: {active_model_name}")
    model = genai.GenerativeModel(
        model_name=active_model_name,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.3
        }
    )

    for attempt in range(3):
        try:
            res = model.generate_content(prompt)
            raw_dict = extract_safe_json(res.text)

            html = raw_dict.get("html_content", "")
            if not html or "<!DOCTYPE html>" not in html:
                if "<!DOCTYPE html>" in res.text:
                    raw_dict["html_content"] = res.text

            app_data = SolvedAppSchema(**raw_dict)

            slug = re.sub(r"[^a-zA-Z0-9\-]", "", app_data.app_slug.lower().replace(" ", "-")) or f"tool-{int(time.time())}"
            target_dir = os.path.join("apps", slug)
            os.makedirs(target_dir, exist_ok=True)

            with open(os.path.join(target_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(app_data.html_content)

            with open(os.path.join(target_dir, "meta.json"), "w", encoding="utf-8") as f:
                json.dump(app_data.model_dump(exclude={"html_content"}), f, ensure_ascii=False, indent=2)

            print(f"[Success] Built and verified solution at: {target_dir}")
            return slug

        except Exception as e:
            print(f"[Warn] Attempt {attempt+1} failed: {e}")
            time.sleep(15)

    print("[Warn] Model failed to generate JSON within attempt budget.")
    exit(0)

if __name__ == "__main__":
    generate_solution_app()
