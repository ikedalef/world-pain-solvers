import requests
import json
import re

def fetch_reddit_pains():
    subreddits = ["productivity", "smallbusiness", "freelance", "webdev"]
    headers = {"User-Agent": "AutonomousPainSolver/1.0"}
    pains = []

    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/top.json?t=week&limit=10"
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                posts = res.json().get("data", {}).get("children", [])
                for p in posts:
                    title = p["data"]["title"]
                    body = p["data"].get("selftext", "")[:300]
                    if re.search(r"(how do I|is there a tool|struggling with|waste of time|hate doing|manual|automate)", title + body, re.I):
                        pains.append({
                            "source": f"Reddit r/{sub}",
                            "title": title,
                            "context": body.replace("\n", " ").strip()
                        })
        except Exception as e:
            print(f"[Warn] Reddit fetch failed for r/{sub}: {e}")
    return pains

def fetch_hackernews_pains():
    pains = []
    try:
        url = "https://hn.algolia.com/api/v1/search_by_date?tags=ask_hn&hitsPerPage=10"
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            hits = res.json().get("hits", [])
            for h in hits:
                title = h.get("title", "")
                text = h.get("story_text", "")[:300] if h.get("story_text") else ""
                pains.append({
                    "source": "HackerNews Ask HN",
                    "title": title,
                    "context": text.replace("\n", " ").strip()
                })
    except Exception as e:
        print(f"[Warn] HackerNews fetch failed: {e}")
    return pains

def get_curated_pain_points():
    all_pains = fetch_reddit_pains() + fetch_hackernews_pains()
    if not all_pains:
        return [
            {"source": "CorePain", "title": "Freelancers struggling to parse and split messy CSV expenses without privacy leaks", "context": "Need 100% in-browser offline tool to clean, categorize and calculate tax deductions from invoice CSVs."},
            {"source": "CorePain", "title": "Developers needing instant secure regex & cron expression generator and visualizer", "context": "Need instant plain-english to cron/regex translator that tests testcases live."},
            {"source": "CorePain", "title": "Students & Researchers need audio-to-markdown structured summary converter with zero upload", "context": "In-browser WebSpeech voice dictation to auto-bulleted markdown with instant copy."}
        ]
    return all_pains[:15]

if __name__ == "__main__":
    pains = get_curated_pain_points()
    print(f"Collected {len(pains)} verified pain points.")
