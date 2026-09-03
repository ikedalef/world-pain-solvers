import os
import subprocess
import json
import google.generativeai as genai

CANDIDATE_MODELS = [
    os.environ.get("GEMINI_MODEL", "gemini-3.6-flash"),
    "gemini-3.6-flash",
    "gemini-1.5-flash",
]

def test_app_with_playwright(app_dir: str):
    html_path = os.path.abspath(os.path.join(app_dir, "index.html"))
    test_script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
    const browser = await chromium.launch();
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', err => errors.push(err.toString()));
    
    await page.goto('file://{html_path}', {{ waitUntil: 'networkidle' }});
    
    const buttons = await page.$$('button');
    const inputs = await page.$$('input, textarea');
    
    if (buttons.length === 0 && inputs.length === 0) {{
        errors.push('No interactive elements (button or input) found in tool.');
    }}

    await browser.close();
    if (errors.length > 0) {{
        console.error(JSON.stringify(errors));
        process.exit(1);
    }}
    process.exit(0);
}})();
"""
    result = subprocess.run(["node", "-e", test_script], capture_output=True, text=True)
    return result.returncode == 0, result.stderr

def repair_app_if_broken(app_dir: str):
    passed, error_log = test_app_with_playwright(app_dir)
    if passed:
        print(f"[Test Passed] {app_dir} is fully interactive and error-free.")
        return True

    print(f"[Auto-Repair] Issues detected in {app_dir}:\n{error_log}\nRequesting repair...")
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    html_path = os.path.join(app_dir, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        broken_html = f.read()

    repair_prompt = f"""
このHTMLアプリはヘッドレスブラウザテストで以下の実行時エラーを出しました:
{error_log}

【元のコード】
{broken_html}

エラーを完全に修正し、ブラウザで完全に動作する修正済みのHTMLコード（<!DOCTYPE html>から</html>まで）のみを出力してください。Markdownバッククォートなどの余計なテキストは含めないでください。
"""
    for model_name in dict.fromkeys(CANDIDATE_MODELS):
        try:
            print(f"[Auto-Repair] Trying repair with {model_name}...")
            model = genai.GenerativeModel(model_name=model_name)
            res = model.generate_content(repair_prompt)
            cleaned_html = res.text.strip().replace("```html", "").replace("```", "").strip()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(cleaned_html)
            print(f"[Auto-Repair] Repair applied using {model_name}.")
            return True
        except Exception as e:
            print(f"[Auto-Repair] Model {model_name} repair failed: {e}")

    return False

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target:
        repair_app_if_broken(target)
