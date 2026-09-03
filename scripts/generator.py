import os
import json
import time
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

# 過去のエラー知見に基づき、稼働実績のあるモデルを優先度順に定義
CANDIDATE_MODELS = [
    os.environ.get("GEMINI_MODEL", "gemini-3.6-flash"),
    "gemini-3.6-flash",
    "gemini-1.5-flash",
]

def generate_solution_app():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    
    genai.configure(api_key=api_key)
    pains = get_curated_pain_points()

    system_instruction = """
あなたは「世界中の人々のリアルな困りごと・苦痛をWebテクノロジーで一掃する」最高峰の課題解決エンジニアです。

【絶対原則】
1. 人間のリアルなペインの根絶:
   - 退屈なモックや既存のありきたりなツールは厳禁。
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
{system_instruction}

以下の世界中から集められた「リアルな困りごと」リストを精読し、最も実利性が高く、ブラウザツールとして劇的な効率化をもたらす課題を1つ選定してアプリを構築してください。

【収集されたペインリスト】
{json.dumps(pains, ensure_ascii=False, indent=2)}
"""

    last_error = None
    for model_name in dict.fromkeys(CANDIDATE_MODELS):  # 重複を除去して順に試行
        for attempt in range(2):
            try:
                print(f"[Info] Attempting generation with model: {model_name} (Attempt {attempt+1})")
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={
                        "response_mime_type": "application/json",
                        "response_schema": SolvedAppSchema,
                        "temperature": 0.4
                    }
                )
                res = model.generate_content(prompt)
                app_data = SolvedAppSchema(**json.loads(res.text))
                
                target_dir = os.path.join("apps", app_data.app_slug)
                os.makedirs(target_dir, exist_ok=True)
                
                with open(os.path.join(target_dir, "index.html"), "w", encoding="utf-8") as f:
                    f.write(app_data.html_content)
                    
                with open(os.path.join(target_dir, "meta.json"), "w", encoding="utf-8") as f:
                    json.dump(app_data.model_dump(exclude={"html_content"}), f, ensure_ascii=False, indent=2)
                    
                print(f"[Success] Built solution with {model_name} for: {app_data.target_pain}")
                return app_data.app_slug
            except Exception as e:
                print(f"[Warn] Model {model_name} failed: {e}")
                last_error = e
                time.sleep(5)

    raise RuntimeError(f"All model generation attempts failed. Last error: {last_error}")

if __name__ == "__main__":
    generate_solution_app()
