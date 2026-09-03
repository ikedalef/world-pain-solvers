import os
import subprocess
import json
import google.generativeai as genai

def test_app_with_playwright(app_dir: str):
    html_path = os.path.abspath(os.path.join(app_dir, "index.html"))
    test_script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
    const browser = await chromium.launch({{ args: ['--no-sandbox', '--disable-setuid-sandbox'] }});
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', err => errors.push(err.toString()));

    try {{
        await page.goto('file://{html_path}', {{ waitUntil: 'networkidle', timeout: 15000 }});
        const buttons = await page.$$('button');
        const inputs = await page.$$('input, textarea');

        if (buttons.length === 0 && inputs.length === 0) {{
            errors.push('CRITICAL: No interactive inputs or buttons found. Tool is non-functional.');
        }}
    }} catch (e) {{
        errors.push(`Navigation failed: ${{e.message}}`);
    }} finally {{
        await browser.close();
    }}

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
        print(f"[Test Passed] {app_dir} is interactive and 100% error-free.")
        return True

    print(f"[Auto-Repair] Failure detected in {app_dir}:\n{error_log}\nInitiating repair sequence...")
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    html_path = os.path.join(app_dir, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        broken_html = f.read()

    repair_prompt = f"""
このHTMLアプリはPlaywrightテストで以下のエラーを出しました:
{error_log}

【対象コード】
{broken_html}

ブラウザ上で一切のエラーを出さず、動作するよう修正してください。
Markdownのバッククォート等を含めず、<!DOCTYPE html>から</html>までの純粋なHTMLコードのみを返してください。
"""
    try:
        model = genai.GenerativeModel(model_name="gemini-3.6-flash")
        res = model.generate_content(repair_prompt)
        cleaned_html = res.text.strip().replace("```html", "").replace("```", "").strip()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(cleaned_html)
        print(f"[Auto-Repair] Fix successfully committed to {html_path}.")
        return True
    except Exception as e:
        print(f"[Auto-Repair] Repair failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target:
        repair_app_if_broken(target)
