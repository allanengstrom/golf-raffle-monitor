import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone

BRANDS = [
    "Titleist", "TaylorMade", "Callaway", "PING",
    "Cobra", "Cleveland", "Srixon", "Mizuno", "Bridgestone"
]
KEYWORDS = ["raffle", "giveaway", "sweepstakes", "enter to win", "win a"]
SUBREDDITS = ["golf", "golfequipment", "golf_r"]

SMS_TO = "5713732274@vtext.com"
GMAIL_FROM = os.environ["GMAIL_ADDRESS"]
GMAIL_PASS = os.environ["GMAIL_APP_PASSWORD"]
SEEN_FILE = "seen_raffles.json"
HEADERS = {"User-Agent": "GolfRaffleMonitor/1.0 (personal use)"}


def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f)


def send_sms(brand, title, url):
    body = f"RAFFLE: {brand}\n{title}\n{url}"
    msg = MIMEText(body)
    msg["From"] = GMAIL_FROM
    msg["To"] = SMS_TO
    msg["Subject"] = ""
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_FROM, GMAIL_PASS)
        server.send_message(msg)
    print(f"[SMS] {brand}: {title}")


def is_relevant(text):
    text = text.lower()
    has_keyword = any(kw in text for kw in KEYWORDS)
    has_brand = any(b.lower() in text for b in BRANDS)
    return has_keyword and has_brand


def search_reddit(subreddit, brand):
    results = []
    url = (
        f"https://www.reddit.com/r/{subreddit}/search.json"
        f"?q={brand}+raffle+OR+giveaway+OR+sweepstakes"
        f"&sort=new&restrict_sr=1&limit=10&t=week"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        for post in r.json()["data"]["children"]:
            p = post["data"]
            if is_relevant(p["title"]):
                results.append({
                    "id": f"reddit_{p['id']}",
                    "brand": brand,
                    "title": p["title"],
                    "url": f"https://reddit.com{p['permalink']}",
                })
    except Exception as e:
        print(f"[WARN] Reddit {subreddit}/{brand}: {e}")
    return results


def scrape_brand_pages():
    pages = {
        "Titleist": "https://www.titleist.com/promotions",
        "TaylorMade": "https://www.taylormadegolf.com/promotions",
        "Callaway": "https://www.callawaygolf.com/promotions",
        "Cobra": "https://www.cobragolf.com/blogs/news",
        "Mizuno": "https://www.mizunousa.com/pages/promotions",
    }
    results = []
    for brand, url in pages.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if any(kw in r.text.lower() for kw in KEYWORDS):
                results.append({
                    "id": f"brand_{brand}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
                    "brand": brand,
                    "title": f"Possible raffle/giveaway on {brand} promotions page",
                    "url": url,
                })
        except Exception as e:
            print(f"[WARN] Brand page {brand}: {e}")
    return results


def main():
    seen = load_seen()
    new_count = 0

    findings = []
    for brand in BRANDS:
        for sub in SUBREDDITS:
            findings.extend(search_reddit(sub, brand))
    findings.extend(scrape_brand_pages())

    # Deduplicate by id within this run
    seen_this_run = set()
    for item in findings:
        key = item["id"]
        if key in seen or key in seen_this_run:
            continue
        seen_this_run.add(key)
        seen.add(key)
        new_count += 1
        try:
            send_sms(item["brand"], item["title"], item["url"])
        except Exception as e:
            print(f"[ERROR] SMS failed: {e}")

    save_seen(seen)
    print(f"Done. {new_count} new raffle(s) found at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
