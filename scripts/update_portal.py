import os
import json

def rebuild_portal():
    apps_dir = "apps"
    if not os.path.exists(apps_dir):
        os.makedirs(apps_dir, exist_ok=True)

    stripe_link = os.environ.get("STRIPE_PAYMENT_LINK", "https://buy.stripe.com/evqaEXafF6jw6kV0jg5J60j")

    apps = []
    for item in os.listdir(apps_dir):
        meta_path = os.path.join(apps_dir, item, "meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["slug"] = item
                    apps.append(data)
            except Exception as e:
                print(f"[Warn] Could not parse {meta_path}: {e}")

    apps_cards_html = ""
    for app in apps:
        title = app.get("title", "Productivity Tool")
        category = app.get("category", "Data Utility")
        pain = app.get("target_pain", "Automate manual friction in workflow.")
        slug = app.get("slug", "")
        features = app.get("key_features", [])

        feature_items = "".join([f"<li class='flex items-center text-xs text-slate-300'><span class='text-indigo-400 mr-2'>✓</span>{f}</li>" for f in features])

        card = f"""
        <div class="bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-6 transition-all duration-300 flex flex-col justify-between group shadow-lg">
            <div>
                <div class="flex items-center justify-between mb-4">
                    <span class="text-xs font-semibold px-2.5 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full">{category}</span>
                    <a href="{stripe_link}" target="_blank" class="text-[11px] font-semibold px-2.5 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full transition-colors flex items-center gap-1 cursor-pointer">
                        <span>⚡ $5 Lifetime</span>
                    </a>
                </div>
                <h3 class="text-xl font-bold text-white mb-2 group-hover:text-indigo-300 transition-colors">{title}</h3>
                <p class="text-sm text-slate-400 mb-4 line-clamp-3 leading-relaxed">{pain}</p>
                <ul class="space-y-1.5 mb-6">
                    {feature_items}
                </ul>
            </div>
            <div class="flex items-center gap-3">
                <a href="apps/{slug}/index.html" class="flex-1 inline-flex items-center justify-center px-4 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition-colors shadow-md shadow-indigo-600/20">
                    Launch Tool →
                </a>
                <a href="{stripe_link}" target="_blank" class="inline-flex items-center justify-center px-3 py-2.5 text-xs font-bold text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded-xl transition-colors whitespace-nowrap">
                    Get Pro ($5)
                </a>
            </div>
        </div>
        """
        apps_cards_html += card

    portal_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PainKillers Pro | High-Utility Privacy-First Web Tools</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen antialiased selection:bg-indigo-500 selection:text-white flex flex-col justify-between">
    <!-- Header -->
    <header class="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <a href="index.html" class="flex items-center space-x-3">
                <div class="h-4 w-4 rounded-full bg-emerald-500 animate-pulse"></div>
                <span class="text-lg font-bold text-white tracking-tight">PainKillers<span class="text-indigo-400">.pro</span></span>
            </a>
            <div class="flex items-center space-x-3">
                <a href="{stripe_link}" target="_blank" class="text-xs font-bold px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-full transition-all shadow-md shadow-emerald-500/20">
                    Get Lifetime Pass ($5)
                </a>
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 flex-1">
        <div class="text-center max-w-3xl mx-auto mb-16">
            <h1 class="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight mb-6">
                Stop wasting hours on <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">repetitive manual workflows</span>.
            </h1>
            <p class="text-lg sm:text-xl text-slate-400 leading-relaxed">
                Autonomous, privacy-first web tools designed to solve real operational bottlenecks. 100% in-browser. No servers. No data leaks. Instant execution.
            </p>
        </div>

        <!-- Catalog Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {apps_cards_html}
        </div>
    </main>

    <footer class="border-t border-slate-800/80 py-8 text-center text-xs text-slate-500">
        <p>© PainKillers.pro — Autonomous High-Utility Tools. 100% Client-Side Privacy Guaranteed.</p>
    </footer>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(portal_html)
    print("[Success] Rebuilt portal index.html with fully clickable Stripe payment CTAs.")

if __name__ == "__main__":
    rebuild_portal()
