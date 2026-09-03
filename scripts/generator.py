import os
import json
import time
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from pain_miner import get_curated_pain_points

class SolvedAppSchema(BaseModel):
    app_slug: str = Field(description="URLセーフなアプリ識別子。kebab-case (例: csv-privacy-cleaner)")
    title: str = Field(description="ユーザーが一目で課題解決を認識できる明確なツール名")
    target_pain: str = Field(description="具体的にどの層のどんな苦痛を解決したのか")
    key_features: list[str] = Field(description="困りごとを解決するための主要な3〜4機能")
    category: str = Field(description="Productivity, Finance, Developer, Writing, Accessibility など")
    html_content: str = Field(description="Tailwind CDN & インラインVanilla JSによる完全自己完結HTML")

def generate_solution_app():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    client = genai.Client(api_key=api_key)
    pains = get_curated_pain_points()

    system_instruction = """
あなたは「世界中の人々のリアルな困りごと・苦痛をWebテクノロジーで一掃する」最高峰の課題解決エンジニアです。

【絶対原則】
1. 人間のリアルなペインの根絶:
   - 「ありきたりな電卓」や「時計」のような退屈なモックは厳禁。
   - ユーザーが「手作業で数十分かかっていた面倒な作業」「既存ツールの有料化・ログイン必須・データ漏洩リスクへの不満」を、ブラウザ上で1秒・完全ローカル・無料で解決するツールに仕立ててください。
2. 完全クライアントサイド（Privacy-First）:
   - 機密データ、CSV、テキスト、ファイルが外部サーバーに一切送信されないことを明記し、全処理をブラウザ上のJavaScript (FileReader API, WebCrypto, Canvas API等) で完結させること。
3. エクストリーム・アクセシビリティ & UI:
   - 直感的なドラッグ＆ドロップ、1クリックコピー機能、入力ミスを許容するバリデーション、明快なエラーメッセージ。
   - Tailwind CSS（CDN: https://cdn.tailwindcss.com）による、清潔でプロフェッショナルなデザイン。
4. 単一ファイル完結:
   - 外部ライブラリのビルドや追加ファイルは不可。HTML + Tailwind CDN + Vanilla JSのみで動作させること。
"""

    prompt = f"""
以下の世界中から集められた「リアルな困りごと」リストを精読し、最も実利性が高く、ブラウザツールとして劇的な効率化をもたらす課題を1つ選定してアプリを構築してください。

【収集されたペインリスト】
{json.dumps(pains, ensure_ascii=False, indent=2)}
"""

    for attempt in range(3):
        try:
            res = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=SolvedAppSchema,
                    temperature=0.4,
                )
            )
            app_data = SolvedAppSchema(**json.loads(res.text))
            
            target_dir = os.path.join("apps", app_data.app_slug)
            os.makedirs(target_dir, exist_ok=True)
            
            with open(os.path.join(target_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(app_data.html_content)
                
            with open(os.path.join(target_dir, "meta.json"), "w", encoding="utf-8") as f:
                json.dump(app_data.model_dump(exclude={"html_content"}), f, ensure_ascii=False, indent=2)
                
            print(f"[Success] Built solution for: {app_data.target_pain}")
            return app_data.app_slug
        except Exception as e:
            print(f"[Error] Generation attempt {attempt+1} failed: {e}")
            time.sleep(10)
    raise RuntimeError("Failed to generate solution app.")

if __name__ == "__main__":
    generate_solution_app()
