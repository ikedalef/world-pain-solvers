import os
import json
import time
import re
from pydantic import BaseModel, Field
import google.generativeai as genai
from pain_miner import get_curated_pain_points

class SolvedAppSchema(BaseModel):
    app_slug: str = Field(description="URLセーフなアプリ識別子。kebab-case (例: csv-privacy-cleaner)")
    title: str = Field(description="ユーザーが一目で課題解決を認識できる明確なツール名")
    target_pain: str = Field(description="具体的にどの層のどんな苦痛を解決したのか")
    key_features: list[str] = Field(description="困りごとを解決するための主要な3〜4機能")
    category: str = Field(description="Productivity, Finance, Developer, Writing, Accessibility など")
    html_content: str = Field(description="Tailwind CDN & インラインVanilla JSによる完全自己完結HTML")

def extract_safe_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{[\s\S]*\})", text)
        if match:
            return json.loads(match.group(1))
        raise ValueError(f"Could not parse valid JSON from AI output: {text[:200]}...")

def generate_solution_app():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: GEMINI_API_KEY environment variable is not defined.")

    genai.configure(api_key=api_key)
    # トークン消費削減のため厳選された上位3件のみ抽出
    pains = get_curated_pain_points()[:3]

    system_instruction = """
あなたは世界中の人々のリアルな困りごとをWebツールで解決するエキスパートです。
1. 退屈なモックや電卓は禁止。実利性の高い課題をブラウザ上で完全ローカル（サーバー送信なし）で解決するツールを作成してください。
2. 外部ライブラリのビルドは不要。単一のindex.html内にTailwind CSS CDNとVanilla JSを完結させてください。
3. 直感的で美しいUI、コピー機能、入力バリデーションを必須とします。
"""

    prompt = f"""
{system_instruction}

以下の困りごとリストから1つを選定し、ブラウザ完結型Webツールを作成してください。
{json.dumps(pains, ensure_ascii=False, indent=2)}
"""

    model_name = "gemini-3.6-flash"
    print(f"[Info] Executing generation with model: {model_name}")

    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": SolvedAppSchema,
            "temperature": 0.4
        }
    )

    # レートリミット（429）を考慮した十分な待機時間を持つリトライループ
    for attempt in range(3):
        try:
            res = model.generate_content(prompt)
            raw_data = extract_safe_json(res.text)
            app_data = SolvedAppSchema(**raw_data)

            target_dir = os.path.join("apps", app_data.app_slug)
            os.makedirs(target_dir, exist_ok=True)

            with open(os.path.join(target_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(app_data.html_content)

            with open(os.path.join(target_dir, "meta.json"), "w", encoding="utf-8") as f:
                json.dump(app_data.model_dump(exclude={"html_content"}), f, ensure_ascii=False, indent=2)

            print(f"[Success] Built solution for: {app_data.target_pain}")
            return app_data.app_slug
        except Exception as e:
            # 429 quota超過の指示（約30秒〜40秒）に確実に対応するため長めに待機
            wait_sec = 40 + (attempt * 20)
            print(f"[Warn] API Rate limit/Error encountered: {e}")
            print(f"[Info] Waiting {wait_sec}s for quota cooldown before attempt {attempt+2}...")
            time.sleep(wait_sec)

    raise RuntimeError("Failed to generate solution app after quota backoff.")

if __name__ == "__main__":
    generate_solution_app()
