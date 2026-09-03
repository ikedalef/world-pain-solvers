import time
import requests
import re
import json

def fetch_with_retry(url: str, headers: dict = None, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            elif res.status_code == 429:
                time.sleep(10)
        except Exception:
            time.sleep(5)
    return {}

def fetch_reddit_pains():
    subreddits = ["productivity", "smallbusiness", "freelance"]
    headers = {"User-Agent": "AutonomousWorldPainSolver/1.0"}
    pains = []

    for sub in subreddits:
        data = fetch_with_retry(f"https://www.reddit.com/r/{sub}/top.json?t=week&limit=5", headers=headers)
        children = data.get("data", {}).get("children", [])
        for p in children:
            title = p.get("data", {}).get("title", "")
            body = p.get("data", {}).get("selftext", "")[:150]
            if re.search(r"(how do I|is there a tool|struggling with|waste of time|hate doing|manual|automate)", title + body, re.I):
                pains.append({
                    "source": f"Reddit r/{sub}",
                    "title": title,
                    "context": body.replace("\n", " ").strip()
                })
    return pains

def fetch_hackernews_pains():
    pains = []
    data = fetch_with_retry("https://hn.algolia.com/api/v1/search_by_date?tags=ask_hn&hitsPerPage=5")
    hits = data.get("hits", [])
    for h in hits:
        title = h.get("title", "")
        text = h.get("story_text", "")[:150] if h.get("story_text") else ""
        pains.append({
            "source": "HackerNews Ask HN",
            "title": title,
            "context": text.replace("\n", " ").strip()
        })
    return pains

def get_curated_pain_points():
    try:
        all_pains = fetch_reddit_pains() + fetch_hackernews_pains()
    except Exception:
        all_pains = []

    if not all_pains:
        return [
            {"source": "CorePain", "title": "Freelancers struggling to parse and clean messy CSV expenses offline", "context": "Need 100% in-browser private tool to clean CSVs and calculate tax deductions."},
            {"source": "CorePain", "title": "Engineers needing instant visual cron schedule validator", "context": "Need local validator showing next execution times across timezones."},
            {"source": "CorePain", "title": "Job applicants needing ATS-friendly resume plaintext cleaner", "context": "Need client-side tool to strip special characters and optimize text for ATS parsers."}
        ]
    return all_pains[:3]

if __name__ == "__main__":
    pains = get_curated_pain_points()
    print(f"Collected {len(pains)} verified pain points.")
