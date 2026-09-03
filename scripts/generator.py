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
    """Markdownタグや前後の余計な文字列を除去して確実にJSONをパース"""
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
    pains = get_curated_pain_points()

    system_instruction = """
あなたは「世界中の人々のリアルな困りごと・苦痛をWebテクノロジーで一掃する」最高峰の課題解決エンジニアです。

【絶対原則】
1. 人間のリアルなペインの根絶:
   - 単なる電卓や時計などのありきたりなモックは厳禁。
   - ユーザーが手作業で苦労していた作業や、既存ツールの不満をブラウザ上で1秒・完全ローカル・無料で解決する実用ツールを作成してください。
2. 完全クライアントサイド（Privacy-First）:
   - 機密データやファイルが外部サーバーに送信されないことを明記し、全処理をブラウザ上のJavaScript (FileReader API, WebCrypto等) で完結させること。
3. エクストリーム・アクセシビリティ & UI:
   - 1クリックコピー機能、入力ミスを許容するバリデーション、Tailwind CSS（CDN: https://cdn.tailwindcss.com）による洗練されたUI。
4. 単一ファイル完結:
   - 外部ライブラリのビルド不要。HTML + Tailwind CDN + Vanilla JSのみで動作させること。
"""

    prompt = f"""
{system_instruction}

以下の世界中から集められた「リアルな困りごと」リストを精読し、最も実利性の高い課題を1つ選定してアプリを構築してください。

【収集されたペインリスト】
{json.dumps(pains, ensure_ascii=False, indent=2)}
"""

    # API側推奨の最新モデル gemini-3.6-flash を使用
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
            wait_sec = (2 ** attempt) * 5
            print(f"[Error] Generation attempt {attempt+1} failed: {e}. Retrying in {wait_sec}s...")
            time.sleep(wait_sec)

    raise RuntimeError("Failed to generate solution app after retry budget.")

if __name__ == "__main__":
    generate_solution_app()
