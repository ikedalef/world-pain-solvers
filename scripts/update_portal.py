import os
import json

def build_portal():
    apps = []
    apps_dir = "apps"
    
    if os.path.exists(apps_dir):
        for slug in os.listdir(apps_dir):
            meta_path = os.path.join(apps_dir, slug, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["url"] = f"./apps/{slug}/index.html"
                    apps.append(data)

    portal_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Everyday Pain Solvers | 100% Free & In-Browser Tools</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-900 min-h-screen">
    <header class="border-b bg-white">
        <div class="max-w-6xl mx-auto px-4 py-8">
            <span class="text-xs font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">100% Free & In-Browser</span>
            <h1 class="text-3xl font-extrabold mt-3">Everyday Pain Solvers</h1>
            <p class="text-slate-600 mt-2">Autonomous, privacy-first web tools generated to solve real problems reported by real people worldwide.</p>
        </div>
    </header>
    <main class="max-w-6xl mx-auto px-4 py-10">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {''.join([f'''
            <div class="bg-white border rounded-xl p-6 flex flex-col justify-between hover:shadow-md transition">
                <div>
                    <span class="text-xs font-semibold px-2 py-1 bg-slate-100 text-slate-700 rounded">{app.get("category", "Tool")}</span>
                    <h2 class="text-xl font-bold mt-3 text-slate-800">{app.get("title")}</h2>
                    <p class="text-sm text-slate-600 mt-2 leading-relaxed">{app.get("target_pain")}</p>
                </div>
                <div class="mt-6 pt-4 border-t">
                    <a href="{app.get("url")}" class="inline-flex items-center justify-center w-full bg-slate-900 hover:bg-slate-800 text-white font-medium py-2 rounded-lg text-sm transition">
                        Open Tool &rarr;
                    </a>
                </div>
            </div>
            ''' for app in apps])}
        </div>
    </main>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(portal_html)
    print(f"[Portal] Updated index.html with {len(apps)} solved apps.")

if __name__ == "__main__":
    build_portal()
