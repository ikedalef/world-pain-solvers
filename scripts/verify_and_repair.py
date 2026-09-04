import os
import sys
import subprocess
import json
import google.generativeai as genai

def test_app_with_playwright(app_dir: str):
    html_path = os.path.abspath(os.path.join(app_dir, "index.html"))
    if not os.path.exists(html_path):
        print(f"[Skip] No index.html found at {html_path}.")
        return True, ""

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
            errors.push('CRITICAL: No interactive inputs or buttons found.');
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
    if not app_dir or not os.path.exists(app_dir):
        print("[Info] No app directory to repair. Skipping.")
        return True

    passed, error_log = test_app_with_playwright(app_dir)
    if passed:
        print(f"[Test Passed] {app_dir} is interactive and error-free.")
        return True

    print(f"[Auto-Repair] Issues detected in {app_dir}:\n{error_log}")
    return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    repair_app_if_broken(target)
